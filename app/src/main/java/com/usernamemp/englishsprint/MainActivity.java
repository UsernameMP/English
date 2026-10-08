package com.usernamemp.englishsprint;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Build;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.Html;
import android.text.style.BackgroundColorSpan;
import android.text.style.ClickableSpan;
import android.text.method.LinkMovementMethod;
import android.text.TextPaint;
import android.view.Gravity;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.Space;
import android.widget.TextView;
import android.text.InputType;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.Locale;
import java.util.Map;
import java.util.Random;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MainActivity extends Activity {
    private static final int BG = RiftStyle.BACKGROUND;
    private static final int INK = RiftStyle.INK;
    private static final int MUTED = RiftStyle.MUTED;
    private static final int PRIMARY = RiftStyle.BLUE;
    private static final int GOOD = RiftStyle.GOOD;
    private static final int BAD = Color.rgb(205, 63, 72);
    private static final int CARD = Color.WHITE;
    private static final int SOFT = RiftStyle.STROKE;
    private static final int HIGHLIGHT = Color.rgb(255, 236, 153);

    private ProgressStore progress;
    private AudioEngine audio;
    private RewardFx rewards;
    private DictionaryStore dictionary;
    private DictionaryRepository dictionaryRepository;
    private EconomyStore economy;
    private PlayCreditStore playCredits;
    private TrainingTargetStore trainingTarget;
    private LearningContextStore learningContext;
    private ActivityStore activity;
    private ShopStore shop;
    private DigitalRewardStore digitalRewards;
    private WorkshopStore workshop;
    private MetaGameStore metaGame;
    private LearningEventStore learningEvents;
    private MiniGameHost miniGames;
    private UpdateManager updater;
    private boolean homeVisible = false;

    private List<Question> session = new ArrayList<>();
    private int questionIndex = 0;
    private int sessionCorrect = 0;
    private String sessionTitle = "";
    private final Map<String, int[]> sessionStats = new HashMap<>();
    private final Set<String> reinforcementKnowledge = new HashSet<>();
    private final Set<String> reinforcementQuestionIds = new HashSet<>();
    private final Random sessionRandom = new Random();
    private int sessionBestBefore = 0;
    private boolean newRecordCelebrated = false;
    private int sessionAnswered = 0;
    private long questionShownAtMs = 0L;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LocaleStore.apply(this);
        QuestionBank.init(this);
        progress = new ProgressStore(this);
        dictionary = new DictionaryStore(this);
        dictionaryRepository = new DictionaryRepository(this, dictionary);
        economy = new EconomyStore(this);
        playCredits = new PlayCreditStore(this);
        trainingTarget = new TrainingTargetStore(this, QuestionBank.currentPack());
        learningContext = new LearningContextStore(this);
        if (!learningContext.hasSelection()
                && getSharedPreferences("english_sprint_settings", MODE_PRIVATE).contains("selected_pack")) {
            ContentPack selected = QuestionBank.currentPack();
            learningContext.remember(selected.id, selected.gradeMin, selected.competition);
        }
        if (learningContext.isValidFor(QuestionBank.currentPack())) {
            trainingTarget.selectContext(QuestionBank.currentPack(), learningContext.grade(), learningContext.target());
        }
        activity = new ActivityStore(this);
        shop = new ShopStore(this, economy);
        digitalRewards = new DigitalRewardStore(this, economy);
        workshop = new WorkshopStore(this, economy);
        metaGame = new MetaGameStore(this, economy);
        learningEvents = new LearningEventStore(this);
        miniGames = new MiniGameHost(this, economy);
        audio = new AudioEngine(this);
        rewards = new RewardFx(this);
        updater = new UpdateManager(this);
        getWindow().setStatusBarColor(BG);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);
        hideSystemNavigation();
        showHome();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (updater != null) updater.tryInstallPendingUpdate();
    }

    @Override
    protected void onDestroy() {
        audio.shutdown();
        rewards.shutdown();
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        if (miniGames != null && miniGames.abortActive()) {
            hideSystemNavigation();
            return;
        }
        if (homeVisible) {
            finish();
            return;
        }
        showHome();
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideSystemNavigation();
    }

    @Override
    public void setContentView(View view) {
        super.setContentView(view);

        // Android 15+ draws app content behind the transparent status bar.
        // Account for the actual system-bar/cutout height on every screen,
        // without altering pre-Android-15 layout behavior or immersive navigation.
        if (Build.VERSION.SDK_INT < 35) return;

        final int left = view.getPaddingLeft();
        final int top = view.getPaddingTop();
        final int right = view.getPaddingRight();
        final int bottom = view.getPaddingBottom();
        view.setOnApplyWindowInsetsListener((target, insets) -> {
            int safeTop = insets.getInsets(
                    WindowInsets.Type.statusBars() | WindowInsets.Type.displayCutout()).top;
            target.setPadding(left, top + safeTop, right, bottom);
            return insets;
        });
        view.requestApplyInsets();
    }

    private void hideSystemNavigation() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                controller.hide(WindowInsets.Type.navigationBars());
                controller.setSystemBarsBehavior(
                        WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
            }
        } else {
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        }
    }

    private void showHome() {
        homeVisible = true;
        hideSystemNavigation();
        audio.stop();
        LinearLayout root = column();
        root.setPadding(dp(20), dp(18), dp(20), dp(36));

        LinearLayout masthead = row();
        TextView mark = text("R", 26, Color.WHITE, Typeface.BOLD);
        mark.setGravity(Gravity.CENTER);
        mark.setBackground(RiftStyle.gradient(this, 17,
                RiftStyle.BLUE, RiftStyle.VIOLET));
        RiftStyle.raise(mark, 3);
        masthead.addView(mark, new LinearLayout.LayoutParams(dp(52), dp(52)));
        LinearLayout brand = column();
        brand.setPadding(dp(12), 0, 0, 0);
        brand.addView(text(getString(R.string.app_name), 28, INK, Typeface.BOLD));
        brand.addView(text(getString(R.string.rift_eyebrow), 12, MUTED, Typeface.NORMAL));
        masthead.addView(brand, new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        Button settings = compactButton("⚙");
        settings.setContentDescription(getString(R.string.settings));
        settings.setOnClickListener(v -> showSettings());
        masthead.addView(settings, new LinearLayout.LayoutParams(dp(50), dp(50)));
        root.addView(masthead);
        root.addView(space(22));

        LinearLayout hero = column();
        hero.setPadding(dp(22), dp(22), dp(22), dp(22));
        hero.setBackground(RiftStyle.cosmic(this, 26));
        RiftStyle.raise(hero, 8);

        TextView label = text(getString(R.string.rift_hero_kicker), 12,
                RiftStyle.CYAN, Typeface.BOLD);
        label.setLetterSpacing(.14f);
        hero.addView(label);
        hero.addView(space(14));
        TextView title = text(getString(R.string.rift_hero_title), 30,
                Color.WHITE, Typeface.BOLD);
        title.setLineSpacing(dp(3), 1f);
        hero.addView(title);
        hero.addView(space(8));
        TextView detail = text(getString(R.string.rift_hero_subtitle), 15,
                Color.rgb(214, 224, 255), Typeface.NORMAL);
        detail.setLineSpacing(dp(3), 1f);
        hero.addView(detail);
        hero.addView(space(22));

        Button start = primaryButton(getString(R.string.learn_now) + "  →");
        start.setBackground(RiftStyle.shape(this, Color.WHITE, 17, 0, Color.TRANSPARENT));
        start.setTextColor(RiftStyle.NAVY);
        start.setMinHeight(dp(60));
        start.setOnClickListener(v -> showLearnHub());
        hero.addView(start, matchWrap());
        root.addView(hero, matchWrap());

        root.addView(space(20));
        root.addView(progressCard());
        root.addView(space(23));

        root.addView(sectionHeading(getString(R.string.rift_explore), getString(R.string.rift_explore_caption)));
        root.addView(space(12));
        root.addView(featureCard("◇", getString(R.string.skill_map),
                getString(R.string.rift_atlas_caption), RiftStyle.BLUE, () -> showProgress()));
        root.addView(space(10));
        root.addView(featureCard("✦", getString(R.string.my_world),
                getString(R.string.rift_world_caption), RiftStyle.VIOLET, () -> showMyWorld()));
        root.addView(space(10));
        root.addView(featureCard("◈", getString(R.string.shop),
                getString(R.string.rift_shop_caption), RiftStyle.GOOD, () -> showShop()));
        setScrollable(root);
    }

    private void showLearnHub() {
        homeVisible = false;
        if (restoreLearningContext()) showTrainingHub();
        else showCourseStorefront();
    }

    private boolean restoreLearningContext() {
        if (!learningContext.hasSelection()) return false;
        ContentPack remembered = null;
        for (ContentPack pack : QuestionBank.availablePacks()) {
            if (pack.id.equals(learningContext.packId())) remembered = pack;
        }
        if (remembered == null || !learningContext.isValidFor(remembered)) return false;
        if (!QuestionBank.currentPack().id.equals(remembered.id)) {
            QuestionBank.selectPack(this, remembered.id);
            trainingTarget = new TrainingTargetStore(this, QuestionBank.currentPack());
        }
        trainingTarget.selectContext(remembered, learningContext.grade(), learningContext.target());
        return true;
    }

    private void showCourseStorefront() {
        audio.stop();
        LinearLayout root = column();
        root.setPadding(dp(20), dp(18), dp(20), dp(34));
        Button back = compactButton("←");
        back.setContentDescription(getString(R.string.home));
        back.setOnClickListener(v -> showHome());
        root.addView(back, new LinearLayout.LayoutParams(dp(52), dp(48)));
        root.addView(space(24));

        TextView eyebrow = text(getString(R.string.rift_course_kicker), 12, PRIMARY, Typeface.BOLD);
        eyebrow.setLetterSpacing(.14f);
        root.addView(eyebrow);
        root.addView(space(6));
        root.addView(text(getString(R.string.choose_subject), 30, INK, Typeface.BOLD));
        TextView caption = text(getString(R.string.choose_subject_caption), 15, MUTED, Typeface.NORMAL);
        caption.setPadding(0, dp(7), 0, 0);
        root.addView(caption);
        root.addView(space(22));

        ContentCatalog catalog = new ContentCatalog(this);
        EntitlementStore entitlements = new EntitlementStore(this);
        EntitlementProductCatalog products = new EntitlementProductCatalog(this);
        List<String> subjects = catalog.subjects();
        for (int i = 0; i < subjects.size(); i += 2) {
            LinearLayout line = row();
            for (int j = i; j < Math.min(i + 2, subjects.size()); j++) {
                String subject = subjects.get(j);
                boolean unlocked = subjectUnlocked(subject, catalog, entitlements);
                int index = j;
                View tile = subjectCard(subject, unlocked, () -> {
                    if (unlocked) showGradePicker(subject);
                    else showSubscriptionOffer(subject, products);
                });
                LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                        0, dp(152), 1f);
                if (index % 2 == 1) lp.leftMargin = dp(10);
                line.addView(tile, lp);
            }
            if (line.getChildCount() == 1) line.addView(new View(this),
                    new LinearLayout.LayoutParams(0, dp(152), 1f));
            LinearLayout.LayoutParams lp = matchWrap();
            lp.bottomMargin = dp(10);
            root.addView(line, lp);
        }
        setScrollable(root);
    }

    private String subjectGlyph(String subject) {
        if ("english".equals(subject)) return "Aa";
        if ("mathematics".equals(subject)) return "∑";
        if ("informatics".equals(subject)) return "</>";
        if ("biology".equals(subject)) return "DNA";
        if ("geography".equals(subject)) return "◎";
        if ("history".equals(subject)) return "⌛";
        if ("ecology".equals(subject)) return "♧";
        if ("social_science".equals(subject)) return "§";
        return "✦";
    }

    private int subjectTint(String subject) {
        if ("english".equals(subject)) return RiftStyle.BLUE;
        if ("mathematics".equals(subject)) return RiftStyle.VIOLET;
        if ("biology".equals(subject) || "ecology".equals(subject)) return RiftStyle.GOOD;
        if ("geography".equals(subject)) return Color.rgb(13, 146, 195);
        if ("history".equals(subject)) return Color.rgb(198, 121, 49);
        return Color.rgb(90, 93, 172);
    }

    private View subjectCard(String subject, boolean unlocked, Runnable onClick) {
        int tint = subjectTint(subject);
        LinearLayout tile = column();
        tile.setPadding(dp(16), dp(16), dp(12), dp(13));
        tile.setBackground(RiftStyle.shape(this, Color.WHITE, 21, 1, SOFT));
        RiftStyle.raise(tile, 2);
        TextView glyph = text(subjectGlyph(subject),
                subjectGlyph(subject).length() > 2 ? 16 : 27, tint, Typeface.BOLD);
        glyph.setGravity(Gravity.CENTER);
        glyph.setBackground(RiftStyle.shape(this,
                tint == RiftStyle.GOOD ? Color.rgb(233, 249, 239)
                        : Color.rgb(238, 239, 255), 16, 0, Color.TRANSPARENT));
        tile.addView(glyph, new LinearLayout.LayoutParams(dp(51), dp(51)));
        tile.addView(space(15));
        TextView name = text(subjectLabel(subject), 15, INK, Typeface.BOLD);
        name.setMaxLines(2);
        name.setEllipsize(android.text.TextUtils.TruncateAt.END);
        tile.addView(name);
        tile.addView(space(5));
        tile.addView(text(getString(unlocked ? R.string.rift_open : R.string.rift_locked),
                12, unlocked ? tint : MUTED, Typeface.BOLD));
        tile.setAlpha(unlocked ? 1f : .78f);
        tile.setOnClickListener(v -> onClick.run());
        return tile;
    }

    private boolean subjectUnlocked(String subject,ContentCatalog catalog,EntitlementStore entitlements){
        for(ContentCatalog.Course c:catalog.courses()) if(c.subject.equals(subject)&&entitlements.canAccessPack(c.packId)) return true;
        return false;
    }

    private String subjectLabel(String subject){
        if("english".equals(subject)) return getString(R.string.subject_english);
        if("mathematics".equals(subject)) return getString(R.string.subject_math);
        if("informatics".equals(subject)) return getString(R.string.subject_informatics);
        if("geography".equals(subject)) return getString(R.string.subject_geography);
        if("biology".equals(subject)) return getString(R.string.subject_biology);
        if("history".equals(subject)) return getString(R.string.subject_history);
        if("social_science".equals(subject)) return getString(R.string.subject_social_science);
        if("ecology".equals(subject)) return getString(R.string.subject_ecology);
        return subject;
    }

    private void showSubscriptionOffer(String subject,EntitlementProductCatalog products){
        EntitlementProductCatalog.Product product=products.subscriptionForSubject(subject);
        String detail=product==null?getString(R.string.subscription_coming):getString(R.string.subscription_required_body,subjectLabel(subject));
        new AlertDialog.Builder(this).setTitle("🔒 "+subjectLabel(subject)).setMessage(detail)
                .setPositiveButton(getString(R.string.subscription_action),(d,w)->{})
                .setNegativeButton(getString(R.string.dictionary_close),null).show();
    }

    private void showGradePicker(String subject){
        ContentCatalog catalog=new ContentCatalog(this);
        List<Integer> grades=catalog.grades(subject);
        LinearLayout root=column(); root.setPadding(dp(20),dp(18),dp(20),dp(30));
        Button back=compactButton("←"); back.setOnClickListener(v->showCourseStorefront()); root.addView(back,new LinearLayout.LayoutParams(dp(52),dp(44)));
        root.addView(space(12)); root.addView(text(getString(R.string.choose_grade),28,INK,Typeface.BOLD));
        root.addView(text(subjectLabel(subject),14,MUTED,Typeface.NORMAL)); root.addView(space(14));
        LinearLayout line=null;
        for(int i=0;i<grades.size();i++){
            if(i%3==0){line=row(); root.addView(line,matchWrap());}
            final int grade=grades.get(i);
            Button b=secondaryButton(String.valueOf(grade)); b.setTextSize(20); b.setOnClickListener(v->showCompetitionPicker(subject,grade));
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(66),1f); if(i%3>0)lp.leftMargin=dp(8); line.addView(b,lp);
        }
        setScrollable(root);
    }

    private void showCompetitionPicker(String subject,int grade){
        ContentCatalog catalog=new ContentCatalog(this);
        List<ContentCatalog.Course> courses=catalog.applicable(subject,grade);
        LinearLayout root=column(); root.setPadding(dp(20),dp(18),dp(20),dp(30));
        Button back=compactButton("←"); back.setOnClickListener(v->showGradePicker(subject)); root.addView(back,new LinearLayout.LayoutParams(dp(52),dp(44)));
        root.addView(space(12)); root.addView(text(getString(R.string.choose_goal),28,INK,Typeface.BOLD));
        root.addView(text(subjectLabel(subject)+" · "+getString(R.string.grade_fmt,grade),14,MUTED,Typeface.NORMAL)); root.addView(space(14));
        Button all=primaryButton(getString(R.string.all_olympiads)); all.setOnClickListener(v->selectFirstApplicable(courses,grade)); root.addView(all,matchWrap());
        root.addView(space(10));
        for(ContentCatalog.Course c:courses){
            Button b=secondaryButton(competitionLabel(c.competition));
            b.setOnClickListener(v->selectCourse(c.packId,grade,c.competition));
            LinearLayout.LayoutParams lp=matchWrap(); lp.bottomMargin=dp(8); root.addView(b,lp);
        }
        setScrollable(root);
    }

    private String competitionLabel(String raw){
        if("VSOSh".equalsIgnoreCase(raw)) return getString(R.string.vsosh);
        if("Olympiad pilot".equalsIgnoreCase(raw)) return getString(R.string.olympiad_pilot);
        if("Olympiad bridge".equalsIgnoreCase(raw)) return getString(R.string.olympiad_bridge);
        return raw;
    }

    private void selectFirstApplicable(List<ContentCatalog.Course> courses,int grade){
        if(!courses.isEmpty()) selectCourse(courses.get(0).packId,grade,LearningContextStore.ALL_OLYMPIADS);
    }

    private void selectCourse(String packId,int grade,String target){
        QuestionBank.selectPack(this,packId);
        learningContext.remember(packId,grade,target);
        trainingTarget=new TrainingTargetStore(this,QuestionBank.currentPack());
        trainingTarget.selectContext(QuestionBank.currentPack(),grade,target);
        showTrainingHub();
    }

    private void showTrainingHub() {
        LinearLayout root = column();
        root.setPadding(dp(20), dp(18), dp(20), dp(36));
        Button back = compactButton("←");
        back.setOnClickListener(v -> showHome());
        root.addView(back, new LinearLayout.LayoutParams(dp(52), dp(48)));
        root.addView(space(22));

        TextView kicker = text(getString(R.string.rift_training_kicker),
                12, PRIMARY, Typeface.BOLD);
        kicker.setLetterSpacing(.14f);
        root.addView(kicker);
        root.addView(space(6));
        root.addView(text(getString(R.string.learn_title), 30, INK, Typeface.BOLD));
        root.addView(space(18));
        String target = learningContext.target();
        String targetLabel = LearningContextStore.ALL_OLYMPIADS.equals(target)
                ? getString(R.string.all_olympiads) : competitionLabel(target);

        LinearLayout hero = column();
        hero.setPadding(dp(20), dp(21), dp(20), dp(21));
        hero.setBackground(RiftStyle.cosmic(this, 23));
        RiftStyle.raise(hero, 5);
        TextView label = text(subjectLabel(QuestionBank.currentPack().subject), 24,
                Color.WHITE, Typeface.BOLD);
        hero.addView(label);
        hero.addView(space(5));
        hero.addView(text(getString(R.string.grade_fmt, learningContext.grade())
                        + " · " + targetLabel, 14, Color.rgb(212, 224, 255), Typeface.NORMAL));
        hero.addView(space(19));
        Button auto = primaryButton(getString(R.string.auto_training) + "  →");
        auto.setBackground(RiftStyle.shape(this, Color.WHITE, 17, 0, Color.TRANSPARENT));
        auto.setTextColor(RiftStyle.NAVY);
        auto.setOnClickListener(v -> startSession(getString(R.string.quick_training), quickSession()));
        hero.addView(auto, matchWrap());
        root.addView(hero, matchWrap());

        root.addView(space(10));
        Button change = secondaryButton(getString(R.string.change_course) + "  ↗");
        change.setOnClickListener(v -> showCourseStorefront());
        root.addView(change, matchWrap());
        root.addView(space(24));

        root.addView(sectionHeading(getString(R.string.choose_topic),
                getString(R.string.rift_explore_caption)));
        root.addView(space(13));
        if ("english".equals(QuestionBank.currentPack().subject))
            addTopicGrid(root, new String[]{"A+", "⌕", "♫", "✦"},
                    new int[]{R.string.grammar_title, R.string.reading_title,
                            R.string.listening_title, R.string.story_title},
                    new Question.Type[]{Question.Type.GRAMMAR, Question.Type.READING,
                            Question.Type.LISTENING, Question.Type.STORY});
        else addKnowledgeTopicGrid(root);

        root.addView(space(14));
        root.addView(featureCard("◇", getString(R.string.skill_map),
                getString(R.string.rift_atlas_caption), RiftStyle.BLUE, () -> showProgress()));
        setScrollable(root);
    }

    private View topicCard(String glyph, String title, int color, Runnable action) {
        LinearLayout tile = column();
        tile.setPadding(dp(15), dp(15), dp(14), dp(12));
        tile.setBackground(RiftStyle.shape(this, Color.WHITE, 19, 1, SOFT));
        TextView badge = text(glyph, 24, color, Typeface.BOLD);
        badge.setGravity(Gravity.CENTER);
        badge.setBackground(RiftStyle.shape(this, Color.rgb(239, 240, 255),
                14, 0, Color.TRANSPARENT));
        tile.addView(badge, new LinearLayout.LayoutParams(dp(48), dp(48)));
        tile.addView(space(10));
        TextView heading = text(title, 15, INK, Typeface.BOLD);
        heading.setMaxLines(2);
        heading.setEllipsize(android.text.TextUtils.TruncateAt.END);
        tile.addView(heading);
        tile.setClickable(true);
        tile.setOnClickListener(v -> action.run());
        return tile;
    }

    private void addTopicGrid(LinearLayout root, String[] icons, int[] labels, Question.Type[] types) {
        for (int row = 0; row < 2; row++) {
            LinearLayout line = row();
            for (int col = 0; col < 2; col++) {
                int n = row * 2 + col;
                final Question.Type type = types[n];
                int title = labels[n];
                View tile = topicCard(icons[n], getString(title),
                        n % 2 == 0 ? RiftStyle.BLUE : RiftStyle.VIOLET,
                        () -> startTopic(type, getString(title)));
                LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                        0, dp(118), 1f);
                if (col == 1) lp.leftMargin = dp(10);
                line.addView(tile, lp);
            }
            LinearLayout.LayoutParams lp = matchWrap();
            lp.bottomMargin = dp(10);
            root.addView(line, lp);
        }
    }

    private void addKnowledgeTopicGrid(LinearLayout root) {
        List<String> ids = QuestionBank.knowledgeIds();
        int count = Math.min(8, ids.size());
        for (int start = 0; start < count; start += 2) {
            LinearLayout line = row();
            for (int i = start; i < Math.min(start + 2, count); i++) {
                final String id = ids.get(i);
                View tile = topicCard("◇",
                        QuestionBank.knowledgeLabel(id, Locale.getDefault()),
                        i % 2 == 0 ? RiftStyle.BLUE : RiftStyle.VIOLET,
                        () -> startKnowledgeTopic(id));
                LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, dp(118), 1f);
                if (i % 2 == 1) lp.leftMargin = dp(10);
                line.addView(tile, lp);
            }
            if (line.getChildCount() == 1) line.addView(new View(this),
                    new LinearLayout.LayoutParams(0, dp(118), 1f));
            LinearLayout.LayoutParams lp = matchWrap();
            lp.bottomMargin = dp(10);
            root.addView(line, lp);
        }
    }

    private void startTopic(Question.Type type,String title) {
        List<Question> questions=QuestionBank.byType(type);
        if(questions.isEmpty()) {
            new AlertDialog.Builder(this).setMessage(getString(R.string.topic_empty)).setPositiveButton(getString(R.string.got_it),null).show();
            return;
        }
        startSession(title,shuffled(questions,15));
    }

    private void startKnowledgeTopic(String knowledgeId) {
        List<Question> questions=new ArrayList<>();
        for(Question q:QuestionBank.all()) for(KnowledgeRef ref:q.knowledge) if(ref.id.equals(knowledgeId)){questions.add(q);break;}
        if(questions.isEmpty()) return;
        startSession(QuestionBank.knowledgeLabel(knowledgeId,Locale.getDefault()),shuffled(questions,15));
    }

    private String humanPackLabel(ContentPack pack) {
        boolean ru="ru".equals(Locale.getDefault().getLanguage());
        String subject;
        if("english".equals(pack.subject)) subject=ru?"Английский язык":"English";
        else if("informatics".equals(pack.subject)) subject=ru?"Информатика":"Informatics";
        else if("mathematics".equals(pack.subject)) subject=ru?"Математика":"Mathematics";
        else if("geography".equals(pack.subject)) subject=ru?"География":"Geography";
        else if("biology".equals(pack.subject)) subject=ru?"Биология":"Biology";
        else if("history".equals(pack.subject)) subject=ru?"История":"History";
        else if("social_science".equals(pack.subject)) subject=ru?"Обществознание":"Social Studies";
        else if("ecology".equals(pack.subject)) subject=ru?"Экология":"Ecology";
        else subject=pack.subject;
        String grades=pack.gradeMin==pack.gradeMax?String.valueOf(pack.gradeMin):(pack.gradeMin+"–"+pack.gradeMax);
        String region=pack.region;
        if(ru && "Tatarstan".equalsIgnoreCase(region)) region="Татарстан";
        if(ru && "Global".equalsIgnoreCase(region)) region="международный";
        return subject+" · "+grades+(ru?" класс":" grade")+(region.isEmpty()?"":" · "+region);
    }

    private String modeName(String mode) {
        if (MetaGameStore.DEFENSE.equals(mode)) return getString(R.string.mode_defense);
        if (MetaGameStore.HERO.equals(mode)) return getString(R.string.mode_hero);
        return getString(R.string.mode_pet);
    }

    private void showMyWorld() {
        homeVisible = false;
        LinearLayout root = column();
        root.setPadding(dp(20), dp(18), dp(20), dp(36));
        Button back = compactButton("←");
        back.setOnClickListener(v -> showHome());
        root.addView(back, new LinearLayout.LayoutParams(dp(52), dp(48)));
        root.addView(space(23));

        TextView kicker = text(getString(R.string.rift_world_kicker),
                12, PRIMARY, Typeface.BOLD);
        kicker.setLetterSpacing(.14f);
        root.addView(kicker);
        root.addView(space(7));
        root.addView(text(getString(R.string.my_world), 30, INK, Typeface.BOLD));
        root.addView(space(7));
        root.addView(text(getString(R.string.my_world_caption), 15, MUTED, Typeface.NORMAL));
        root.addView(space(18));

        LinearLayout stage = column();
        stage.setPadding(dp(20), dp(22), dp(20), dp(23));
        stage.setBackground(RiftStyle.cosmic(this, 24));
        RiftStyle.raise(stage, 5);
        TextView stageTitle = text("✦", 45, RiftStyle.CYAN, Typeface.BOLD);
        stage.addView(stageTitle);
        stage.addView(space(10));
        stage.addView(text(modeName(metaGame.preferredMode()), 25, Color.WHITE, Typeface.BOLD));
        stage.addView(space(8));
        stage.addView(text(getString(R.string.shop_balance_fmt, economy.balance()),
                15, Color.rgb(212, 225, 255), Typeface.BOLD));
        root.addView(stage, matchWrap());
        root.addView(space(22));
        root.addView(text(getString(R.string.rift_explore), 21, INK, Typeface.BOLD));
        root.addView(space(12));

        String mode = metaGame.preferredMode();
        if (MetaGameStore.DEFENSE.equals(mode)) {
            addWorldItems(root, mode, new String[]{"barrier", "sensor", "defense_module"},
                    new int[]{25, 60, 140});
            root.addView(text(getString(R.string.game_prototype_notice),
                    13, MUTED, Typeface.NORMAL));
        } else if (MetaGameStore.HERO.equals(mode))
            addWorldItems(root, mode, new String[]{"outfit", "gear", "ability"},
                    new int[]{20, 55, 130});
        else addWorldItems(root, mode, new String[]{"collar", "toy", "room"},
                    new int[]{20, 45, 120});
        setScrollable(root);
    }

    private void addWorldItems(LinearLayout root, String mode, String[] ids, int[] prices) {
        for (int i = 0; i < ids.length; i++) {
            final String id = ids[i];
            final int price = prices[i];
            LinearLayout card = column();
            card.setPadding(dp(16), dp(16), dp(16), dp(16));
            card.setBackground(RiftStyle.shape(this, Color.WHITE, 20, 1, SOFT));
            RiftStyle.raise(card, 2);
            LinearLayout heading = row();
            TextView badge = text(i == 0 ? "◇" : i == 1 ? "✦" : "◈",
                    26, i == 1 ? RiftStyle.VIOLET : RiftStyle.BLUE, Typeface.BOLD);
            badge.setGravity(Gravity.CENTER);
            badge.setBackground(RiftStyle.shape(this, Color.rgb(237, 240, 255),
                    16, 0, Color.TRANSPARENT));
            heading.addView(badge, new LinearLayout.LayoutParams(dp(52), dp(52)));
            LinearLayout info = column();
            info.setPadding(dp(13), 0, 0, 0);
            info.addView(text(getString(getResources().getIdentifier(
                    "meta_" + id, "string", getPackageName())), 18, INK, Typeface.BOLD));
            info.addView(space(5));
            info.addView(text(getString(R.string.meta_level,
                    metaGame.level(mode, id)), 13, MUTED, Typeface.NORMAL));
            heading.addView(info);
            card.addView(heading);
            card.addView(space(14));
            Button buy = secondaryButton(getString(R.string.meta_upgrade, price));
            buy.setOnClickListener(v -> {
                if (metaGame.buyLevel(mode, id, price)) showMyWorld();
                else new AlertDialog.Builder(this)
                        .setMessage(getString(R.string.shop_not_enough))
                        .setPositiveButton(getString(R.string.got_it), null).show();
            });
            card.addView(buy, matchWrap());
            LinearLayout.LayoutParams lp = matchWrap();
            lp.bottomMargin = dp(11);
            root.addView(card, lp);
        }
    }

    private View progressCard() {
        LinearLayout card = column();
        card.setPadding(dp(18), dp(17), dp(18), dp(18));
        card.setBackground(RiftStyle.shape(this, Color.WHITE, 21, 1, SOFT));
        RiftStyle.raise(card, 2);

        LinearLayout top = row();
        LinearLayout main = column();
        TextView heading = text(getString(R.string.rift_your_progress), 12, MUTED, Typeface.BOLD);
        heading.setLetterSpacing(.08f);
        main.addView(heading);
        main.addView(space(6));
        main.addView(text(getString(R.string.level_fmt, progress.level()), 24, INK, Typeface.BOLD));
        top.addView(main, new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        top.addView(RiftStyle.pill(this, progress.xpInLevel() + " / 350 XP",
                PRIMARY, Color.rgb(235, 234, 255)));
        card.addView(top);

        ProgressBar bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        bar.setMax(350);
        bar.setProgress(progress.xpInLevel());
        bar.setProgressTintList(android.content.res.ColorStateList.valueOf(PRIMARY));
        bar.setProgressBackgroundTintList(android.content.res.ColorStateList.valueOf(SOFT));
        LinearLayout.LayoutParams bp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(8));
        bp.topMargin = dp(15);
        card.addView(bar, bp);
        card.addView(space(15));

        LinearLayout chips = row();
        chips.addView(RiftStyle.pill(this, "◇  " + getString(R.string.crystals_fmt, economy.balance()),
                RiftStyle.BLUE, Color.rgb(239, 241, 255)));
        chips.addView(spaceHorizontal(8));
        chips.addView(RiftStyle.pill(this, "✦  " + getString(R.string.play_credits_fmt, playCredits.balance()),
                RiftStyle.VIOLET, Color.rgb(246, 239, 255)));
        card.addView(chips);
        return card;
    }

    private View activityCard() {
        LinearLayout card = column();
        card.setPadding(dp(16), dp(13), dp(16), dp(13));
        card.setBackground(roundRect(CARD, 16, 1, SOFT));
        card.addView(text(getString(R.string.activity_week), 13, MUTED, Typeface.BOLD));
        LinearLayout strip = row();
        Calendar calendar = Calendar.getInstance();
        List<ActivityStore.Day> days = activity.recentDays(7);
        for (ActivityStore.Day day : days) {
            TextView marker = text(day.date.substring(8) + (day.active() ? "  ✓" : "  ·"),
                    13, day.active() ? GOOD : MUTED, Typeface.BOLD);
            marker.setGravity(Gravity.CENTER);
            strip.addView(marker, new LinearLayout.LayoutParams(0, dp(38), 1f));
        }
        card.addView(strip);
        card.setClickable(true);
        card.setOnClickListener(v -> showActivityMonth());
        return card;
    }

    private View nextFocusCard() {
        LinearLayout card = column();
        card.setPadding(dp(16), dp(13), dp(16), dp(13));
        card.setBackground(roundRect(Color.rgb(232, 237, 255), 16, 0, Color.TRANSPARENT));
        card.addView(text(getString(R.string.next_focus), 13, PRIMARY, Typeface.BOLD));
        List<String> focus = QuestionBank.recommendedKnowledge(progress, 3);
        for (String id : focus) {
            TextView line = text("• " + QuestionBank.knowledgeLabel(id, Locale.getDefault()),
                    15, INK, Typeface.NORMAL);
            line.setPadding(0, dp(4), 0, 0);
            card.addView(line);
        }
        return card;
    }

    private void showActivityMonth() {
        List<ActivityStore.Day> days = activity.currentMonth();
        int answered = 0, correct = 0, xp = 0, crystals = 0, sessions = 0, active = 0;
        for (ActivityStore.Day day : days) {
            answered += day.answered; correct += day.correct; xp += day.xp;
            crystals += day.crystals; sessions += day.sessions;
            if (day.active()) active++;
        }
        String message = getString(R.string.activity_month_summary,
                active, answered, correct, xp, crystals, sessions);
        new AlertDialog.Builder(this)
                .setTitle(getString(R.string.activity_month))
                .setMessage(message)
                .setPositiveButton(getString(R.string.got_it), null)
                .show();
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
        reinforcementKnowledge.clear();
        reinforcementQuestionIds.clear();
        sessionBestBefore = progress.bestCombo();
        newRecordCelebrated = false;
        sessionAnswered = 0;
        showQuestion();
    }

    private void showQuestion() {
        questionShownAtMs = System.currentTimeMillis();
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
        enableDictionaryLinks(prompt, q.prompt);
        root.addView(prompt);

        TextView contextView = null;
        if (!q.context.isEmpty()) {
            contextView = text(q.context, 17, INK, Typeface.NORMAL);
            contextView.setLineSpacing(dp(4), 1.05f);
            enableDictionaryLinks(contextView, q.context);
            contextView.setPadding(dp(16), dp(14), dp(16), dp(14));
            contextView.setBackground(roundRect(Color.rgb(238, 241, 247), 14, 0, Color.TRANSPARENT));
            LinearLayout.LayoutParams clp = matchWrap();
            clp.topMargin = dp(16);
            root.addView(contextView, clp);
        }
        final TextView contextForAnswer = contextView;

        int[] listensLeft = {2};
        Button listeningAction = null;
        if (q.type == Question.Type.LISTENING) {
            Button play = primaryButton(getString(R.string.listen_first));
            play.setMinHeight(dp(72));
            play.setOnClickListener(v -> {
                if (listensLeft[0] <= 0) return;
                audio.play(q);
                listensLeft[0]--;
                play.setText(listensLeft[0] > 0
                        ? getString(R.string.listen_again_fmt, listensLeft[0])
                        : getString(R.string.listens_used));
                if (listensLeft[0] == 0) play.setEnabled(false);
            });
            listeningAction = play;
        }
        root.addView(space(18));

        List<Button> answerButtons = new ArrayList<>();
        if ("numeric".equals(q.interaction) || "free_response".equals(q.interaction)) {
            EditText input = new EditText(this);
            input.setHint(getString("numeric".equals(q.interaction) ? R.string.numeric_answer_hint : R.string.short_answer_hint));
            input.setTextSize(22);
            input.setSingleLine(true);
            input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
            input.setPadding(dp(16), dp(12), dp(16), dp(12));
            input.setBackground(roundRect(CARD, 14, 1, SOFT));
            root.addView(input, matchWrap());

            Button submit = primaryButton(getString(R.string.submit_answer));
            LinearLayout.LayoutParams submitLp = matchWrap();
            submitLp.topMargin = dp(10);
            root.addView(submit, submitLp);
            submit.setOnClickListener(v -> {
                boolean correct = q.acceptsText(input.getText().toString());
                input.setEnabled(false);
                submit.setEnabled(false);
                handleAnswerResult(root, q, correct, -1,
                        Collections.emptyList(), contextForAnswer);
            });
        } else if ("matching".equals(q.interaction)) {
            root.addView(text(getString(R.string.matching_hint), 13, MUTED, Typeface.BOLD));

            final int matchedBackground = Color.rgb(238, 240, 244);
            final int poolBackground = Color.rgb(246, 247, 250);
            List<Integer> assigned = new ArrayList<>();
            for (int i = 0; i < q.matchingLeft.size(); i++) assigned.add(-1);
            List<Button> leftButtons = new ArrayList<>();
            List<Button> rightButtons = new ArrayList<>();
            int[] selectedLeft = {-1};
            Button[] submitRef = {null};
            final String matchingAlphabet = "ru".equals(Locale.getDefault().getLanguage())
                    ? "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ"
                    : "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

            LinearLayout leftPool = column();
            leftPool.setPadding(dp(10), dp(10), dp(10), dp(6));
            leftPool.setBackground(roundRect(poolBackground, 14, 1, SOFT));
            leftPool.addView(text(getString(R.string.matching_left_pool), 12, MUTED, Typeface.BOLD));

            for (int i = 0; i < q.matchingLeft.size(); i++) {
                final int leftIndex = i;
                Button left = answerButton((leftIndex + 1) + ".  " + q.matchingLeft.get(i));
                LinearLayout.LayoutParams lp = matchWrap();
                lp.topMargin = dp(6);
                leftPool.addView(left, lp);
                leftButtons.add(left);
                answerButtons.add(left);
                left.setOnClickListener(v -> {
                    int previousRight = assigned.get(leftIndex);
                    if (previousRight >= 0) {
                        assigned.set(leftIndex, -1);
                        Button released = rightButtons.get(previousRight);
                        released.setEnabled(true);
                        released.setAlpha(1f);
                        released.setBackground(roundRect(CARD, 14, 1, SOFT));
                        released.setText(String.valueOf(matchingAlphabet.charAt(previousRight % matchingAlphabet.length())) + ".  " + q.matchingRight.get(previousRight));
                        left.setText((leftIndex + 1) + ".  " + q.matchingLeft.get(leftIndex));
                    }

                    selectedLeft[0] = leftIndex;
                    for (int j = 0; j < leftButtons.size(); j++) {
                        Button candidate = leftButtons.get(j);
                        if (j == leftIndex) {
                            candidate.setAlpha(1f);
                            candidate.setBackground(roundRect(Color.rgb(225, 232, 255), 14, 2, PRIMARY));
                        } else if (assigned.get(j) >= 0) {
                            candidate.setAlpha(0.72f);
                            candidate.setBackground(roundRect(matchedBackground, 14, 1, SOFT));
                        } else {
                            candidate.setAlpha(1f);
                            candidate.setBackground(roundRect(CARD, 14, 1, SOFT));
                        }
                    }
                    if (submitRef[0] != null) submitRef[0].setEnabled(false);
                });
            }
            root.addView(leftPool, matchWrap());

            root.addView(space(10));

            LinearLayout rightPool = column();
            rightPool.setPadding(dp(10), dp(10), dp(10), dp(6));
            rightPool.setBackground(roundRect(poolBackground, 14, 1, SOFT));
            rightPool.addView(text(getString(R.string.matching_right_pool), 12, MUTED, Typeface.BOLD));

            for (int i = 0; i < q.matchingRight.size(); i++) {
                final int rightIndex = i;
                Button right = secondaryButton(String.valueOf(matchingAlphabet.charAt(rightIndex % matchingAlphabet.length())) + ".  " + q.matchingRight.get(i));
                LinearLayout.LayoutParams lp = matchWrap();
                lp.topMargin = dp(6);
                rightPool.addView(right, lp);
                rightButtons.add(right);
                answerButtons.add(right);
                right.setOnClickListener(v -> {
                    int leftIndex = selectedLeft[0];
                    if (leftIndex < 0 || assigned.contains(rightIndex)) return;

                    assigned.set(leftIndex, rightIndex);
                    Button left = leftButtons.get(leftIndex);
                    left.setText((leftIndex + 1) + ".  " + q.matchingLeft.get(leftIndex)
                            + "\n→ " + String.valueOf(matchingAlphabet.charAt(rightIndex % matchingAlphabet.length())));
                    left.setAlpha(0.72f);
                    left.setBackground(roundRect(matchedBackground, 14, 1, SOFT));

                    right.setText(String.valueOf(matchingAlphabet.charAt(rightIndex % matchingAlphabet.length())) + ".  " + q.matchingRight.get(rightIndex)
                            + "   ✓");
                    right.setEnabled(false);
                    right.setAlpha(0.48f);
                    right.setBackground(roundRect(matchedBackground, 14, 1, SOFT));

                    selectedLeft[0] = -1;
                    if (submitRef[0] != null) submitRef[0].setEnabled(!assigned.contains(-1));
                });
            }
            root.addView(rightPool, matchWrap());

            root.addView(space(8));
            Button reset = secondaryButton(getString(R.string.matching_reset));
            root.addView(reset, matchWrap());
            reset.setOnClickListener(v -> {
                selectedLeft[0] = -1;
                for (int i = 0; i < assigned.size(); i++) {
                    assigned.set(i, -1);
                    Button left = leftButtons.get(i);
                    left.setText((i + 1) + ".  " + q.matchingLeft.get(i));
                    left.setEnabled(true);
                    left.setAlpha(1f);
                    left.setBackground(roundRect(CARD, 14, 1, SOFT));
                }
                for (int i = 0; i < rightButtons.size(); i++) {
                    Button right = rightButtons.get(i);
                    right.setText(String.valueOf(matchingAlphabet.charAt(i % matchingAlphabet.length())) + ".  " + q.matchingRight.get(i));
                    right.setEnabled(true);
                    right.setAlpha(1f);
                    right.setBackground(roundRect(CARD, 14, 1, SOFT));
                }
                if (submitRef[0] != null) submitRef[0].setEnabled(false);
            });

            Button submit = primaryButton(getString(R.string.submit_answer));
            submitRef[0] = submit;
            submit.setEnabled(false);
            LinearLayout.LayoutParams submitLp = matchWrap();
            submitLp.topMargin = dp(8);
            root.addView(submit, submitLp);
            submit.setOnClickListener(v -> {
                reset.setEnabled(false);
                submit.setEnabled(false);
                for (Button button : answerButtons) button.setEnabled(false);
                boolean correct = q.acceptsMatching(assigned);
                for (Button button : leftButtons) {
                    button.setAlpha(1f);
                    button.setBackground(roundRect(correct ? Color.rgb(221, 245, 234) : Color.rgb(255, 244, 215),
                            14, 2, correct ? GOOD : Color.rgb(210, 160, 60)));
                }
                handleAnswerResult(root, q, correct, -1, Collections.emptyList(), contextForAnswer);
            });
        } else if ("multi_choice".equals(q.interaction)) {
            TextView hint = text(getString(R.string.multi_choice_hint), 13, MUTED, Typeface.BOLD);
            hint.setPadding(0, 0, 0, dp(8));
            root.addView(hint);
            Set<Integer> selected = new HashSet<>();
            for (int i = 0; i < q.options.size(); i++) {
                final int answerIndex = i;
                Button button = answerButton(q.options.get(i));
                LinearLayout.LayoutParams blp = matchWrap();
                blp.bottomMargin = dp(10);
                root.addView(button, blp);
                answerButtons.add(button);
                button.setOnClickListener(v -> {
                    if (selected.contains(answerIndex)) {
                        selected.remove(answerIndex);
                        button.setBackground(roundRect(CARD, 14, 1, SOFT));
                    } else {
                        selected.add(answerIndex);
                        button.setBackground(roundRect(Color.rgb(225, 232, 255), 14, 2, PRIMARY));
                    }
                });
            }
            Button submit = primaryButton(getString(R.string.submit_answer));
            root.addView(submit, matchWrap());
            submit.setOnClickListener(v -> {
                submit.setEnabled(false);
                for (Button button : answerButtons) button.setEnabled(false);
                handleAnswerResult(root, q, q.acceptsIndices(selected), -1,
                        answerButtons, contextForAnswer);
            });
        } else if ("sequence".equals(q.interaction)) {
            root.addView(text(getString(R.string.sequence_hint), 13, MUTED, Typeface.BOLD));
            List<Integer> ordered = new ArrayList<>();
            for (int i = 0; i < q.options.size(); i++) {
                final int answerIndex = i;
                Button button = answerButton(q.options.get(i));
                LinearLayout.LayoutParams blp = matchWrap();
                blp.bottomMargin = dp(10);
                root.addView(button, blp);
                answerButtons.add(button);
                button.setOnClickListener(v -> {
                    if (ordered.contains(answerIndex)) return;
                    ordered.add(answerIndex);
                    button.setText(ordered.size() + ".  " + q.options.get(answerIndex));
                    button.setBackground(roundRect(Color.rgb(225, 232, 255), 14, 2, PRIMARY));
                });
            }
            Button reset = secondaryButton(getString(R.string.sequence_reset));
            root.addView(reset, matchWrap());
            reset.setOnClickListener(v -> {
                ordered.clear();
                for (int i = 0; i < answerButtons.size(); i++) {
                    answerButtons.get(i).setText(q.options.get(i));
                    answerButtons.get(i).setBackground(roundRect(CARD, 14, 1, SOFT));
                }
            });
            Button submit = primaryButton(getString(R.string.submit_answer));
            LinearLayout.LayoutParams submitLp = matchWrap();
            submitLp.topMargin = dp(8);
            root.addView(submit, submitLp);
            submit.setOnClickListener(v -> {
                reset.setEnabled(false);
                submit.setEnabled(false);
                handleAnswerResult(root, q, q.acceptsSequence(ordered), -1,
                        answerButtons, contextForAnswer);
            });
        } else {
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
        }

        TextView footer = text("XP " + progress.xp() + "   ·   " + getString(R.string.crystals_fmt, economy.balance())
                        + "   ·   combo ×" + progress.combo(),
                13, MUTED, Typeface.BOLD);
        footer.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams flp = matchWrap();
        flp.topMargin = dp(8);
        root.addView(footer, flp);

        if (listeningAction != null) {
            setQuestionScrollable(root, listeningAction);
        } else {
            setScrollable(root);
        }
    }

    private void handleAnswer(LinearLayout root, Question q, int chosen,
                              List<Button> buttons, TextView contextView) {
        handleAnswerResult(root, q, q.isCorrect(chosen), chosen, buttons, contextView);
    }

    private void handleAnswerResult(LinearLayout root, Question q, boolean correct, int chosen,
                                    List<Button> buttons, TextView contextView) {
        boolean reinforcement = reinforcementQuestionIds.remove(q.id);
        ProgressStore.SkillState beforeState = progress.state(q.primaryKnowledgeId());
        int xpBefore = progress.xp();
        progress.record(q, correct);
        learningEvents.record(q, correct, Math.max(0L, System.currentTimeMillis() - questionShownAtMs),
                QuestionBank.currentPack().id);
        ProgressStore.SkillState afterState = progress.state(q.primaryKnowledgeId());
        boolean becameConfident = beforeState != ProgressStore.SkillState.CONFIDENT
                && afterState == ProgressStore.SkillState.CONFIDENT;
        sessionAnswered++;
        boolean playCreditEarned = playCredits.awardForLearningProgress(sessionAnswered);

        boolean reinforcementScheduled = !correct && scheduleReinforcement(q);
        RewardFx.Reaction reaction = rewards.reaction(correct, progress.combo());

        boolean newRecord = correct
                && !newRecordCelebrated
                && progress.combo() >= 3
                && progress.combo() > sessionBestBefore;
        if (newRecord) {
            newRecordCelebrated = true;
            rewards.playNewRecord(progress.combo());
        } else {
            rewards.play(reaction, correct, progress.combo());
        }
        if (correct) sessionCorrect++;

        int crystalGain = economy.awardLearning(
                correct,
                progress.combo(),
                newRecord,
                becameConfident,
                reinforcement && correct,
                sessionAnswered,
                q.id
        );
        activity.recordAnswer(correct, progress.xp() - xpBefore, crystalGain,
                progress.combo(), QuestionBank.currentPack().id);

        int[] stats = sessionStats.computeIfAbsent(q.skill, k -> new int[]{0, 0});
        stats[0]++;
        if (correct) stats[1]++;

        for (int i = 0; i < buttons.size(); i++) {
            Button b = buttons.get(i);
            b.setEnabled(false);
            if (i == q.correctIndex || (("multi_choice".equals(q.interaction) || "sequence".equals(q.interaction))
                    && q.correctIndices.contains(i))) {
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

        if (crystalGain > 0) {
            TextView crystals = text(getString(R.string.crystals_gain_fmt, crystalGain), 16, PRIMARY, Typeface.BOLD);
            crystals.setPadding(0, dp(7), 0, 0);
            feedback.addView(crystals);
        }

        if (playCreditEarned) {
            TextView credit = text(getString(R.string.play_credit_earned), 15, PRIMARY, Typeface.BOLD);
            credit.setPadding(0, dp(7), 0, 0);
            feedback.addView(credit);
        }

        if (reinforcementScheduled) {
            TextView repair = text(getString(R.string.reinforcement_scheduled), 14, PRIMARY, Typeface.BOLD);
            repair.setPadding(0, dp(8), 0, 0);
            feedback.addView(repair);
        }

        if (reinforcement && correct) {
            TextView reinforced = text(getString(R.string.reinforced), 15, GOOD, Typeface.BOLD);
            reinforced.setPadding(0, dp(8), 0, 0);
            feedback.addView(reinforced);
        }

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
            boolean hasMore = questionIndex + 1 < session.size();
            questionIndex++;
            boolean miniGamesEnabled = getSharedPreferences("english_sprint_settings", MODE_PRIVATE)
                    .getBoolean("minigames", true);
            if (miniGamesEnabled
                    && miniGames.shouldOfferBreak(sessionAnswered, hasMore)
                    && playCredits.consumeGameSession()) {
                miniGames.startBreak(this, this::showQuestion);
            } else {
                showQuestion();
            }
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

    private boolean scheduleReinforcement(Question wrong) {
        String knowledgeId = wrong.primaryKnowledgeId();
        if (knowledgeId == null || knowledgeId.isEmpty() || reinforcementKnowledge.contains(knowledgeId)) {
            return false;
        }

        int target = questionIndex + 3 + sessionRandom.nextInt(3);
        if (target >= session.size()) return false;

        Set<String> usedIds = new HashSet<>();
        for (Question q : session) usedIds.add(q.id);

        List<Question> candidates = new ArrayList<>();
        for (Question q : QuestionBank.all()) {
            if (q.id.equals(wrong.id)) continue;
            if (usedIds.contains(q.id)) continue;
            if (knowledgeId.equals(q.primaryKnowledgeId())) candidates.add(q);
        }
        if (candidates.isEmpty()) return false;

        Collections.shuffle(candidates, sessionRandom);
        Question repair = candidates.get(0);
        session.set(target, repair);
        reinforcementKnowledge.add(knowledgeId);
        reinforcementQuestionIds.add(repair.id);
        return true;
    }

    private void showSessionResult() {
        audio.stop();
        activity.recordSessionCompleted();
        LinearLayout root = column();
        root.setPadding(dp(20), dp(24), dp(20), dp(36));
        int percent = session.isEmpty() ? 0 :
                Math.round(sessionCorrect * 100f / session.size());

        TextView eyebrow = text(getString(R.string.rift_result_kicker),
                12, PRIMARY, Typeface.BOLD);
        eyebrow.setLetterSpacing(.14f);
        root.addView(eyebrow);
        root.addView(space(9));
        root.addView(text(sessionTitle, 28, INK, Typeface.BOLD));
        root.addView(space(16));

        LinearLayout result = column();
        result.setGravity(Gravity.CENTER_HORIZONTAL);
        result.setPadding(dp(18), dp(24), dp(18), dp(24));
        result.setBackground(RiftStyle.shape(this, Color.WHITE, 25, 1, SOFT));
        RiftStyle.raise(result, 4);
        RiftStyle.ScoreRing ring = new RiftStyle.ScoreRing(this, percent);
        result.addView(ring, new LinearLayout.LayoutParams(dp(166), dp(166)));
        result.addView(space(6));
        result.addView(text(sessionCorrect + " / " + session.size(),
                23, INK, Typeface.BOLD));
        result.addView(space(5));
        result.addView(text(getString(R.string.rift_milestone), 14, MUTED, Typeface.NORMAL));
        root.addView(result, matchWrap());

        root.addView(space(24));
        root.addView(sectionHeading(getString(R.string.what_next),
                getString(R.string.rift_atlas_caption)));
        root.addView(space(12));

        List<Map.Entry<String, int[]>> entries = new ArrayList<>(sessionStats.entrySet());
        entries.sort(Comparator.comparingDouble(e -> {
            int[] scores = e.getValue();
            return scores[0] == 0 ? 1.0 : (double) scores[1] / scores[0];
        }));
        int shown = 0;
        for (Map.Entry<String, int[]> entry : entries) {
            if (shown++ >= 4) break;
            ProgressStore.SkillState state = progress.state(entry.getKey());
            LinearLayout line = row();
            line.setPadding(dp(15), dp(14), dp(15), dp(14));
            line.setBackground(RiftStyle.shape(this, Color.WHITE, 16, 1, SOFT));
            TextView dot = text("◆", 15, state == ProgressStore.SkillState.CONFIDENT
                    ? GOOD : PRIMARY, Typeface.BOLD);
            line.addView(dot);
            TextView name = text(skillName(entry.getKey()), 15, INK, Typeface.BOLD);
            name.setPadding(dp(10), 0, dp(8), 0);
            line.addView(name, new LinearLayout.LayoutParams(0,
                    ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
            TextView stage = text(skillStateLabel(state), 12, MUTED, Typeface.NORMAL);
            line.addView(stage);
            LinearLayout.LayoutParams lp = matchWrap();
            lp.bottomMargin = dp(9);
            root.addView(line, lp);
        }
        root.addView(space(18));
        Button again = primaryButton(getString(R.string.another_quick) + "  →");
        again.setOnClickListener(v -> startSession(
                getString(R.string.quick_training), quickSession()));
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
        root.setPadding(dp(18), dp(18), dp(18), dp(36));
        Button back = compactButton("←");
        back.setOnClickListener(v -> showHome());
        root.addView(back, new LinearLayout.LayoutParams(dp(52), dp(48)));
        root.addView(space(23));
        TextView kicker = text(getString(R.string.rift_atlas_kicker), 12, PRIMARY, Typeface.BOLD);
        kicker.setLetterSpacing(.14f);
        root.addView(kicker);
        root.addView(space(6));
        root.addView(text(getString(R.string.rift_paths), 30, INK, Typeface.BOLD));
        TextView description = text(getString(R.string.rift_nodes_hint), 15, MUTED, Typeface.NORMAL);
        description.setPadding(0, dp(8), 0, 0);
        root.addView(description);
        root.addView(space(18));

        LinearLayout summary = row();
        summary.setPadding(dp(16), dp(15), dp(16), dp(15));
        summary.setBackground(RiftStyle.shape(this, Color.WHITE, 18, 1, SOFT));
        List<String> skills = new ArrayList<>(QuestionBank.knowledgeIds());
        int mastered = 0;
        for (String id : skills)
            if (progress.state(id) == ProgressStore.SkillState.CONFIDENT) mastered++;
        summary.addView(text(mastered + " / " + skills.size(), 25, PRIMARY, Typeface.BOLD));
        TextView note = text("  " + getString(R.string.rift_mastered), 14, MUTED, Typeface.NORMAL);
        summary.addView(note);
        root.addView(summary);

        skills.sort((a, b) -> {
            int deps = Integer.compare(QuestionBank.prerequisitesForKnowledge(a).size(),
                    QuestionBank.prerequisitesForKnowledge(b).size());
            return deps != 0 ? deps : a.compareTo(b);
        });
        List<String> names = new ArrayList<>();
        List<Integer> statuses = new ArrayList<>();
        for (String id : skills) {
            names.add(QuestionBank.knowledgeLabel(id, Locale.getDefault()));
            ProgressStore.SkillState state = progress.state(id);
            statuses.add(state == ProgressStore.SkillState.CONFIDENT ? 3 :
                    state == ProgressStore.SkillState.GROWING ? 2 :
                    state == ProgressStore.SkillState.LEARNING ? 1 : 0);
        }
        RiftStyle.KnowledgeMap atlas = new RiftStyle.KnowledgeMap(this, skills, names, statuses,
                QuestionBank.knowledgeRelations(), id -> {
            List<String> prereqs = QuestionBank.prerequisitesForKnowledge(id);
            StringBuilder details = new StringBuilder(skillStateLabel(progress.state(id)));
            details.append("\n\n").append(getString(R.string.rift_node_prereqs)).append(":\n");
            if (prereqs.isEmpty()) details.append(getString(R.string.rift_no_prereqs));
            else for (String pre : prereqs)
                details.append("• ").append(QuestionBank.knowledgeLabel(pre, Locale.getDefault())).append("\n");
            new AlertDialog.Builder(this)
                    .setTitle(QuestionBank.knowledgeLabel(id, Locale.getDefault()))
                    .setMessage(details.toString().trim())
                    .setPositiveButton(getString(R.string.learn_now), (d, w) -> startKnowledgeTopic(id))
                    .setNegativeButton(getString(R.string.dictionary_close), null)
                    .show();
        });
        root.addView(atlas, matchWrap());
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

        TextView assessedTitle = text(getString(R.string.knowledge_assessed), 12, MUTED, Typeface.BOLD);
        assessedTitle.setPadding(0, dp(14), 0, dp(5));
        box.addView(assessedTitle);
        List<String> assessedLabels = new ArrayList<>();
        for (KnowledgeRef ref : q.knowledge) {
            assessedLabels.add(QuestionBank.knowledgeLabel(ref.id, Locale.getDefault()));
        }
        box.addView(text(String.join(" · ", assessedLabels), 15, INK, Typeface.NORMAL));

        TextView prerequisiteTitle = text(getString(R.string.knowledge_prerequisites), 12, MUTED, Typeface.BOLD);
        prerequisiteTitle.setPadding(0, dp(14), 0, dp(5));
        box.addView(prerequisiteTitle);
        List<String> prerequisiteLabels = new ArrayList<>();
        for (String id : q.prerequisites) {
            prerequisiteLabels.add(QuestionBank.knowledgeLabel(id, Locale.getDefault()));
        }
        box.addView(text(prerequisiteLabels.isEmpty()
                ? getString(R.string.knowledge_none)
                : String.join(" · ", prerequisiteLabels), 15, INK, Typeface.NORMAL));

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

    private List<Question> quickSession() {
        long seed = System.nanoTime();
        android.content.SharedPreferences prefs = getSharedPreferences("english_sprint_session_history", MODE_PRIVATE);
        java.util.Set<String> recent = new java.util.HashSet<>(prefs.getStringSet("recent_question_ids", java.util.Collections.emptySet()));

        List<Question> candidates = QuestionBank.adaptiveSession(progress, 75, seed);
        List<Question> fresh = new ArrayList<>();
        for (Question q : candidates) {
            if (!recent.contains(q.id)) fresh.add(q);
            if (fresh.size() >= 15) break;
        }
        if (fresh.size() < 15) {
            recent.clear();
            fresh.clear();
            for (Question q : candidates) {
                fresh.add(q);
                if (fresh.size() >= 15) break;
            }
        }

        List<Question> mixed = dictionary.mixVocabulary(fresh, 2, seed + 17);
        if (mixed.size() > 15) mixed = new ArrayList<>(mixed.subList(0, 15));

        for (Question q : mixed) recent.add(q.id);
        if (recent.size() > 90) {
            recent.clear();
            for (Question q : mixed) recent.add(q.id);
        }
        prefs.edit().putStringSet("recent_question_ids", recent).apply();
        return mixed;
    }

    private void enableDictionaryLinks(TextView view, String source) {
        if (source == null || source.isEmpty()) return;
        if (!"english".equals(QuestionBank.currentPack().subject)) return;

        SpannableString span = new SpannableString(source);
        Matcher matcher = Pattern.compile("[A-Za-z][A-Za-z'’-]*").matcher(source);
        boolean hasWords = false;

        while (matcher.find()) {
            final int start = matcher.start();
            final int end = matcher.end();
            final String token = matcher.group();
            hasWords = true;

            span.setSpan(new ClickableSpan() {
                @Override
                public void onClick(View widget) {
                    lookupDictionaryWord(view, source, start, end, token);
                }

                @Override
                public void updateDrawState(TextPaint ds) {
                    ds.setColor(INK);
                    ds.setUnderlineText(false);
                }
            }, start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        }

        view.setText(span);
        if (hasWords) {
            view.setMovementMethod(LinkMovementMethod.getInstance());
            view.setHighlightColor(Color.TRANSPARENT);
        }
    }

    private void lookupDictionaryWord(TextView view, String source, int start, int end, String token) {
        SpannableString highlighted = new SpannableString(source);
        highlighted.setSpan(new BackgroundColorSpan(HIGHLIGHT), start, end,
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        view.setText(highlighted);

        ProgressDialog loading = ProgressDialog.show(
                this, null, getString(R.string.dictionary_loading, token), true, false);

        dictionaryRepository.lookup(token, (entry, fromNetwork, error) -> {
            loading.dismiss();

            if (entry != null) {
                dictionary.save(entry);
                showDictionaryEntry(entry, () -> enableDictionaryLinks(view, source));
                return;
            }

            new AlertDialog.Builder(this)
                    .setTitle(token)
                    .setMessage(getString(R.string.dictionary_unavailable))
                    .setPositiveButton(getString(R.string.got_it), null)
                    .setOnDismissListener(dialog -> enableDictionaryLinks(view, source))
                    .show();
        });
    }

    private void showDictionaryEntry(DictionaryEntry entry) {
        showDictionaryEntry(entry, null);
    }

    private void showDictionaryEntry(DictionaryEntry entry, Runnable onDismiss) {
        LinearLayout box = column();
        box.setPadding(dp(22), dp(18), dp(22), dp(10));

        TextView word = text(entry.lemma, 28, INK, Typeface.BOLD);
        box.addView(word);

        if (!entry.phonetic.isEmpty()) {
            TextView phonetic = text(entry.phonetic, 16, MUTED, Typeface.NORMAL);
            phonetic.setPadding(0, dp(3), 0, dp(12));
            box.addView(phonetic);
        }

        TextView translation = text(entry.translation(Locale.getDefault()), 21, PRIMARY, Typeface.BOLD);
        box.addView(translation);

        TextView definitionTitle = text(getString(R.string.dictionary_definition), 12, MUTED, Typeface.BOLD);
        definitionTitle.setPadding(0, dp(16), 0, dp(4));
        box.addView(definitionTitle);
        TextView definition = text(entry.definition(Locale.getDefault()), 17, INK, Typeface.NORMAL);
        definition.setLineSpacing(dp(4), 1.05f);
        box.addView(definition);

        if (!entry.example.isEmpty()) {
            TextView exampleTitle = text(getString(R.string.dictionary_example), 12, MUTED, Typeface.BOLD);
            exampleTitle.setPadding(0, dp(16), 0, dp(4));
            box.addView(exampleTitle);
            TextView example = text(entry.example, 16, INK, Typeface.ITALIC);
            example.setLineSpacing(dp(3), 1.04f);
            box.addView(example);
        }

        boolean saved = dictionary.isSaved(entry);
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setView(box)
                .setPositiveButton(saved ? getString(R.string.dictionary_remove) : getString(R.string.dictionary_add),
                        (d, which) -> {
                            if (saved) dictionary.remove(entry); else dictionary.save(entry);
                        })
                .setNegativeButton(getString(R.string.dictionary_close), null)
                .create();
        if (onDismiss != null) dialog.setOnDismissListener(d -> onDismiss.run());
        dialog.show();
    }

    private void showDictionary() {
        LinearLayout root = column();
        root.setPadding(dp(20), dp(20), dp(20), dp(28));

        Button back = compactButton("←");
        back.setOnClickListener(v -> showHome());
        root.addView(back, new LinearLayout.LayoutParams(dp(52), dp(44)));
        root.addView(space(14));
        root.addView(text(getString(R.string.dictionary_title), 28, INK, Typeface.BOLD));
        root.addView(space(14));

        List<DictionaryEntry> saved = dictionary.savedEntries();
        if (saved.isEmpty()) {
            TextView empty = text(getString(R.string.dictionary_empty), 16, MUTED, Typeface.NORMAL);
            empty.setLineSpacing(dp(4), 1.05f);
            root.addView(empty);
        } else {
            for (DictionaryEntry entry : saved) {
                LinearLayout card = column();
                card.setPadding(dp(16), dp(13), dp(16), dp(13));
                card.setBackground(roundRect(CARD, 14, 1, SOFT));
                card.setOnClickListener(v -> showDictionaryEntry(entry));
                card.setClickable(true);

                LinearLayout row = row();
                row.addView(text(entry.lemma, 18, INK, Typeface.BOLD),
                        new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
                row.addView(text(entry.phonetic, 14, MUTED, Typeface.NORMAL));
                card.addView(row);

                TextView translation = text(entry.translation(Locale.getDefault()), 15, PRIMARY, Typeface.BOLD);
                translation.setPadding(0, dp(4), 0, 0);
                card.addView(translation);

                LinearLayout.LayoutParams lp = matchWrap();
                lp.bottomMargin = dp(8);
                root.addView(card, lp);
            }
        }

        setScrollable(root);
    }

    private void setQuestionScrollable(LinearLayout content, Button listeningAction) {
        int background = shop == null ? BG : shop.backgroundColor(BG);
        content.setPadding(dp(18), dp(14), dp(18), dp(132));

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(background);
        scroll.addView(content, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        FrameLayout shell = new FrameLayout(this);
        shell.setBackgroundColor(background);
        shell.addView(scroll, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        FrameLayout.LayoutParams actionLp = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(72), Gravity.BOTTOM);
        actionLp.leftMargin = dp(18);
        actionLp.rightMargin = dp(18);
        actionLp.bottomMargin = dp(24);
        shell.addView(listeningAction, actionLp);

        setContentView(shell);
    }

    private void showShop() {
        homeVisible = false;
        LinearLayout root = column();
        root.setPadding(dp(20), dp(20), dp(20), dp(30));

        Button back = compactButton("←");
        back.setOnClickListener(v -> showHome());
        root.addView(back, new LinearLayout.LayoutParams(dp(52), dp(44)));
        root.addView(space(14));
        root.addView(text(getString(R.string.shop_title), 28, INK, Typeface.BOLD));
        root.addView(text(getString(R.string.shop_balance_fmt, economy.balance()), 18, PRIMARY, Typeface.BOLD));
        root.addView(space(16));

        for (ShopItem item : shop.items()) {
            root.addView(shopItemCard(item));
        }

        root.addView(space(18));
        root.addView(text(getString(R.string.digital_rewards), 22, INK, Typeface.BOLD));
        TextView security = text(getString(R.string.reward_local_security_note), 13, MUTED, Typeface.NORMAL);
        security.setLineSpacing(dp(3), 1.04f);
        security.setPadding(0, dp(5), 0, dp(12));
        root.addView(security);

        for (DigitalRewardItem item : digitalRewards.items()) {
            root.addView(digitalRewardCard(item));
        }

        setScrollable(root);
    }

    private View dailyPlanCard() {
        PreparationPlan plan = PreparationPlan.create(progress, trainingTarget);
        ReadinessForecast readiness = ReadinessForecast.create(progress);
        LinearLayout card = column();
        card.setPadding(dp(18), dp(15), dp(18), dp(15));
        card.setBackground(roundRect(CARD, 18, 1, SOFT));
        card.addView(text(getString(R.string.daily_plan), 17, INK, Typeface.BOLD));
        card.addView(text(getString(R.string.daily_plan_summary, plan.questionsToday, plan.dueReviews),
                14, MUTED, Typeface.NORMAL));
        card.addView(text(getString(R.string.readiness_summary,
                        readiness.readinessPercent, readiness.confidencePercent),
                15, GOOD, Typeface.BOLD));
        List<String> labels = new ArrayList<>();
        for (String id : readiness.weakestKnowledge) labels.add(QuestionBank.knowledgeLabel(id, Locale.getDefault()));
        card.addView(text(getString(R.string.daily_plan_focus, android.text.TextUtils.join(" · ", labels)),
                13, PRIMARY, Typeface.BOLD));
        Button start = primaryButton(getString(R.string.daily_plan_start));
        LinearLayout.LayoutParams lp = matchWrap();
        lp.topMargin = dp(10);
        card.addView(start, lp);
        start.setOnClickListener(v -> startSession(getString(R.string.daily_plan),
                QuestionBank.adaptiveSession(progress, plan.questionsToday, System.currentTimeMillis() / 86400000L)));
        return card;
    }

    private void showWorkshop() {
        LinearLayout root = column();
        root.setPadding(dp(20), dp(20), dp(20), dp(30));
        Button back = compactButton("←");
        back.setOnClickListener(v -> showHome());
        root.addView(back, new LinearLayout.LayoutParams(dp(52), dp(44)));
        root.addView(space(14));
        root.addView(text(getString(R.string.workshop_title), 28, INK, Typeface.BOLD));
        root.addView(text(getString(R.string.workshop_caption), 14, MUTED, Typeface.NORMAL));
        root.addView(text(getString(R.string.shop_balance_fmt, economy.balance()), 18, PRIMARY, Typeface.BOLD));
        root.addView(space(14));
        for (WorkshopItem item : workshop.items()) root.addView(workshopCard(item));
        setScrollable(root);
    }

    private View workshopCard(WorkshopItem item) {
        LinearLayout card = column();
        card.setPadding(dp(16), dp(14), dp(16), dp(14));
        card.setBackground(roundRect(CARD, 14, 1, SOFT));
        card.addView(text(item.icon + "  " + item.name(Locale.getDefault()), 19, INK, Typeface.BOLD));
        card.addView(text(item.description(Locale.getDefault()), 14, MUTED, Typeface.NORMAL));
        Button action;
        if (workshop.isBuilt(item)) {
            action = secondaryButton(getString(R.string.workshop_built));
            action.setEnabled(false);
        } else {
            action = secondaryButton(getString(R.string.workshop_build, item.priceCrystals, item.requiredLevel));
            action.setOnClickListener(v -> {
                String result = workshop.build(item, progress.level());
                if ("built".equals(result)) showWorkshop();
                else new AlertDialog.Builder(this)
                        .setMessage("level".equals(result) ? getString(R.string.workshop_level_needed, item.requiredLevel)
                                : getString(R.string.shop_not_enough))
                        .setPositiveButton(getString(R.string.got_it), null).show();
            });
        }
        LinearLayout.LayoutParams actionLp = matchWrap();
        actionLp.topMargin = dp(9);
        card.addView(action, actionLp);
        LinearLayout.LayoutParams cardLp = matchWrap();
        cardLp.bottomMargin = dp(9);
        card.setLayoutParams(cardLp);
        return card;
    }

    private View shopItemCard(ShopItem item) {
        LinearLayout card = column();
        card.setPadding(dp(16), dp(14), dp(16), dp(14));

        int previewColor = CARD;
        if ("background".equals(item.type)) {
            try { previewColor = Color.parseColor(item.payload.optString("color")); }
            catch (Exception ignored) {}
        }
        card.setBackground(roundRect(previewColor, 14, 1, SOFT));

        LinearLayout head = row();
        head.addView(text(item.name(Locale.getDefault()), 18, INK, Typeface.BOLD),
                new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        head.addView(text("💎 " + item.priceCrystals, 15, PRIMARY, Typeface.BOLD));
        card.addView(head);

        TextView desc = text(item.description(Locale.getDefault()), 14, MUTED, Typeface.NORMAL);
        desc.setPadding(0, dp(5), 0, dp(10));
        card.addView(desc);

        Button action;
        if (shop.isEquipped(item)) {
            action = secondaryButton(getString(R.string.shop_equipped));
            action.setEnabled(false);
        } else if (shop.isOwned(item)) {
            action = secondaryButton(getString(R.string.shop_equip));
            action.setOnClickListener(v -> {
                shop.buyAndEquip(item);
                showShop();
            });
        } else {
            action = secondaryButton(getString(R.string.shop_buy_fmt, item.priceCrystals));
            action.setOnClickListener(v -> confirmShopPurchase(item));
        }
        card.addView(action, matchWrap());

        LinearLayout.LayoutParams lp = matchWrap();
        lp.bottomMargin = dp(9);
        card.setLayoutParams(lp);
        return card;
    }

    private void confirmShopPurchase(ShopItem item) {
        new AlertDialog.Builder(this)
                .setTitle(getString(R.string.shop_confirm_title, item.name(Locale.getDefault())))
                .setMessage(getString(R.string.shop_confirm_body, item.priceCrystals))
                .setPositiveButton(getString(R.string.shop_confirm), (dialog, which) -> {
                    if (shop.buyAndEquip(item)) {
                        showShop();
                    } else {
                        new AlertDialog.Builder(this)
                                .setMessage(getString(R.string.shop_not_enough))
                                .setPositiveButton(getString(R.string.got_it), null)
                                .show();
                    }
                })
                .setNegativeButton(getString(R.string.dictionary_close), null)
                .show();
    }

    private View digitalRewardCard(DigitalRewardItem item) {
        LinearLayout card = column();
        card.setPadding(dp(16), dp(14), dp(16), dp(14));
        card.setBackground(roundRect(CARD, 14, 1, SOFT));

        LinearLayout head = row();
        head.addView(text(item.name(Locale.getDefault()), 17, INK, Typeface.BOLD),
                new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        head.addView(text("💎 " + item.priceCrystals, 15, PRIMARY, Typeface.BOLD));
        card.addView(head);

        TextView desc = text(item.description(Locale.getDefault()), 14, MUTED, Typeface.NORMAL);
        desc.setPadding(0, dp(5), 0, dp(10));
        card.addView(desc);

        Button action;
        if (digitalRewards.isRedeemed(item)) {
            action = secondaryButton(getString(R.string.reward_open));
            action.setOnClickListener(v -> showOwnedReward(item));
        } else if (digitalRewards.canRedeemLocally(item)) {
            action = secondaryButton(getString(R.string.reward_redeem_fmt, item.priceCrystals));
            action.setOnClickListener(v -> confirmDigitalReward(item));
        } else {
            action = secondaryButton(item.backendRequired
                    ? getString(R.string.reward_locked_secure)
                    : getString(R.string.reward_locked_rights));
            action.setEnabled(false);
        }
        card.addView(action, matchWrap());

        LinearLayout.LayoutParams lp = matchWrap();
        lp.bottomMargin = dp(9);
        card.setLayoutParams(lp);
        return card;
    }

    private void confirmDigitalReward(DigitalRewardItem item) {
        new AlertDialog.Builder(this)
                .setTitle(getString(R.string.reward_redeem_title, item.name(Locale.getDefault())))
                .setMessage(getString(R.string.reward_redeem_body, item.priceCrystals))
                .setPositiveButton(getString(R.string.shop_confirm), (dialog, which) -> {
                    if (digitalRewards.redeemOwnedAsset(item)) {
                        showOwnedReward(item);
                    } else {
                        new AlertDialog.Builder(this)
                                .setMessage(getString(R.string.shop_not_enough))
                                .setPositiveButton(getString(R.string.got_it), null)
                                .show();
                    }
                })
                .setNegativeButton(getString(R.string.dictionary_close), null)
                .show();
    }

    private void showOwnedReward(DigitalRewardItem item) {
        String html = digitalRewards.readOwnedAsset(item);
        if (html.isEmpty()) {
            showShop();
            return;
        }

        LinearLayout root = column();
        root.setPadding(dp(20), dp(20), dp(20), dp(30));

        Button back = compactButton("←");
        back.setOnClickListener(v -> showShop());
        root.addView(back, new LinearLayout.LayoutParams(dp(52), dp(44)));
        root.addView(space(12));
        root.addView(text(item.name(Locale.getDefault()), 25, INK, Typeface.BOLD));
        root.addView(space(10));

        TextView content = text("", 17, INK, Typeface.NORMAL);
        content.setLineSpacing(dp(5), 1.06f);
        content.setText(Html.fromHtml(html, Html.FROM_HTML_MODE_LEGACY));
        root.addView(content, matchWrap());

        Button close = primaryButton(getString(R.string.reward_book_close));
        close.setOnClickListener(v -> showShop());
        LinearLayout.LayoutParams lp = matchWrap();
        lp.topMargin = dp(18);
        root.addView(close, lp);

        setScrollable(root);
    }

    private void showSettings() {
        homeVisible = false;
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

        TextView volumeLabel = text(getString(R.string.effects_volume_fmt, rewards.volume()),
                16, INK, Typeface.BOLD);
        volumeLabel.setPadding(dp(12), dp(14), dp(12), dp(4));
        root.addView(volumeLabel, matchWrap());

        android.widget.SeekBar volume = new android.widget.SeekBar(this);
        volume.setMax(100);
        volume.setProgress(rewards.volume());
        volume.setPadding(dp(12), dp(2), dp(12), dp(8));
        volume.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(android.widget.SeekBar seekBar, int value, boolean fromUser) {
                volumeLabel.setText(getString(R.string.effects_volume_fmt, value));
                if (fromUser) rewards.setVolume(value);
            }
            @Override public void onStartTrackingTouch(android.widget.SeekBar seekBar) {}
            @Override public void onStopTrackingTouch(android.widget.SeekBar seekBar) {}
        });
        root.addView(volume, matchWrap());

        android.widget.Switch quotes = new android.widget.Switch(this);
        quotes.setText(getString(R.string.quotes_setting));
        quotes.setTextSize(17);
        quotes.setChecked(getSharedPreferences("english_sprint_settings", MODE_PRIVATE)
                .getBoolean("quotes", true));
        quotes.setPadding(dp(12), dp(12), dp(12), dp(12));
        quotes.setOnCheckedChangeListener((buttonView, isChecked) ->
                getSharedPreferences("english_sprint_settings", MODE_PRIVATE)
                        .edit().putBoolean("quotes", isChecked).apply());
        root.addView(quotes, matchWrap());

        android.widget.Switch miniGameSwitch = new android.widget.Switch(this);
        miniGameSwitch.setText(getString(R.string.minigame_setting));
        miniGameSwitch.setTextSize(17);
        miniGameSwitch.setChecked(getSharedPreferences("english_sprint_settings", MODE_PRIVATE)
                .getBoolean("minigames", true));
        miniGameSwitch.setPadding(dp(12), dp(12), dp(12), dp(12));
        miniGameSwitch.setOnCheckedChangeListener((buttonView, isChecked) ->
                getSharedPreferences("english_sprint_settings", MODE_PRIVATE)
                        .edit().putBoolean("minigames", isChecked).apply());
        root.addView(miniGameSwitch, matchWrap());

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

        TextView languageTitle=text(getString(R.string.language_setting),13,MUTED,Typeface.BOLD);
        languageTitle.setPadding(dp(12),dp(22),dp(12),dp(6)); root.addView(languageTitle,matchWrap());
        Button language=secondaryButton(getString(R.string.language_current, LocaleStore.current(this)));
        language.setOnClickListener(v->new AlertDialog.Builder(this).setTitle(getString(R.string.language_setting))
                .setItems(new String[]{"Русский","English","System"},(d,w)-> LocaleStore.set(this,w==0?"ru":w==1?"en":"system")).show());
        root.addView(language,matchWrap());

        TextView worldTitle=text(getString(R.string.preferred_world),13,MUTED,Typeface.BOLD);
        worldTitle.setPadding(dp(12),dp(22),dp(12),dp(6)); root.addView(worldTitle,matchWrap());
        Button worldChoice=secondaryButton(modeName(metaGame.preferredMode()));
        worldChoice.setOnClickListener(v->new AlertDialog.Builder(this).setTitle(getString(R.string.preferred_world))
                .setItems(new String[]{getString(R.string.mode_pet),getString(R.string.mode_defense),getString(R.string.mode_hero)},(d,w)->{metaGame.setPreferredMode(w==1?MetaGameStore.DEFENSE:w==2?MetaGameStore.HERO:MetaGameStore.PET); showSettings();}).show());
        root.addView(worldChoice,matchWrap());

        TextView targetTitle = text(getString(R.string.target_section), 13, MUTED, Typeface.BOLD);
        targetTitle.setPadding(dp(12), dp(22), dp(12), dp(6));
        root.addView(targetTitle, matchWrap());

        TextView targetSummary = text(trainingTarget.summary(), 16, INK, Typeface.BOLD);
        targetSummary.setPadding(dp(12), dp(4), dp(12), dp(2));
        root.addView(targetSummary, matchWrap());

        TextView targetDate = text(getString(R.string.target_date_label, trainingTarget.targetDate()),
                14, MUTED, Typeface.NORMAL);
        targetDate.setPadding(dp(12), dp(2), dp(12), dp(8));
        root.addView(targetDate, matchWrap());

        android.widget.Switch targetMode = new android.widget.Switch(this);
        targetMode.setText(getString(R.string.target_specific_mode));
        targetMode.setTextSize(16);
        targetMode.setChecked(TrainingTargetStore.MODE_COMPETITION.equals(trainingTarget.mode()));
        targetMode.setPadding(dp(12), dp(8), dp(12), dp(8));
        targetMode.setOnCheckedChangeListener((buttonView, isChecked) ->
                trainingTarget.setMode(isChecked
                        ? TrainingTargetStore.MODE_COMPETITION
                        : TrainingTargetStore.MODE_GENERAL));
        root.addView(targetMode, matchWrap());

        Button targetDateButton = secondaryButton(getString(R.string.target_set_date));
        targetDateButton.setOnClickListener(v -> showTargetDatePicker());
        root.addView(targetDateButton, matchWrap());

        TextView updatesTitle = text(getString(R.string.updates_section), 13, MUTED, Typeface.BOLD);
        updatesTitle.setPadding(dp(12), dp(22), dp(12), dp(6));
        root.addView(updatesTitle, matchWrap());

        TextView installedVersion = text(
                getString(R.string.update_version_fmt, BuildConfig.VERSION_NAME),
                15, INK, Typeface.NORMAL);
        installedVersion.setPadding(dp(12), dp(4), dp(12), dp(8));
        root.addView(installedVersion, matchWrap());

        Button updateButton = secondaryButton(getString(R.string.update_check));
        updateButton.setOnClickListener(v -> updater.showCheckDialog());
        root.addView(updateButton, matchWrap());

        updater.check((info, error) -> {
            if (info != null && error == null) {
                updateButton.setText(getString(R.string.update_button_available, info.version));
                updateButton.setTextColor(Color.WHITE);
                updateButton.setBackground(roundRect(PRIMARY,
                        shop == null ? 14 : shop.buttonRadius(14), 0, Color.TRANSPARENT));
            }
        });

        setScrollable(root);
    }

    private void showPackPicker() { showPackPicker(false); }

    private void showPackPicker(boolean returnToLearn) {
        List<ContentPack> packs = QuestionBank.availablePacks();
        String[] labels = new String[packs.size()];
        int selected = 0;
        for (int i = 0; i < packs.size(); i++) {
            labels[i] = humanPackLabel(packs.get(i));
            if (packs.get(i).id.equals(QuestionBank.currentPack().id)) selected = i;
        }
        final int checked = selected;
        new AlertDialog.Builder(this)
                .setTitle(getString(R.string.content_pack_section))
                .setSingleChoiceItems(labels, checked, (dialog, which) -> {
                    if (which != checked) {
                        QuestionBank.selectPack(this, packs.get(which).id);
                        progress = new ProgressStore(this);
                        learningContext.remember(packs.get(which).id,packs.get(which).gradeMin,packs.get(which).competition);
                        trainingTarget = new TrainingTargetStore(this, QuestionBank.currentPack());
                        trainingTarget.selectContext(QuestionBank.currentPack(),packs.get(which).gradeMin,packs.get(which).competition);
                    }
                    dialog.dismiss();
                    if (returnToLearn) showLearnHub(); else showHome();
                })
                .setNegativeButton(getString(R.string.dictionary_close), null)
                .show();
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

    private void showTargetDatePicker() {
        Calendar initial = Calendar.getInstance();
        String raw = trainingTarget.targetDate();
        try {
            String[] parts = raw.split("-");
            if (parts.length == 3) {
                initial.set(Integer.parseInt(parts[0]),
                        Integer.parseInt(parts[1]) - 1,
                        Integer.parseInt(parts[2]));
            }
        } catch (Exception ignored) {
        }

        new android.app.DatePickerDialog(
                this,
                (view, year, month, day) -> {
                    trainingTarget.setTargetDate(year, month, day);
                    showSettings();
                },
                initial.get(Calendar.YEAR),
                initial.get(Calendar.MONTH),
                initial.get(Calendar.DAY_OF_MONTH)
        ).show();
    }

    private View sectionHeading(String heading, String caption) {
        LinearLayout group = column();
        group.addView(text(heading, 21, INK, Typeface.BOLD));
        TextView supporting = text(caption, 13, MUTED, Typeface.NORMAL);
        supporting.setPadding(0, dp(4), 0, 0);
        group.addView(supporting);
        return group;
    }

    private View spaceHorizontal(int width) {
        Space spacer = new Space(this);
        spacer.setLayoutParams(new LinearLayout.LayoutParams(dp(width), 1));
        return spacer;
    }

    private View featureCard(String symbol, String heading, String caption, int tint, Runnable action) {
        LinearLayout card = row();
        card.setPadding(dp(15), dp(15), dp(15), dp(15));
        card.setBackground(RiftStyle.shape(this, Color.WHITE, 19, 1, SOFT));
        RiftStyle.raise(card, 2);
        TextView emblem = text(symbol, 26, tint, Typeface.BOLD);
        emblem.setGravity(Gravity.CENTER);
        emblem.setBackground(RiftStyle.shape(this,
                tint == RiftStyle.VIOLET ? Color.rgb(245, 238, 255) :
                tint == RiftStyle.GOOD ? Color.rgb(231, 249, 241) :
                Color.rgb(237, 240, 255), 16, 0, Color.TRANSPARENT));
        card.addView(emblem, new LinearLayout.LayoutParams(dp(56), dp(56)));
        LinearLayout labels = column();
        labels.setPadding(dp(14), 0, 0, 0);
        labels.addView(text(heading, 17, INK, Typeface.BOLD));
        labels.addView(space(4));
        labels.addView(text(caption, 13, MUTED, Typeface.NORMAL));
        card.addView(labels, new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        card.addView(text("›", 28, tint, Typeface.BOLD));
        card.setOnClickListener(v -> action.run());
        card.setClickable(true);
        return card;
    }

    private LinearLayout column() {
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setBackgroundColor(shop == null ? BG : shop.backgroundColor(BG));
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
        scroll.setBackgroundColor(shop == null ? BG : shop.backgroundColor(BG));
        scroll.addView(content, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        setContentView(scroll);
        scroll.setAlpha(0f);
        scroll.animate().alpha(1f).setDuration(180).start();
        hideSystemNavigation();
    }

    private TextView text(String value, float sp, int color, int style) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(sp);
        t.setTextColor(color);
        t.setIncludeFontPadding(false);
        t.setTypeface(Typeface.create(style == Typeface.BOLD ? "sans-serif-medium" : "sans-serif",
                style));
        return t;
    }

    private Button answerButton(String value) {
        Button b = new Button(this);
        b.setText(value);
        b.setTextSize(17);
        b.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        b.setTextColor(INK);
        b.setAllCaps(false);
        b.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        b.setPadding(dp(18), dp(11), dp(18), dp(11));
        b.setMinHeight(dp(64));
        b.setBackground(RiftStyle.shape(this, CARD, 17, 1, SOFT));
        b.setElevation(0);
        return b;
    }

    private Button primaryButton(String value) {
        Button b = new Button(this);
        b.setText(value);
        b.setTextSize(17);
        b.setTextColor(Color.WHITE);
        b.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        b.setAllCaps(false);
        b.setMinHeight(dp(58));
        b.setBackground(RiftStyle.gradient(this, 18, RiftStyle.BLUE, RiftStyle.VIOLET));
        RiftStyle.raise(b, 3);
        return b;
    }

    private Button secondaryButton(String value) {
        Button b = new Button(this);
        b.setText(value);
        b.setTextSize(16);
        b.setTextColor(INK);
        b.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        b.setAllCaps(false);
        b.setMinHeight(dp(54));
        b.setBackground(RiftStyle.shape(this, CARD, 17, 1, SOFT));
        b.setElevation(0);
        return b;
    }

    private Button compactButton(String value) {
        Button b = new Button(this);
        b.setText(value);
        b.setTextSize(20);
        b.setTextColor(INK);
        b.setAllCaps(false);
        b.setPadding(0, 0, 0, 0);
        b.setBackground(RiftStyle.shape(this, CARD, 15, 1, SOFT));
        b.setElevation(0);
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
