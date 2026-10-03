package com.usernamemp.englishsprint;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.LinkedHashMap;
import java.util.Map;

public final class ProgressStore {
    private static final String PREFS = "english_sprint_progress";
    private final SharedPreferences prefs;

    public ProgressStore(Context context) {
        prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public void record(Question question, boolean correct) {
        String base = "skill_" + question.skill + "_";
        int attempts = prefs.getInt(base + "attempts", 0) + 1;
        int rights = prefs.getInt(base + "correct", 0) + (correct ? 1 : 0);

        int combo = correct ? prefs.getInt("combo", 0) + 1 : 0;
        int best = Math.max(combo, prefs.getInt("best_combo", 0));
        int xpGain = correct ? 10 + Math.min(combo, 10) * 2 : 2;

        prefs.edit()
                .putInt(base + "attempts", attempts)
                .putInt(base + "correct", rights)
                .putInt("combo", combo)
                .putInt("best_combo", best)
                .putInt("xp", prefs.getInt("xp", 0) + xpGain)
                .putInt("answered", prefs.getInt("answered", 0) + 1)
                .apply();
    }

    public double mastery(String skill) {
        String base = "skill_" + skill + "_";
        int attempts = prefs.getInt(base + "attempts", 0);
        int correct = prefs.getInt(base + "correct", 0);
        if (attempts == 0) return 0.50;
        // Beta(1,1) smoothing: first wrong answer drops mastery below unseen skills,
        // first correct answer raises it above unseen skills.
        return (correct + 1.0) / (attempts + 2.0);
    }

    public int attempts(String skill) {
        return prefs.getInt("skill_" + skill + "_attempts", 0);
    }

    public int correct(String skill) {
        return prefs.getInt("skill_" + skill + "_correct", 0);
    }

    public int xp() {
        return prefs.getInt("xp", 0);
    }

    public int combo() {
        return prefs.getInt("combo", 0);
    }

    public int bestCombo() {
        return prefs.getInt("best_combo", 0);
    }

    public int answered() {
        return prefs.getInt("answered", 0);
    }

    public int level() {
        return 1 + xp() / 350;
    }

    public int xpInLevel() {
        return xp() % 350;
    }

    public Map<String, Double> masteryMap() {
        Map<String, Double> result = new LinkedHashMap<>();
        for (String skill : QuestionBank.SKILLS) {
            result.put(skill, mastery(skill));
        }
        return result;
    }

    public void reset() {
        prefs.edit().clear().apply();
    }
}
