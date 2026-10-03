package com.usernamemp.englishsprint;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.BackgroundColorSpan;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.Space;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;

public class MainActivity extends Activity {
    private static final int BG = Color.rgb(246, 247, 251);
    private static final int INK = Color.rgb(24, 29, 38);
    private static final int MUTED = Color.rgb(96, 105, 122);
    private static final int PRIMARY = Color.rgb(47, 82, 235);
    private static final int GOOD = Color.rgb(24, 145, 92);
    private static final int BAD = Color.rgb(205, 63, 72);
    private static final int CARD = Color.WHITE;
    private static final int SOFT = Color.rgb(232, 236, 246);
    private static final int HIGHLIGHT = Color.rgb(255, 236, 153);

    private ProgressStore progress;
    private AudioEngine audio;
    private RewardFx rewards;

    private List<Question> session = new ArrayList<>();
    private int questionIndex = 0;
    private int sessionCorrect = 0;
    private String sessionTitle = "";
    private final Map<String, int[]> sessionStats = new HashMap<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        QuestionBank.init(this);
        progress = new ProgressStore(this);
        audio = new AudioEngine(this);
        rewards = new RewardFx(this);
        getWindow().setStatusBarColor(BG);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);
        showHome();
    }

    @Override
    protected void onDestroy() {
        audio.shutdown();
        rewards.shutdown();
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        showHome();
    }

    private void showHome() {
        audio.stop();
        LinearLayout root = column();
        root.setPadding(dp(20), dp(18), dp(20), dp(30));

        LinearLayout header = row();
        LinearLayout titles = column();
        ContentPack pack = QuestionBank.currentPack();
        titles.addView(text(pack.title(Locale.getDefault()), 29, INK, Typeface.BOLD));
        titles.addView(text(pack.subtitle(Locale.getDefault()), 14, MUTED, Typeface.NORMAL));
        header.addView(titles, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        Button settings = compactButton("⚙");
        settings.setOnClickListener(v -> showSettings());
        header.addView(settings, new LinearLayout.LayoutParams(dp(52), dp(44)));
        root.addView(header);

        int days = daysUntilTarget();
        TextView deadline = text(days >= 0
                ? getString(R.string.deadline_remaining, days)
                : getString(R.string.training_mode), 14, PRIMARY, Typeface.BOLD);
        deadline.setPadding(0, dp(10), 0, 0);
        root.addView(deadline);

        root.addView(space(16));
        root.addView(progressCard());
        root.addView(space(16));

        Button play = primaryButton(getString(R.string.play));
        play.setTextSize(22);
        play.setMinHeight(dp(72));
        play.setOnClickListener(v -> startSession(getString(R.string.quick_training),
                QuestionBank.adaptiveSession(progress, 15, System.nanoTime())));
        root.addView(play, matchWrap());

        TextView playHint = text(getString(R.string.play_hint),
                13, MUTED, Typeface.NORMAL);
        playHint.setGravity(Gravity.CENTER);
        playHint.setPadding(0, dp(7), 0, dp(16));
        root.addView(playHint);

        TextView modes = text(getString(R.string.modes), 13, MUTED, Typeface.BOLD);
        root.addView(modes);
        root.addView(space(8));

        root.addView(menuButton(getString(R.string.grammar_mode), getString(R.string.grammar_caption), () ->
                startSession(getString(R.string.grammar_title), shuffled(QuestionBank.byType(Question.Type.GRAMMAR), 20))));

        root.addView(menuButton("⌕  Reading", getString(R.string.reading_caption), () ->
                startSession("Reading", shuffled(QuestionBank.byType(Question.Type.READING), 10))));

        root.addView(menuButton("▶  Listening", getString(R.string.listening_caption), () ->
                startSession("Listening", shuffled(QuestionBank.byType(Question.Type.LISTENING), 10))));

        root.addView(menuButton("✦  Story builder", getString(R.string.story_caption), () ->
                startSession("Story builder", shuffled(QuestionBank.byType(Question.Type.STORY), 10))));

        Button progressButton = secondaryButton(getString(R.string.skill_map));
        progressButton.setOnClickListener(v -> showProgress());
        LinearLayout.LayoutParams plp = matchWrap();
        plp.topMargin = dp(4);
        root.addView(progressButton, plp);

        setScrollable(root);
    }

    private View progressCard() {
        LinearLayout card = column();
        card.setPadding(dp(18), dp(16), dp(18), dp(16));
        card.setBackground(roundRect(CARD, 18, 0, Color.TRANSPARENT));

        LinearLayout top = row();
        TextView level = text(getString(R.string.level_fmt, progress.level()), 18, INK, Typeface.BOLD);
        TextView xp = text(progress.xp() + " XP", 16, PRIMARY, Typeface.BOLD);
        top.addView(level, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        top.addView(xp);
        card.addView(top);

        ProgressBar bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        bar.setMax(350);
        bar.setProgress(progress.xpInLevel());
        LinearLayout.LayoutParams barLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(8));
        barLp.topMargin = dp(10);
        card.addView(bar, barLp);

        TextView stats = text(getString(R.string.combo_stats_fmt, progress.combo(),
                progress.bestCombo(), progress.answered()), 13, MUTED, Typeface.NORMAL);
        LinearLayout.LayoutParams statsLp = matchWrap();
        statsLp.topMargin = dp(10);
        card.addView(stats, statsLp);

        TextView rank = text(getString(R.string.rank_fmt, rankForCombo(progress.bestCombo())),
                13, PRIMARY, Typeface.BOLD);
        LinearLayout.LayoutParams rankLp = matchWrap();
        rankLp.topMargin = dp(6);
        card.addView(rank, rankLp);

        return card;
    }

    private View menuButton(String heading, String caption, Runnable action) {
        LinearLayout box = column();
        box.setPadding(dp(18), dp(15), dp(18), dp(15));
        box.setBackground(roundRect(CARD, 16, 1, SOFT));
        box.setClickable(true);
        box.setFocusable(true);
        box.setOnClickListener(v -> action.run());

        TextView h = text(heading, 18, INK, Typeface.BOLD);
        TextView c = text(caption, 13, MUTED, Typeface.NORMAL);
        c.setPadding(0, dp(4), 0, 0);
        box.addView(h);
        box.addView(c);

        LinearLayout.LayoutParams lp = matchWrap();
        lp.bottomMargin = dp(10);
        box.setLayoutParams(lp);
        return box;
    }

    private void startSession(String title, List<Question> questions) {
        sessionTitle = title;
        session = new ArrayList<>(questions);
        questionIndex = 0;
        sessionCorrect = 0;
        sessionStats.clear();
        showQuestion();
    }

    private void showQuestion() {
        audio.stop();
        if (questionIndex >= session.size()) {
            showSessionResult();
            return;
        }

        Question q = session.get(questionIndex);
        LinearLayout root = column();
        root.setPadding(dp(18), dp(14), dp(18), dp(24));

        LinearLayout top = row();
        Button close = compactButton("←");
        close.setOnClickListener(v -> showHome());
        top.addView(close, new LinearLayout.LayoutParams(dp(52), dp(44)));

        TextView count = text((questionIndex + 1) + " / " + session.size(),
                14, MUTED, Typeface.BOLD);
        count.setGravity(Gravity.END | Gravity.CENTER_VERTICAL);
        LinearLayout.LayoutParams countLp = new LinearLayout.LayoutParams(
                0, dp(44), 1f);
        top.addView(count, countLp);
        root.addView(top);

        ProgressBar bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        bar.setMax(session.size());
        bar.setProgress(questionIndex);
        LinearLayout.LayoutParams pblp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(6));
        pblp.topMargin = dp(6);
        root.addView(bar, pblp);

        root.addView(space(16));

        TextView chip = text(skillName(q.skill), 13, PRIMARY, Typeface.BOLD);
        chip.setPadding(dp(10), dp(6), dp(10), dp(6));
        chip.setBackground(roundRect(Color.rgb(232, 237, 255), 20, 0, Color.TRANSPARENT));
        root.addView(chip, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        root.addView(space(12));

        TextView prompt = text(q.prompt, 24, INK, Typeface.BOLD);
        prompt.setLineSpacing(0, 1.08f);
        root.addView(prompt);

        TextView contextView = null;
        if (!q.context.isEmpty()) {
            contextView = text(q.context, 17, INK, Typeface.NORMAL);
            contextView.setLineSpacing(dp(4), 1.05f);
            contextView.setPadding(dp(16), dp(14), dp(16), dp(14));
            contextView.setBackground(roundRect(Color.rgb(238, 241, 247), 14, 0, Color.TRANSPARENT));
            LinearLayout.LayoutParams clp = matchWrap();
            clp.topMargin = dp(16);
            root.addView(contextView, clp);
        }
        final TextView contextForAnswer = contextView;

        int[] listensLeft = {2};
        if (q.type == Question.Type.LISTENING) {
            root.addView(space(16));
            Button play = primaryButton(getString(R.string.listen_first));
            play.setOnClickListener(v -> {
                if (listensLeft[0] <= 0) return;
                audio.play(q);
                listensLeft[0]--;
                play.setText(listensLeft[0] > 0
                        ? getString(R.string.listen_again_fmt, listensLeft[0])
                        : getString(R.string.listens_used));
                if (listensLeft[0] == 0) play.setEnabled(false);
            });
            root.addView(play, matchWrap());
        }

        root.addView(space(18));

        List<Button> answerButtons = new ArrayList<>();
        for (int i = 0; i < q.options.size(); i++) {
            final int answerIndex = i;
            Button b = answerButton(q.options.get(i));
            LinearLayout.LayoutParams blp = matchWrap();
            blp.bottomMargin = dp(10);
            root.addView(b, blp);
            answerButtons.add(b);
            b.setOnClickListener(v -> handleAnswer(
                    root, q, answerIndex, answerButtons, contextForAnswer));
        }

        TextView footer = text("XP " + progress.xp() + "   ·   combo ×" + progress.combo(),
                13, MUTED, Typeface.BOLD);
        footer.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams flp = matchWrap();
        flp.topMargin = dp(8);
        root.addView(footer, flp);

        setScrollable(root);
    }

    private void handleAnswer(LinearLayout root, Question q, int chosen,
                              List<Button> buttons, TextView contextView) {
        boolean correct = q.isCorrect(chosen);
        progress.record(q, correct);
        RewardFx.Reaction reaction = rewards.reaction(correct, progress.combo());
        rewards.play(reaction, correct, progress.combo());
        if (correct) sessionCorrect++;

        int[] stats = sessionStats.computeIfAbsent(q.skill, k -> new int[]{0, 0});
        stats[0]++;
        if (correct) stats[1]++;

        for (int i = 0; i < buttons.size(); i++) {
            Button b = buttons.get(i);
            b.setEnabled(false);
            if (i == q.correctIndex) {
                b.setBackground(roundRect(Color.rgb(221, 245, 234), 14, 2, GOOD));
                b.setTextColor(Color.rgb(15, 105, 67));
            } else if (i == chosen) {
                b.setBackground(roundRect(Color.rgb(255, 244, 215), 14, 2, Color.rgb(210, 160, 60)));
                b.setTextColor(Color.rgb(135, 88, 15));
            }
        }

        if (contextView != null && !q.evidence.isEmpty()) {
            highlightEvidence(contextView, q.context, q.evidence);
        }

        LinearLayout feedback = column();
        feedback.setPadding(dp(16), dp(14), dp(16), dp(14));
        feedback.setBackground(roundRect(
                correct ? Color.rgb(232, 248, 240) : Color.rgb(246, 247, 251),
                14, 0, Color.TRANSPARENT));

        TextView verdict = text(reaction.symbol + "  " + reaction.headline,
                17, correct ? GOOD : MUTED, Typeface.BOLD);
        feedback.addView(verdict);

        TextView reactionLine = text(reaction.subline, 14, INK, Typeface.NORMAL);
        reactionLine.setPadding(0, dp(5), 0, 0);
        feedback.addView(reactionLine);

        if (!correct) {
            String quote = rewards.quoteForMistake();
            if (!quote.isEmpty()) {
                TextView quoteView = text(quote, 13, MUTED, Typeface.NORMAL);
                quoteView.setPadding(0, dp(9), 0, 0);
                feedback.addView(quoteView);
            }
        }

        if (!q.explanation.isEmpty()) {
            TextView expl = text(q.explanation, 17, INK, Typeface.BOLD);
            expl.setLineSpacing(dp(3), 1.05f);
            expl.setPadding(0, dp(9), 0, 0);
            feedback.addView(expl);
        }

        if (!q.explanationFull.isEmpty()) {
            Button why = secondaryButton(getString(R.string.why));
            why.setTextSize(15);
            why.setMinHeight(dp(46));
            why.setOnClickListener(v -> showExplanationDialog(q));
            LinearLayout.LayoutParams wlp = matchWrap();
            wlp.topMargin = dp(10);
            feedback.addView(why, wlp);
        }

        LinearLayout.LayoutParams fLp = matchWrap();
        fLp.topMargin = dp(8);
        root.addView(feedback, fLp);

        Button next = primaryButton(questionIndex + 1 < session.size() ? getString(R.string.next) : getString(R.string.result));
        next.setOnClickListener(v -> {
            questionIndex++;
            showQuestion();
        });
        LinearLayout.LayoutParams nlp = matchWrap();
        nlp.topMargin = dp(12);
        root.addView(next, nlp);

        // Keep the newly added feedback visible on large and small phones.
        root.post(() -> {
            View parent = (View) root.getParent();
            if (parent instanceof ScrollView) {
                ((ScrollView) parent).smoothScrollTo(0, root.getBottom());
            }
        });
    }

    private void showSessionResult() {
        audio.stop();
        LinearLayout root = column();
        root.setPadding(dp(20), dp(28), dp(20), dp(30));

        int percent = session.isEmpty() ? 0 : Math.round(sessionCorrect * 100f / session.size());
        TextView title = text(sessionTitle, 18, MUTED, Typeface.BOLD);
        root.addView(title);

        TextView score = text(sessionCorrect + " / " + session.size(), 48,
                percent >= 75 ? GOOD : INK, Typeface.BOLD);
        score.setPadding(0, dp(10), 0, 0);
        root.addView(score);

        TextView percentView = text(percent + "%", 20, MUTED, Typeface.BOLD);
        root.addView(percentView);

        root.addView(space(22));

        TextView weakTitle = text(getString(R.string.what_next), 20, INK, Typeface.BOLD);
        root.addView(weakTitle);
        root.addView(space(8));

        List<Map.Entry<String, int[]>> entries = new ArrayList<>(sessionStats.entrySet());
        entries.sort(Comparator.comparingDouble(e -> {
            int[] s = e.getValue();
            return s[0] == 0 ? 1.0 : (double) s[1] / s[0];
        }));

        int shown = 0;
        for (Map.Entry<String, int[]> e : entries) {
            int[] s = e.getValue();
            if (shown >= 4) break;
            ProgressStore.SkillState skillState = progress.state(e.getKey());
            TextView row = text(skillName(e.getKey()) + "   ·   " + skillStateLabel(skillState), 16,
                    INK, Typeface.NORMAL);
            row.setPadding(0, dp(6), 0, dp(6));
            root.addView(row);
            shown++;
        }

        root.addView(space(20));

        Button again = primaryButton(getString(R.string.another_quick));
        again.setOnClickListener(v -> startSession(getString(R.string.quick_training),
                QuestionBank.adaptiveSession(progress, 15, System.nanoTime())));
        root.addView(again, matchWrap());

        Button home = secondaryButton(getString(R.string.home));
        home.setOnClickListener(v -> showHome());
        LinearLayout.LayoutParams hlp = matchWrap();
        hlp.topMargin = dp(10);
        root.addView(home, hlp);

        setScrollable(root);
    }

    private void showProgress() {
        LinearLayout root = column();
        root.setPadding(dp(20), dp(20), dp(20), dp(28));

        Button back = compactButton("←");
        back.setOnClickListener(v -> showHome());
        root.addView(back, new LinearLayout.LayoutParams(dp(52), dp(44)));

        root.addView(space(14));
        root.addView(text(getString(R.string.skill_map), 28, INK, Typeface.BOLD));
        root.addView(text(getString(R.string.skill_map_caption),
                14, MUTED, Typeface.NORMAL));
        root.addView(space(16));

        List<String> skills = new ArrayList<>(QuestionBank.knowledgeIds());
        skills.sort((a, b) -> {
            int state = Integer.compare(progress.state(a).ordinal(), progress.state(b).ordinal());
            if (state != 0) return state;
            return Integer.compare(progress.attempts(a), progress.attempts(b));
        });

        for (String skill : skills) {
            ProgressStore.SkillState state = progress.state(skill);
            LinearLayout line = row();
            line.setPadding(dp(14), dp(13), dp(14), dp(13));
            line.setBackground(roundRect(CARD, 12, 1, SOFT));

            TextView name = text(skillName(skill), 15, INK, Typeface.BOLD);
            int stateColor;
            switch (state) {
                case CONFIDENT: stateColor = GOOD; break;
                case GROWING: stateColor = Color.rgb(176, 119, 20); break;
                case LEARNING: stateColor = PRIMARY; break;
                default: stateColor = MUTED;
            }
            TextView value = text(skillStateLabel(state), 14, stateColor, Typeface.BOLD);
            line.addView(name, new LinearLayout.LayoutParams(0,
                    ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
            line.addView(value);

            LinearLayout.LayoutParams lp = matchWrap();
            lp.bottomMargin = dp(7);
            root.addView(line, lp);
        }

        setScrollable(root);
    }

    private void showExplanationDialog(Question q) {
        LinearLayout box = column();
        box.setPadding(dp(22), dp(18), dp(22), dp(12));

        TextView ruleTitle = text(getString(R.string.rule_label), 12, PRIMARY, Typeface.BOLD);
        box.addView(ruleTitle);

        TextView rule = text(q.rule.isEmpty() ? q.explanation : q.rule,
                21, INK, Typeface.BOLD);
        rule.setPadding(0, dp(7), 0, dp(16));
        rule.setLineSpacing(dp(3), 1.05f);
        box.addView(rule);

        TextView whyTitle = text(getString(R.string.why_here_label), 12, MUTED, Typeface.BOLD);
        box.addView(whyTitle);

        TextView full = text(q.explanationFull, 17, INK, Typeface.NORMAL);
        full.setLineSpacing(dp(5), 1.06f);
        full.setPadding(0, dp(7), 0, dp(8));
        box.addView(full);

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setView(box)
                .setPositiveButton(getString(R.string.got_it), null)
                .create();
        dialog.setOnShowListener(d -> {
            if (dialog.getWindow() != null) {
                dialog.getWindow().setLayout(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT);
            }
        });
        dialog.show();
        if (dialog.getWindow() != null) {
            dialog.getWindow().setLayout(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT);
        }
    }

    private void showSettings() {
        LinearLayout root = column();
        root.setPadding(dp(20), dp(20), dp(20), dp(28));

        Button back = compactButton("←");
        back.setOnClickListener(v -> showHome());
        root.addView(back, new LinearLayout.LayoutParams(dp(52), dp(44)));
        root.addView(space(14));
        root.addView(text(getString(R.string.settings), 28, INK, Typeface.BOLD));
        root.addView(text(getString(R.string.settings_caption),
                14, MUTED, Typeface.NORMAL));
        root.addView(space(18));

        android.widget.Switch sound = new android.widget.Switch(this);
        sound.setText(getString(R.string.combo_sounds));
        sound.setTextSize(17);
        sound.setChecked(getSharedPreferences("english_sprint_settings", MODE_PRIVATE)
                .getBoolean("sound", true));
        sound.setPadding(dp(12), dp(12), dp(12), dp(12));
        sound.setOnCheckedChangeListener((buttonView, isChecked) ->
                getSharedPreferences("english_sprint_settings", MODE_PRIVATE)
                        .edit().putBoolean("sound", isChecked).apply());
        root.addView(sound, matchWrap());

        android.widget.Switch haptic = new android.widget.Switch(this);
        haptic.setText(getString(R.string.haptics));
        haptic.setTextSize(17);
        haptic.setChecked(getSharedPreferences("english_sprint_settings", MODE_PRIVATE)
                .getBoolean("haptic", true));
        haptic.setPadding(dp(12), dp(12), dp(12), dp(12));
        haptic.setOnCheckedChangeListener((buttonView, isChecked) ->
                getSharedPreferences("english_sprint_settings", MODE_PRIVATE)
                        .edit().putBoolean("haptic", isChecked).apply());
        root.addView(haptic, matchWrap());

        setScrollable(root);
    }

    private void highlightEvidence(TextView view, String source, String evidence) {
        SpannableString span = new SpannableString(source);
        int start = source.toLowerCase(Locale.US).indexOf(evidence.toLowerCase(Locale.US));
        if (start >= 0) {
            span.setSpan(new BackgroundColorSpan(HIGHLIGHT), start, start + evidence.length(),
                    Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        }
        view.setText(span);
    }

    private List<Question> shuffled(List<Question> input, int max) {
        List<Question> list = new ArrayList<>(input);
        Collections.shuffle(list, new Random(System.nanoTime()));
        if (list.size() > max) return new ArrayList<>(list.subList(0, max));
        return list;
    }

    private String skillStateLabel(ProgressStore.SkillState state) {
        switch (state) {
            case CONFIDENT: return getString(R.string.state_confident);
            case GROWING: return getString(R.string.state_growing);
            case LEARNING: return getString(R.string.state_learning);
            default: return getString(R.string.state_not_checked);
        }
    }

    private String rankForCombo(int combo) {
        if (combo >= 15) return getString(R.string.rank_unstoppable);
        if (combo >= 10) return getString(R.string.rank_legend);
        if (combo >= 8) return getString(R.string.rank_machine);
        if (combo >= 5) return getString(R.string.rank_five);
        if (combo >= 3) return getString(R.string.rank_warmup);
        return getString(R.string.rank_rookie);
    }

    private String skillName(String skill) {
        KnowledgeUnit unit = QuestionBank.knowledgeUnit(skill);
        if (unit == null) {
            String knowledgeId = QuestionBank.primaryKnowledgeForLegacy(skill);
            unit = QuestionBank.knowledgeUnit(knowledgeId);
        }
        return unit == null ? skill : unit.label(Locale.getDefault());
    }

    private int daysUntilTarget() {
        Calendar now = Calendar.getInstance();
        Calendar target = Calendar.getInstance();
        target.set(2026, Calendar.OCTOBER, 9, 0, 0, 0);
        target.set(Calendar.MILLISECOND, 0);
        Calendar today = (Calendar) now.clone();
        today.set(Calendar.HOUR_OF_DAY, 0);
        today.set(Calendar.MINUTE, 0);
        today.set(Calendar.SECOND, 0);
        today.set(Calendar.MILLISECOND, 0);
        long delta = target.getTimeInMillis() - today.getTimeInMillis();
        return (int) Math.floor(delta / 86400000.0);
    }

    private LinearLayout column() {
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setBackgroundColor(BG);
        return l;
    }

    private LinearLayout row() {
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.HORIZONTAL);
        l.setGravity(Gravity.CENTER_VERTICAL);
        return l;
    }

    private void setScrollable(LinearLayout content) {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);
        scroll.addView(content, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        setContentView(scroll);
    }

    private TextView text(String value, float sp, int color, int style) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(sp);
        t.setTextColor(color);
        t.setTypeface(Typeface.DEFAULT, style);
        return t;
    }

    private Button answerButton(String value) {
        Button b = new Button(this);
        b.setText(value);
        b.setTextSize(18);
        b.setTextColor(INK);
        b.setAllCaps(false);
        b.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        b.setPadding(dp(18), dp(10), dp(18), dp(10));
        b.setMinHeight(dp(64));
        b.setBackground(roundRect(CARD, 14, 1, SOFT));
        return b;
    }

    private Button primaryButton(String value) {
        Button b = new Button(this);
        b.setText(value);
        b.setTextSize(17);
        b.setTextColor(Color.WHITE);
        b.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        b.setAllCaps(false);
        b.setMinHeight(dp(58));
        b.setBackground(roundRect(PRIMARY, 14, 0, Color.TRANSPARENT));
        return b;
    }

    private Button secondaryButton(String value) {
        Button b = new Button(this);
        b.setText(value);
        b.setTextSize(16);
        b.setTextColor(INK);
        b.setAllCaps(false);
        b.setMinHeight(dp(54));
        b.setBackground(roundRect(CARD, 14, 1, SOFT));
        return b;
    }

    private Button compactButton(String value) {
        Button b = new Button(this);
        b.setText(value);
        b.setTextSize(20);
        b.setTextColor(INK);
        b.setAllCaps(false);
        b.setPadding(0, 0, 0, 0);
        b.setBackground(roundRect(CARD, 12, 1, SOFT));
        return b;
    }

    private GradientDrawable roundRect(int fill, int radiusDp, int strokeDp, int stroke) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(fill);
        g.setCornerRadius(dp(radiusDp));
        if (strokeDp > 0) g.setStroke(dp(strokeDp), stroke);
        return g;
    }

    private Space space(int heightDp) {
        Space s = new Space(this);
        s.setLayoutParams(new LinearLayout.LayoutParams(1, dp(heightDp)));
        return s;
    }

    private LinearLayout.LayoutParams matchWrap() {
        return new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
