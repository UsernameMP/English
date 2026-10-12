package com.usernamemp.englishsprint;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.File;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

/** Separate pre-answer voice/typed reasoning flow; no answer key is shown before save. */
public final class SpokenReasoningActivity extends Activity {
    private static final int MICROPHONE_REQUEST = 71;
    private static final int MODEL_ZIP_REQUEST = 72;
    private LinearLayout content;
    private Question question;
    private SpokenReasoningCapture microphone;
    private SpokenReasoningTraceStore traces;
    private EditText edited, answer;
    private TextView original, status;
    private Button record, stop, submit;
    private String rawTranscript="", modelVersion="", modelSha="", captureMode="typed_reasoning";
    private boolean processing=false, saved=false;
    private final Map<String,String> selection = new HashMap<>();
    private boolean ru() { return "ru".equals(Locale.getDefault().getLanguage()); }
    private String spokenLocale() {
        return question != null && "math_ratio_001".equals(question.id) && !ru() ? "en" : "ru";
    }
    private String t(String russian,String english) { return ru() ? russian : english; }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        QuestionBank.init(this);
        microphone = new SpokenReasoningCapture(this);
        traces = new SpokenReasoningTraceStore(this);
        try {
            JSONArray list = new JSONObject(readAsset("content/spoken_reasoning_candidates.json"))
                    .getJSONArray("candidates");
            for (int i=0;i<list.length();i++) {
                JSONObject item=list.getJSONObject(i);
                selection.put(item.getString("question_id"), item.getString("selection"));
            }
        } catch(Exception e) { fail("Invalid task selection: "+e.getMessage()); return; }
        String target = getIntent().getStringExtra("question_id");
        if (target != null) {
            for (Question q : QuestionBank.all()) if (target.equals(q.id) && selection.containsKey(q.id)) {
                showTask(q);
                return;
            }
        }
        showPicker();
    }

    private String readAsset(String path) throws Exception {
        try (java.io.InputStream in=getAssets().open(path);
             java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream()) {
            byte[] bytes=new byte[4096]; int n;
            while ((n=in.read(bytes)) != -1) out.write(bytes,0,n);
            return out.toString("UTF-8");
        }
    }
    private void screen(String title) {
        ScrollView scroll = new ScrollView(this);
        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        int pad=(int)(18*getResources().getDisplayMetrics().density);
        content.setPadding(pad,pad,pad,pad);
        scroll.addView(content);
        setContentView(scroll);
        Button back = button("←", () -> finish());
        content.addView(back);
        add(title,24);
    }
    private void add(String value,int size) {
        TextView tv=new TextView(this);
        tv.setText(value); tv.setTextSize(size); tv.setTextColor(Color.rgb(33,40,52));
        tv.setPadding(0,14,0,14);
        content.addView(tv);
    }
    private Button button(String label,Runnable click) {
        Button b=new Button(this); b.setText(label); b.setAllCaps(false);
        b.setOnClickListener(v -> click.run()); return b;
    }
    private void fail(String message) {
        screen(t("Голосовое решение","Reason aloud"));
        add(message,16);
    }
    private void showPicker() {
        screen(t("Рассказать решение","Explain aloud"));
        add(t("Отобраны задания, которые можно объяснить словами без рисунка или сложного ввода.",
              "Curated questions that can be explained without diagrams or complex input."),16);
        int count=0;
        for (Question q: QuestionBank.all()) {
            if (!selection.containsKey(q.id) || !"numeric".equals(q.interaction)) continue;
            String label=q.prompt+"\n"+("verified_arithmetic_pilot".equals(selection.get(q.id))
                ? t("Пилот: проверка арифметики","Arithmetic verification pilot")
                : t("Сбор объяснений; автоматическая проверка ограничена","Transcript collection, manual review"));
            content.addView(button(label,()->showTask(q))); count++;
        }
        if(count==0) add(t("В текущем наборе нет отобранных задач. Откройте пилот математики 5–7.",
                              "No eligible tasks in this pack. Select the grade 5–7 mathematics pilot."),16);
        content.addView(button(t("Экспортировать мои записи","Export my transcripts"),this::exportTraces));
        content.addView(button(t("Удалить локальные записи","Delete local transcripts"),this::confirmDelete));
    }
    private void showTask(Question q) {
        microphone.cancel();
        question=q; rawTranscript=""; modelVersion=""; modelSha="";
        captureMode="typed_reasoning"; processing=false; saved=false;
        screen(t("Рассказать решение","Explain aloud"));
        add(q.context,18);
        add(q.prompt,22);
        add(t("Сначала объясните ход решения. Правильный ответ отдельно. Эталон не показывается.",
              "Explain your reasoning first, enter your final answer separately. The key stays hidden."),14);
        final String locale = spokenLocale();
        boolean model = OfflineVoskEngine.hasModel(this,locale);
        if (!model) add(t("Офлайн-модель "+locale+" не установлена. Введите объяснение текстом. Микрофон без модели не активируется.",
                 "Offline "+locale+" ASR model missing. Type your explanation; microphone is disabled."),14);
        record=button(t("● Записать объяснение","● Record explanation"),this::beginRecording);
        record.setEnabled(model); content.addView(record);
        stop=button(t("■ Остановить и распознать","■ Stop and transcribe"),this::endRecording);
        stop.setEnabled(false); content.addView(stop);
        content.addView(button(t("Импортировать офлайн-модель ZIP","Import offline ASR model ZIP"),()->{
            Intent pick=new Intent(Intent.ACTION_OPEN_DOCUMENT);
            pick.setType("application/zip"); pick.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(pick,MODEL_ZIP_REQUEST);
        }));
        original=new TextView(this); original.setTextSize(14);
        original.setText(t("Исходная расшифровка: отсутствует","Original ASR transcript: none"));
        content.addView(original);
        add(t("Расшифровка (можно исправить) / текстовое объяснение:",
              "Editable transcript / typed explanation:"),15);
        edited=new EditText(this); edited.setGravity(android.view.Gravity.TOP);
        edited.setMinLines(4); edited.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        edited.setHint(t("Я рассуждал так…","I reasoned as follows…")); content.addView(edited);
        add(t("Итоговый ответ:","Final answer:"),15);
        answer=new EditText(this); answer.setSingleLine(true);
        answer.setInputType(InputType.TYPE_CLASS_TEXT); content.addView(answer);
        status=new TextView(this); status.setTextSize(15); content.addView(status);
        submit=button(t("Сохранить и проверить","Save and assess"),this::save);
        content.addView(submit);
    }

    private void beginRecording() {
        if (processing || saved) return;
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},MICROPHONE_REQUEST);
            return;
        }
        try {
            microphone.start(); rawTranscript=""; captureMode="recording_in_progress";
            edited.setText(""); original.setText(t("Идёт запись…","Recording…"));
            record.setEnabled(false); stop.setEnabled(true); submit.setEnabled(false);
            status.setText(t("Запись только после нажатия; максимум 90 секунд.",
                             "Recording started by your tap; maximum 90 seconds."));
        } catch (Exception e) { status.setText(e.getMessage()); }
    }
    @Override public void onRequestPermissionsResult(int requestCode,String[] p,int[] grants) {
        super.onRequestPermissionsResult(requestCode,p,grants);
        if(requestCode==MICROPHONE_REQUEST) {
            if(grants.length>0 && grants[0]==PackageManager.PERMISSION_GRANTED) beginRecording();
            else if(status!=null) status.setText(t("Доступ к микрофону запрещён: доступен ввод текстом.",
                          "Microphone denied: typed reasoning is available."));
        }
    }

    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data) {
        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode!=MODEL_ZIP_REQUEST || resultCode!=RESULT_OK || data==null || data.getData()==null)
            return;
        if(status==null) return;
        status.setText(t("Импорт модели в локальное хранилище…","Importing offline ASR model…"));
        final String locale=spokenLocale();
        final android.net.Uri uri=data.getData();
        record.setEnabled(false); submit.setEnabled(false);
        new Thread(()->{
            String msg;
            boolean okay;
            try {
                java.io.InputStream stream=getContentResolver().openInputStream(uri);
                if(stream==null) throw new java.io.IOException("Cannot open model file");
                OfflineVoskEngine.importZip(getApplicationContext(),locale,stream);
                msg=t("Модель импортирована. Речь не отправляется в интернет.",
                      "Model installed. Speech stays offline.");
                okay=true;
            } catch (Exception e) {msg=t("Ошибка импорта: ","Import failed: ")+e.getMessage();okay=false;}
            final String output=msg; final boolean enabled=okay;
            runOnUiThread(()->{
                if(isFinishing()||isDestroyed())return;
                status.setText(output);
                record.setEnabled(enabled || OfflineVoskEngine.hasModel(this,locale));
                submit.setEnabled(true);
            });
        },"rift-model-import").start();
    }
    private void endRecording() {
        if (processing) return;
        stop.setEnabled(false);
        File wav;
        try { wav=microphone.stop(); }
        catch (Exception e) {
            captureMode="typed_reasoning"; record.setEnabled(true); submit.setEnabled(true);
            status.setText(t("Запись не получена: ","Recording error: ")+e.getMessage()); return;
        }
        processing=true;
        status.setText(t("Офлайн-распознавание…","Offline transcription…"));
        final String locale=spokenLocale();
        new Thread(()->{
            OfflineVoskEngine.Transcription result=null; String failure=null;
            try { result=OfflineVoskEngine.recognize(getApplicationContext(),locale,wav); }
            catch (Exception e) { failure=e.getClass().getSimpleName()+": "+e.getMessage(); }
            finally { wav.delete(); }
            final OfflineVoskEngine.Transcription asr=result;
            final String error=failure;
            runOnUiThread(()->{
                if (isFinishing() || isDestroyed()) return;
                processing=false; submit.setEnabled(true); record.setEnabled(true);
                if(asr!=null) {
                    rawTranscript=asr.text; modelVersion=asr.modelVersion; modelSha=asr.modelSha256;
                    captureMode="solve_aloud";
                    original.setText(t("Исходная ASR (неизменяемая): ","Immutable ASR: ")+rawTranscript);
                    edited.setText(rawTranscript);
                    status.setText(t("Исходная расшифровка сохранится отдельно от правок.",
                                     "Original ASR remains separate from user edits."));
                } else {
                    rawTranscript=""; captureMode="typed_reasoning";
                    original.setText(t("Исходной ASR нет","No ASR transcript"));
                    status.setText(t("Не удалось распознать: ","Transcription failed: ")+error);
                }
            });
        },"rift-offline-asr").start();
    }
    private void save() {
        if (processing || saved || microphone.isRecording()) return;
        String studentText=edited.getText().toString().trim();
        String response=answer.getText().toString().trim();
        if (response.isEmpty()) {status.setText(t("Введите итоговый ответ.","Enter your final answer."));return;}
        boolean correct=question.acceptsText(response);
        SpokenReasoningRubric.Result report=SpokenReasoningRubric.assess(question.id,correct,studentText);
        try {
            JSONObject data=new JSONObject();
            data.put("question_id",question.id);
            data.put("pack_id",QuestionBank.currentPack().id);
            data.put("locale",spokenLocale());
            data.put("capture_mode",captureMode);
            data.put("raw_asr_transcript",rawTranscript);
            data.put("edited_transcript",studentText);
            data.put("student_edited",!rawTranscript.isEmpty()&&!rawTranscript.equals(studentText));
            data.put("original_asr_present",!rawTranscript.isEmpty());
            data.put("asr_provider",modelVersion.isEmpty()?"none":"vosk");
            data.put("asr_model_version",modelVersion);
            data.put("asr_model_sha256",modelSha);
            data.put("answer",response); data.put("answer_correct",correct);
            data.put("reasoning_state",report.status);
            data.put("rubric_version","math_ratio_001".equals(question.id)
                    ? SpokenReasoningRubric.VERSION : "not_calibrated");
            data.put("step_evidence",new JSONArray(report.evidence));
            data.put("contradictions",new JSONArray(report.contradictions));
            data.put("audio_retained",false); data.put("sync_consent",false);
            data.put("source_type","observed_learner_input_not_reference");
            String id=traces.save(data);
            status.setText((correct ? t("Ответ верен","Answer correct") : t("Ответ неверен","Answer incorrect"))
                    +"\n"+t("Оценка объяснения: ","Reasoning assessment: ")+report.status
                    +"\n"+t("Сохранено локально, ID: ","Saved locally, ID: ")+id);
            saved=true; record.setEnabled(false); stop.setEnabled(false); submit.setEnabled(false);
        } catch (Exception e) { status.setText(t("Ошибка сохранения: ","Save error: ")+e.getMessage()); }
    }
    private void exportTraces() {
        try {
            Intent send=new Intent(Intent.ACTION_SEND);send.setType("application/json");
            send.putExtra(Intent.EXTRA_TEXT,traces.exportAll().toString());
            startActivity(Intent.createChooser(send,t("Экспорт по вашему выбору","Export with your consent")));
        } catch(Exception e) { new AlertDialog.Builder(this).setMessage(e.getMessage()).show(); }
    }
    private void confirmDelete() {
        new AlertDialog.Builder(this).setMessage(t("Удалить все локальные reasoning-записи?",
              "Delete all locally stored reasoning transcripts?"))
          .setNegativeButton(t("Отмена","Cancel"),null)
          .setPositiveButton(t("Удалить","Delete"),(d,w)->{
              int n=traces.deleteAll();
              new AlertDialog.Builder(this).setMessage(t("Удалено: ","Deleted: ")+n)
                      .setPositiveButton("OK",null).show();
          }).show();
    }
    @Override public void onBackPressed() {
        microphone.cancel(); super.onBackPressed();
    }
    @Override protected void onPause() {
        microphone.cancel(); super.onPause();
    }
    @Override protected void onDestroy() {
        microphone.cancel(); super.onDestroy();
    }
}
