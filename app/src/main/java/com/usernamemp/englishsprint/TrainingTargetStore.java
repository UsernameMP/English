package com.usernamemp.englishsprint;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Locale;

public final class TrainingTargetStore {
    public static final String MODE_COMPETITION = "competition";
    public static final String MODE_GENERAL = "general";

    private static final String PREFS = "english_sprint_training_target";
    private final SharedPreferences prefs;

    public TrainingTargetStore(Context context, ContentPack pack) {
        Context app = context.getApplicationContext();
        prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        if (!prefs.getBoolean("initialized", false)) initializeDefaults(app, pack);
    }

    public String subject() { return prefs.getString("subject", "english"); }
    public int grade() { return prefs.getInt("grade", 5); }
    public String competition() { return prefs.getString("competition", ""); }
    public String region() { return prefs.getString("region", ""); }
    public String season() { return prefs.getString("season", ""); }
    public String targetDate() { return prefs.getString("target_date", ""); }
    public String mode() { return prefs.getString("mode", MODE_COMPETITION); }

    public void setMode(String value) {
        prefs.edit().putString("mode", MODE_GENERAL.equals(value) ? MODE_GENERAL : MODE_COMPETITION).apply();
    }

    public void setTargetDate(int year, int monthZeroBased, int day) {
        Calendar c = Calendar.getInstance();
        c.set(year, monthZeroBased, day, 0, 0, 0);
        c.set(Calendar.MILLISECOND, 0);
        SimpleDateFormat fmt = new SimpleDateFormat("yyyy-MM-dd", Locale.US);
        prefs.edit().putString("target_date", fmt.format(c.getTime())).apply();
    }

    public int daysRemaining() {
        String raw = targetDate();
        if (raw.isEmpty()) return -1;
        try {
            SimpleDateFormat fmt = new SimpleDateFormat("yyyy-MM-dd", Locale.US);
            Calendar target = Calendar.getInstance();
            target.setTime(fmt.parse(raw));
            zeroTime(target);
            Calendar today = Calendar.getInstance();
            zeroTime(today);
            return (int) Math.floor((target.getTimeInMillis() - today.getTimeInMillis()) / 86400000.0);
        } catch (Exception e) {
            return -1;
        }
    }

    public String summary() {
        boolean ru = "ru".equals(Locale.getDefault().getLanguage());
        String gradeLabel = ru ? grade() + " класс" : "Grade " + grade();
        if (MODE_GENERAL.equals(mode())) {
            return subject() + " · " + gradeLabel;
        }
        String base = competition().isEmpty() ? subject() : competition();
        return base + " · " + gradeLabel + (region().isEmpty() ? "" : " · " + region());
    }

    private void initializeDefaults(Context context, ContentPack pack) {
        String date = "";
        String mode = MODE_COMPETITION;
        int grade = pack.gradeMin;
        try {
            JSONObject root = new JSONObject(readAsset(context, "content/training_targets.json"));
            JSONArray targets = root.getJSONArray("targets");
            for (int i = 0; i < targets.length(); i++) {
                JSONObject t = targets.getJSONObject(i);
                if (!pack.id.equals(t.optString("pack_id"))) continue;
                date = t.optString("target_date", "");
                mode = t.optString("mode", MODE_COMPETITION);
                grade = t.optInt("grade", grade);
                break;
            }
        } catch (Exception ignored) {
        }

        prefs.edit()
                .putBoolean("initialized", true)
                .putString("subject", pack.subject)
                .putInt("grade", grade)
                .putString("competition", pack.competition)
                .putString("region", pack.region)
                .putString("season", pack.season)
                .putString("target_date", date)
                .putString("mode", mode)
                .apply();
    }

    private static void zeroTime(Calendar c) {
        c.set(Calendar.HOUR_OF_DAY, 0);
        c.set(Calendar.MINUTE, 0);
        c.set(Calendar.SECOND, 0);
        c.set(Calendar.MILLISECOND, 0);
    }

    private static String readAsset(Context context, String path) throws Exception {
        try (InputStream in = context.getAssets().open(path);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) != -1) out.write(buffer, 0, read);
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }
}
