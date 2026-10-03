package com.usernamemp.englishsprint;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public final class PlayCreditStore {
    private static final String PREFS = "english_sprint_play_credits";
    private static final String KEY_BALANCE = "balance";
    private static final String KEY_EARNED = "earned";
    private static final String KEY_SPENT = "spent";

    private final SharedPreferences prefs;
    private int questionsPerCredit = 10;
    private int maxBalance = 5;
    private int gameSessionCost = 1;

    public PlayCreditStore(Context context) {
        Context app = context.getApplicationContext();
        prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        loadConfig(app);
    }

    public int balance() { return prefs.getInt(KEY_BALANCE, 0); }
    public int lifetimeEarned() { return prefs.getInt(KEY_EARNED, 0); }
    public int lifetimeSpent() { return prefs.getInt(KEY_SPENT, 0); }
    public int questionsPerCredit() { return questionsPerCredit; }

    public boolean awardForLearningProgress(int answeredInSession) {
        if (answeredInSession <= 0 || answeredInSession % questionsPerCredit != 0) return false;
        int current = balance();
        if (current >= maxBalance) return false;
        prefs.edit()
                .putInt(KEY_BALANCE, current + 1)
                .putInt(KEY_EARNED, lifetimeEarned() + 1)
                .apply();
        return true;
    }

    public boolean canStartGame() {
        return balance() >= gameSessionCost;
    }

    public boolean consumeGameSession() {
        int current = balance();
        if (current < gameSessionCost) return false;
        prefs.edit()
                .putInt(KEY_BALANCE, current - gameSessionCost)
                .putInt(KEY_SPENT, lifetimeSpent() + gameSessionCost)
                .apply();
        return true;
    }

    private void loadConfig(Context context) {
        try {
            JSONObject root = new JSONObject(readAsset(context, "game/play_credits.json"));
            questionsPerCredit = Math.max(1, root.optInt("questions_per_credit", 10));
            maxBalance = Math.max(1, root.optInt("max_balance", 5));
            gameSessionCost = Math.max(1, root.optInt("game_session_cost", 1));
        } catch (Exception e) {
            throw new IllegalStateException("Play-credit config failed to load", e);
        }
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
