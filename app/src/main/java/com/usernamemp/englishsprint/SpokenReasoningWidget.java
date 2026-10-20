package com.usernamemp.englishsprint;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.graphics.Typeface;
import android.text.InputType;
import android.view.Gravity;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Same question, same training session. This is a response primitive,
 * not an Activity, course or extra catalogue.
 */
public final class SpokenReasoningWidget {
    public interface Completion { void onAnswer(boolean correct); }
    private static final int REQUEST_MIC = 917;
    private final Activity activity;
    private final Question question;
    private final String packId;
    private final Completion finish;
    private final SpokenReasoningCapture mic;
    private final SpokenReasoningTraceStore store;
    private final List<Attempt> attempts = new ArrayList<>();
    private LinearLayout attemptList;
    private TextView status;
    private Button start, stop, submit;
    private EditText finalAnswer;
    private boolean loading = true, processing = false, recording = false, completed = false, disposed = false;
    private int sequence = 0;
    private String asrError = "";
    private boolean ru() { return "ru".equals(Locale.getDefault().getLanguage()); }
    private String t(String a, String b) { return ru() ? a : b; }
    private String speechLocale() { return "ru"; }

    private static final class Attempt {
        int number;
        long startedAtMs;
        String captureMode, original, modelVersion, modelSha;
        EditText edited;
    }

    public SpokenReasoningWidget(Activity activity, Question question, String packId,
                                 Completion finish) {
        this.activity = activity; this.question = question; this.packId = packId;
        this.finish = finish;
        this.mic = new SpokenReasoningCapture(activity);
        this.store = new SpokenReasoningTraceStore(activity);
    }

    private TextView text(String label,int sp) {
        TextView v = new TextView(activity);
        v.setText(label); v.setTextSize(sp);
        v.setPadding(0,10,0,10);
        return v;
    }
    private Button button(String title, Runnable action) {
        Button b = new Button(activity);
        b.setText(title); b.setAllCaps(false);
        b.setOnClickListener(v -> action.run());
        return b;
    }
    public void attach(LinearLayout root) {
        root.addView(text(t("Запишите ход решения. Можно сделать несколько попыток.",
                            "Record your reasoning; you may make multiple attempts."),15));
        status = text(t("Подготовка встроенной офлайн-модели…",
                        "Preparing bundled offline model…"),14);
        root.addView(status);
        start = button(t("Записать решение","Record reasoning"),this::startRecording);
        root.addView(start);
        stop = button(t("Остановить и распознать","Stop and transcribe"),this::stopRecording);
        stop.setEnabled(false); root.addView(stop);
        Button typed = button(t("Ввести объяснение текстом", "Type explanation instead"),
                              this::addTypedAttempt);
        root.addView(typed);
        attemptList = new LinearLayout(activity);
        attemptList.setOrientation(LinearLayout.VERTICAL);
        root.addView(attemptList);
        if (!"none".equals(question.spokenAnswerKind)) {
            root.addView(text(t("Итоговый ответ", "Final answer"),15));
            finalAnswer = new EditText(activity);
            finalAnswer.setSingleLine(true);
            finalAnswer.setInputType("numeric".equals(question.spokenAnswerKind)
                    ? InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL
                      | InputType.TYPE_NUMBER_FLAG_SIGNED
                    : InputType.TYPE_CLASS_TEXT);
            finalAnswer.setHint("numeric".equals(question.spokenAnswerKind)
                    ? t("Например: 42","Example: 42")
                    : t("Например: Петя","Example: Peter"));
            root.addView(finalAnswer);
        }
        submit = button(t("Завершить задачу", "Submit answer"), this::submit);
        root.addView(submit);
        setActions();
        new Thread(() -> {
            String error = null;
            try { OfflineTOneEngine.ensureBundled(activity.getApplicationContext(),speechLocale()); }
            catch (Exception e) { error = e.getMessage(); }
            final String result = error;
            activity.runOnUiThread(() -> {
                if (disposed) return;
                loading = false;
                if (result != null) {
                    asrError = result;
                    status.setText(t("Офлайн-модель недоступна: ", "Offline model unavailable: ") + result
                            + t(". Ввод текстом доступен.", ". Typed explanation is available."));
                } else {
                    status.setText(t("Офлайн-распознавание готово. Запись только по нажатию.",
                                     "Offline recognizer ready. Recording starts on tap."));
                }
                setActions();
            });
        }, "rift-bundled-model-setup").start();
    }

    private void setActions() {
        if (disposed || start == null) return;
        start.setEnabled(!loading && asrError.isEmpty() && !processing && !recording && !completed);
        stop.setEnabled(recording && !processing);
        submit.setEnabled(!loading && !processing && !recording && !completed);
    }

