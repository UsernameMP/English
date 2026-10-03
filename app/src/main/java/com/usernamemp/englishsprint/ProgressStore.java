package com.usernamemp.englishsprint;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.LinkedHashMap;
import java.util.Map;

public final class ProgressStore {
    private static final String PREFS = "english_sprint_progress";
    private static final String KNOWLEDGE_MIGRATION = "knowledge_migrated_v1";
    private final SharedPreferences prefs;

    public ProgressStore(Context context) {
        prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        migrateLegacyKnowledge();
    }

    public void record(Question question, boolean correct) {
        SharedPreferences.Editor editor = prefs.edit();

        // Keep the legacy counters during the transition so v0.3 progress remains compatible.
        updateEvidence(editor, "skill_" + question.skill + "_", correct);

        for (KnowledgeRef ref : question.knowledge) {
            updateEvidence(editor, knowledgeBase(ref.id), correct);
        }

        int combo = correct ? prefs.getInt("combo", 0) + 1 : 0;
        int best = Math.max(combo, prefs.getInt("best_combo", 0));
        int xpGain = correct ? 10 + Math.min(combo, 10) * 2 : 2;

        editor
                .putInt("combo", combo)
                .putInt("best_combo", best)
                .putInt("xp", prefs.getInt("xp", 0) + xpGain)
                .putInt("answered", prefs.getInt("answered", 0) + 1)
                .apply();
    }

    private void updateEvidence(SharedPreferences.Editor editor, String base, boolean correct) {
        int attempts = prefs.getInt(base + "attempts", 0) + 1;
        int rights = prefs.getInt(base + "correct", 0) + (correct ? 1 : 0);
        int recentMistakes = prefs.getInt(base + "recent_mistakes", 0);
        recentMistakes = correct ? Math.max(0, recentMistakes - 1) : Math.min(8, recentMistakes + 2);

        long now = System.currentTimeMillis();
        int previousInterval = prefs.getInt(base + "review_interval_days", 0);
        int nextInterval;
        long nextReview;
        if (correct) {
            if (previousInterval < 1) nextInterval = 1;
            else if (previousInterval < 3) nextInterval = 3;
            else if (previousInterval < 7) nextInterval = 7;
            else if (previousInterval < 14) nextInterval = 14;
            else nextInterval = 30;
            nextReview = now + nextInterval * 24L * 60L * 60L * 1000L;
        } else {
            nextInterval = 0;
            nextReview = now + 6L * 60L * 60L * 1000L;
        }

        editor
                .putInt(base + "attempts", attempts)
                .putInt(base + "correct", rights)
                .putInt(base + "recent_mistakes", recentMistakes)
                .putLong(base + "last_seen_at", now)
                .putLong(base + "next_review_at", nextReview)
                .putInt(base + "review_interval_days", nextInterval);
    }

    public double mastery(String skillOrKnowledge) {
        if (QuestionBank.knowledgeUnit(skillOrKnowledge) != null) {
            return masteryKnowledge(skillOrKnowledge);
        }
        int attempts = attempts(skillOrKnowledge);
        int correct = correct(skillOrKnowledge);
        if (attempts == 0) return 0.50;
        return (correct + 1.0) / (attempts + 2.0);
    }

    public double masteryKnowledge(String knowledgeId) {
        int attempts = attemptsKnowledge(knowledgeId);
        int correct = correctKnowledge(knowledgeId);
        if (attempts == 0) return 0.50;
        return (correct + 1.0) / (attempts + 2.0);
    }

    public int attempts(String skillOrKnowledge) {
        if (QuestionBank.knowledgeUnit(skillOrKnowledge) != null) {
            return attemptsKnowledge(skillOrKnowledge);
        }
        return prefs.getInt("skill_" + skillOrKnowledge + "_attempts", 0);
    }

    public int correct(String skillOrKnowledge) {
        if (QuestionBank.knowledgeUnit(skillOrKnowledge) != null) {
            return correctKnowledge(skillOrKnowledge);
        }
        return prefs.getInt("skill_" + skillOrKnowledge + "_correct", 0);
    }

    public int recentMistakes(String skillOrKnowledge) {
        if (QuestionBank.knowledgeUnit(skillOrKnowledge) != null) {
            return recentMistakesKnowledge(skillOrKnowledge);
        }
        return prefs.getInt("skill_" + skillOrKnowledge + "_recent_mistakes", 0);
    }

    public int attemptsKnowledge(String knowledgeId) {
        return prefs.getInt(knowledgeBase(knowledgeId) + "attempts", 0);
    }

    public int correctKnowledge(String knowledgeId) {
        return prefs.getInt(knowledgeBase(knowledgeId) + "correct", 0);
    }

    public int recentMistakesKnowledge(String knowledgeId) {
        return prefs.getInt(knowledgeBase(knowledgeId) + "recent_mistakes", 0);
    }

    public long nextReviewAt(String knowledgeId) {
        return prefs.getLong(knowledgeBase(knowledgeId) + "next_review_at", 0L);
    }

    public boolean isDue(String knowledgeId) {
        if (attemptsKnowledge(knowledgeId) == 0) return false;
        long next = nextReviewAt(knowledgeId);
        return next > 0L && next <= System.currentTimeMillis();
    }

    public int reviewIntervalDays(String knowledgeId) {
        return prefs.getInt(knowledgeBase(knowledgeId) + "review_interval_days", 0);
    }

    public SkillState state(String skillOrKnowledge) {
        int a = attempts(skillOrKnowledge);
        if (a < 3) return SkillState.NOT_CHECKED;
        double m = mastery(skillOrKnowledge);
        if (m < 0.55) return SkillState.LEARNING;
        if (m < 0.76) return SkillState.GROWING;
        return SkillState.CONFIDENT;
    }

    public enum SkillState {
        NOT_CHECKED,
        LEARNING,
        GROWING,
        CONFIDENT
    }

    public int xp() { return prefs.getInt("xp", 0); }
    public int combo() { return prefs.getInt("combo", 0); }
    public int bestCombo() { return prefs.getInt("best_combo", 0); }
    public int answered() { return prefs.getInt("answered", 0); }
    public int level() { return 1 + xp() / 350; }
    public int xpInLevel() { return xp() % 350; }

    public Map<String, Double> masteryMap() {
        Map<String, Double> result = new LinkedHashMap<>();
        for (String id : QuestionBank.knowledgeIds()) result.put(id, masteryKnowledge(id));
        return result;
    }

    public void reset() {
        prefs.edit().clear().apply();
    }

    private String knowledgeBase(String id) {
        return "knowledge_" + id + "_";
    }

    private void migrateLegacyKnowledge() {
        if (prefs.getBoolean(KNOWLEDGE_MIGRATION, false)) return;

        SharedPreferences.Editor editor = prefs.edit();
        for (String id : QuestionBank.knowledgeIds()) {
            String legacy = QuestionBank.legacySkillForKnowledge(id);
            if (legacy.isEmpty()) continue;

            String oldBase = "skill_" + legacy + "_";
            String newBase = knowledgeBase(id);
            if (prefs.getInt(newBase + "attempts", 0) > 0) continue;

            editor
                    .putInt(newBase + "attempts", prefs.getInt(oldBase + "attempts", 0))
                    .putInt(newBase + "correct", prefs.getInt(oldBase + "correct", 0))
                    .putInt(newBase + "recent_mistakes", prefs.getInt(oldBase + "recent_mistakes", 0));
        }
        editor.putBoolean(KNOWLEDGE_MIGRATION, true).apply();
    }
}
