package com.usernamemp.englishsprint;

import android.content.Context;
import android.content.SharedPreferences;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/** Local, sync-ready daily aggregates. Absence is intentionally neutral. */
public final class ActivityStore {
    private static final String PREFS = "english_sprint_activity_v1";
    private final SharedPreferences prefs;

    public static final class Day {
        public final String date;
        public final int answered;
        public final int correct;
        public final int xp;
        public final int crystals;
        public final int bestCombo;
        public final int sessions;

        Day(String date, SharedPreferences prefs) {
            this.date = date;
            String base = "day_" + date + "_";
            answered = prefs.getInt(base + "answered", 0);
            correct = prefs.getInt(base + "correct", 0);
            xp = prefs.getInt(base + "xp", 0);
            crystals = prefs.getInt(base + "crystals", 0);
            bestCombo = prefs.getInt(base + "best_combo", 0);
            sessions = prefs.getInt(base + "sessions", 0);
        }

        public boolean active() { return answered > 0 || sessions > 0; }
    }

    public ActivityStore(Context context) {
        prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public void recordAnswer(boolean correct, int xpGain, int crystalGain, int combo, String packId) {
        String date = localDate(new Date());
        String base = "day_" + date + "_";
        prefs.edit()
                .putInt(base + "answered", prefs.getInt(base + "answered", 0) + 1)
                .putInt(base + "correct", prefs.getInt(base + "correct", 0) + (correct ? 1 : 0))
                .putInt(base + "xp", prefs.getInt(base + "xp", 0) + Math.max(0, xpGain))
                .putInt(base + "crystals", prefs.getInt(base + "crystals", 0) + Math.max(0, crystalGain))
                .putInt(base + "best_combo", Math.max(combo, prefs.getInt(base + "best_combo", 0)))
                .putString(base + "last_pack", packId)
                .apply();
    }

    public void recordSessionCompleted() {
        String date = localDate(new Date());
        String key = "day_" + date + "_sessions";
        prefs.edit().putInt(key, prefs.getInt(key, 0) + 1).apply();
    }

    public List<Day> recentDays(int count) {
        if (count < 1) return Collections.emptyList();
        List<Day> result = new ArrayList<>();
        Calendar calendar = Calendar.getInstance();
        calendar.add(Calendar.DAY_OF_YEAR, -(count - 1));
        for (int i = 0; i < count; i++) {
            result.add(new Day(localDate(calendar.getTime()), prefs));
            calendar.add(Calendar.DAY_OF_YEAR, 1);
        }
        return result;
    }

    public List<Day> currentMonth() {
        List<Day> result = new ArrayList<>();
        Calendar calendar = Calendar.getInstance();
        int today = calendar.get(Calendar.DAY_OF_MONTH);
        calendar.set(Calendar.DAY_OF_MONTH, 1);
        for (int i = 0; i < today; i++) {
            result.add(new Day(localDate(calendar.getTime()), prefs));
            calendar.add(Calendar.DAY_OF_MONTH, 1);
        }
        return result;
    }

    private static String localDate(Date date) {
        return new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(date);
    }
}