    public void onPermissionResult(int request, int[] grants) {
        if(request != REQUEST_MIC || disposed) return;
        if(grants.length>0 && grants[0]==PackageManager.PERMISSION_GRANTED) startRecording();
        else status.setText(t("Микрофон не разрешён. Доступен ввод текстом.",
                              "Microphone denied; typed reasoning is available."));
    }
    public static int micPermissionRequest() { return REQUEST_MIC; }
    private void startRecording() {
        if (disposed || processing || recording || loading || completed || !asrError.isEmpty()) return;
        if (activity.checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            activity.requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},REQUEST_MIC);
            return;
        }
        try {
            mic.start();
            recording = true;
            sequence++;
            status.setText(t("Попытка ", "Attempt ") + sequence + t(": запись идёт", ": recording"));
        } catch (Exception e) {
            status.setText(t("Не удалось начать запись: ", "Cannot record: ") + e.getMessage());
        }
        setActions();
    }
    private void stopRecording() {
        if (!recording || processing || disposed) return;
        processing = true; recording = false; setActions();
        File captured;
        try { captured = mic.stop(); }
        catch (Exception e) {
            status.setText(t("Ошибка записи: ", "Recording error: ") + e.getMessage());
            processing = false; setActions(); return;
        }
        final int number = sequence;
        final long startedAt = System.currentTimeMillis();
        status.setText(t("Попытка ", "Attempt ") + number
                       + t(": локальное распознавание…", ": offline transcription…"));
        new Thread(() -> {
            OfflineTOneEngine.Transcription decoded = null;
            String fail = null;
            try { decoded = OfflineTOneEngine.recognize(
                    activity.getApplicationContext(),speechLocale(),captured); }
            catch (Exception e) { fail = e.getMessage(); }
            finally { captured.delete(); }
            final OfflineTOneEngine.Transcription success = decoded;
            final String error = fail;
            activity.runOnUiThread(() -> {
                if (disposed) return;
                processing = false;
                if (success == null) {
                    status.setText(t("Попытка ", "Attempt ") + number +
                            t(": распознавание не удалось: ", ": transcription failed: ") + error);
                } else {
                    Attempt attempt = new Attempt();
                    attempt.number = number; attempt.startedAtMs = startedAt;
                    attempt.captureMode = "solve_aloud";
                    attempt.original = success.text;
                    attempt.modelVersion = success.modelVersion;
                    attempt.modelSha = success.modelSha256;
                    addAttempt(attempt, success.text);
                    status.setText(t("Попытка ", "Attempt ") + number +
                            t(": текст можно проверить и исправить.", ": review or correct transcript."));
                }
                setActions();
            });
        }, "rift-voice-attempt-"+number).start();
    }
    private void addTypedAttempt() {
        if (completed || disposed || recording || processing || loading) return;
        Attempt attempt = new Attempt();
        attempt.number = ++sequence; attempt.startedAtMs = System.currentTimeMillis();
        attempt.captureMode = "typed_reasoning"; attempt.original = "";
        attempt.modelSha = ""; attempt.modelVersion = "";
        addAttempt(attempt,"");
        setActions();
    }
    private void addAttempt(Attempt attempt, String initial) {
        attempts.add(attempt);
        TextView label = text(t("Попытка №", "Attempt #") + attempt.number,18);
        label.setTypeface(null,Typeface.BOLD);
        attemptList.addView(label);
        attemptList.addView(text(t("Исходная ASR: ","Original ASR: ") +
                (attempt.original.isEmpty() ? t("отсутствует", "none") : attempt.original),13));
        EditText edit = new EditText(activity);
        edit.setMinLines(3);
        edit.setGravity(Gravity.TOP);
        edit.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        edit.setHint(t("Моё решение было таким…","My reasoning was…"));
        edit.setText(initial);
        attempt.edited = edit;
        attemptList.addView(edit);
    }

    private void submit() {
        if (loading || processing || recording || completed || disposed) return;
        if (attempts.isEmpty()) {
            status.setText(t("Нужна хотя бы одна попытка решения.",
                             "At least one reasoning attempt is required.")); return;
        }
        String submitted = finalAnswer==null ? "" : finalAnswer.getText().toString().trim();
        if (finalAnswer!=null && submitted.isEmpty()) {
            status.setText(t("Введите итоговый ответ.","Enter the final answer.")); return;
        }
        boolean correct = finalAnswer != null && question.acceptsText(submitted);
        try {
            for (Attempt attempt: attempts) {
                String edit = attempt.edited.getText().toString().trim();
                SpokenReasoningRubric.Result checked = question.reasoningRubric.equals(
                    SpokenReasoningRubric.VERSION)
                    ? SpokenReasoningRubric.assess(question.id,correct,edit)
                    : new SpokenReasoningRubric.Result("not_evaluated",
                                                       new ArrayList<>(),new ArrayList<>());
                JSONObject entry = new JSONObject();
                entry.put("question_id",question.id);
                entry.put("pack_id",packId);
                entry.put("attempt_number",attempt.number);
                entry.put("attempt_started_at_ms",attempt.startedAtMs);
                entry.put("capture_mode",attempt.captureMode);
                entry.put("locale",speechLocale());
                entry.put("raw_asr_transcript",attempt.original);
                entry.put("edited_transcript",edit);
                entry.put("student_edited",!attempt.original.equals(edit));
                entry.put("asr_provider",attempt.modelVersion.isEmpty()?"none":"t-one-71m");
                entry.put("asr_model_version",attempt.modelVersion);
                entry.put("asr_model_sha256",attempt.modelSha);
                entry.put("answer",submitted);
                entry.put("answer_correct",finalAnswer==null?JSONObject.NULL:correct);
                entry.put("rubric_version",question.reasoningRubric);
                entry.put("reasoning_state",checked.status);
                entry.put("step_evidence",new JSONArray(checked.evidence));
                entry.put("contradictions",new JSONArray(checked.contradictions));
                entry.put("audio_retained",false);
                entry.put("sync_consent",false);
                entry.put("source_type","observed_learner_input_not_reference");
                store.save(entry);
            }
            completed = true;
            setActions();
            finish.onAnswer(correct);
        } catch (Exception e) {
            status.setText(t("Ошибка сохранения; ответ не отправлен: ",
                             "Trace save failed, answer not submitted: ") + e.getMessage());
        }
    }
    public void onPause() {
        if (!recording) return;
        mic.cancel();
        recording = false;
        if(status!=null) status.setText(t("Запись прервана; начните новую попытку.",
                                          "Recording interrupted; start a new attempt."));
        setActions();
    }
    public void onResume() { setActions(); }
    public void dispose() {
        disposed = true;
        if(recording) mic.cancel();
        recording = false;
    }
}
