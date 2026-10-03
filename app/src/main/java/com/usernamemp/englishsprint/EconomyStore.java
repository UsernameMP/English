package com.usernamemp.englishsprint;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

public final class EconomyStore {
    public static final String REASON_CORRECT = "correct_answer";
    public static final String REASON_BLOCK_10 = "completed_10_questions";
    public static final String REASON_NEW_RECORD = "new_record";
    public static final String REASON_CONFIDENT = "knowledge_confident";
    public static final String REASON_REINFORCED = "reinforced";

    private static final String PREFS = "english_sprint_economy";
    private static final String KEY_BALANCE = "balance";
    private static final String KEY_EARNED = "lifetime_earned";
    private static final String KEY_SPENT = "lifetime_spent";
    private static final String KEY_LEDGER = "ledger_json";
    private static final int MAX_LEDGER = 500;

    private final Context context;
    private final SharedPreferences prefs;
    private final Map<String, Integer> rewards = new HashMap<>();

    public EconomyStore(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        loadConfig();
    }

    public int balance() { return prefs.getInt(KEY_BALANCE, 0); }
    public int lifetimeEarned() { return prefs.getInt(KEY_EARNED, 0); }
    public int lifetimeSpent() { return prefs.getInt(KEY_SPENT, 0); }

    public int reward(String reason) {
        Integer value = rewards.get(reason);
        return value == null ? 0 : Math.max(0, value);
    }

    public synchronized int awardLearning(
            boolean correct,
            int combo,
            boolean newRecord,
            boolean becameConfident,
            boolean reinforced,
            int answeredInSession,
            String source
    ) {
        int total = 0;
        if (correct) total += credit(reward(REASON_CORRECT), REASON_CORRECT, source);

        if (correct) {
            String comboReason = null;
            if (combo == 3) comboReason = "combo_3";
            else if (combo == 5) comboReason = "combo_5";
            else if (combo == 8) comboReason = "combo_8";
            else if (combo == 10) comboReason = "combo_10";
            else if (combo == 15) comboReason = "combo_15";
            if (comboReason != null) total += credit(reward(comboReason), comboReason, source);
        }

        if (newRecord) total += credit(reward(REASON_NEW_RECORD), REASON_NEW_RECORD, source);
        if (becameConfident) total += credit(reward(REASON_CONFIDENT), REASON_CONFIDENT, source);
        if (reinforced) total += credit(reward(REASON_REINFORCED), REASON_REINFORCED, source);
        if (answeredInSession > 0 && answeredInSession % 10 == 0) {
            total += credit(reward(REASON_BLOCK_10), REASON_BLOCK_10, source);
        }
        return total;
    }

    public synchronized int credit(int amount, String reason, String source) {
        if (amount <= 0) return 0;
        int next = balance() + amount;
        SharedPreferences.Editor editor = prefs.edit()
                .putInt(KEY_BALANCE, next)
                .putInt(KEY_EARNED, lifetimeEarned() + amount);
        appendLedger(editor, amount, reason, source);
        editor.apply();
        return amount;
    }

    public synchronized boolean spend(int amount, String reason, String source) {
        if (amount <= 0) return false;
        int current = balance();
        if (amount > current) return false;
        SharedPreferences.Editor editor = prefs.edit()
                .putInt(KEY_BALANCE, current - amount)
                .putInt(KEY_SPENT, lifetimeSpent() + amount);
        appendLedger(editor, -amount, reason, source);
        editor.apply();
        return true;
    }

    public JSONArray ledger() {
        try {
            return new JSONArray(prefs.getString(KEY_LEDGER, "[]"));
        } catch (Exception e) {
            return new JSONArray();
        }
    }

    private void appendLedger(SharedPreferences.Editor editor, int delta, String reason, String source) {
        JSONArray oldLedger = ledger();
        JSONArray trimmed = new JSONArray();
        int start = Math.max(0, oldLedger.length() - (MAX_LEDGER - 1));
        for (int i = start; i < oldLedger.length(); i++) {
            try { trimmed.put(oldLedger.getJSONObject(i)); } catch (Exception ignored) {}
        }

        JSONObject tx = new JSONObject();
        try {
            tx.put("id", UUID.randomUUID().toString());
            tx.put("ts", System.currentTimeMillis());
            tx.put("delta", delta);
            tx.put("reason", reason == null ? "" : reason);
            tx.put("source", source == null ? "" : source);
            tx.put("balance_after", Math.max(0, balance() + delta));
            trimmed.put(tx);
        } catch (Exception ignored) {}
        editor.putString(KEY_LEDGER, trimmed.toString());
    }

    private void loadConfig() {
        try {
            JSONObject root = new JSONObject(readAsset("game/economy.json"));
            JSONObject map = root.getJSONObject("rewards");
            java.util.Iterator<String> keys = map.keys();
            while (keys.hasNext()) {
                String key = keys.next();
                rewards.put(key, Math.max(0, map.optInt(key, 0)));
            }
        } catch (Exception e) {
            throw new IllegalStateException("Economy config failed to load", e);
        }
    }

    private String readAsset(String path) throws Exception {
        try (InputStream in = context.getAssets().open(path);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) != -1) out.write(buffer, 0, read);
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }
}
