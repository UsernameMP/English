package com.usernamemp.englishsprint;

import android.content.Context;
import android.content.SharedPreferences;

/** Learner navigation context; intentionally separate from global Knowledge Units. */
public final class LearningContextStore {
    public static final String ALL_OLYMPIADS = "all";
    private final SharedPreferences prefs;

    public LearningContextStore(Context context) {
        prefs = context.getSharedPreferences("english_sprint_learning_context", Context.MODE_PRIVATE);
    }

    public boolean hasSelection() { return !packId().isEmpty() && grade() > 0; }
    public String packId() { return prefs.getString("pack_id", ""); }
    public int grade() { return prefs.getInt("grade", 0); }
    public String target() { return prefs.getString("target", ""); }

    public void remember(String packId, int grade, String target) {
        if (packId == null || packId.isEmpty() || grade < 1) return;
        prefs.edit().putString("pack_id", packId).putInt("grade", grade)
                .putString("target", target == null ? "" : target).apply();
    }

    public boolean isValidFor(ContentPack pack) {
        return pack != null && hasSelection() && pack.id.equals(packId())
                && grade() >= pack.gradeMin && grade() <= pack.gradeMax;
    }
}
