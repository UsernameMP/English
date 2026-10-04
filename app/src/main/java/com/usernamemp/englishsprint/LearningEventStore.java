package com.usernamemp.englishsprint;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

/** Bounded, privacy-safe queue for future opt-in account sync and model calibration. */
public final class LearningEventStore {
    private static final String PREFS = "english_sprint_learning_events";
    private static final String KEY_EVENTS = "events_v1";
    private static final int MAX_EVENTS = 1000;
    private final SharedPreferences prefs;

    public LearningEventStore(Context context) {
        prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public synchronized void record(Question question, boolean correct, long durationMs, String packId) {
        JSONArray previous = events();
        JSONArray next = new JSONArray();
        int start = Math.max(0, previous.length() - (MAX_EVENTS - 1));
        for (int i = start; i < previous.length(); i++) {
            try { next.put(previous.getJSONObject(i)); } catch (Exception ignored) {}
        }
        try {
            JSONObject event = new JSONObject();
            event.put("schema_version", 1);
            event.put("event_id", UUID.randomUUID().toString());
            event.put("occurred_at_ms", System.currentTimeMillis());
            event.put("pack_id", packId);
            event.put("question_id", question.id);
            event.put("interaction", question.interaction);
            event.put("correct", correct);
            event.put("duration_bucket", durationBucket(durationMs));
            JSONArray knowledge = new JSONArray();
            for (KnowledgeRef ref : question.knowledge) knowledge.put(ref.id);
            event.put("knowledge_ids", knowledge);
            next.put(event);
            prefs.edit().putString(KEY_EVENTS, next.toString()).apply();
        } catch (Exception ignored) {}
    }

    public synchronized String exportPending() {
        JSONObject envelope = new JSONObject();
        try {
            envelope.put("schema_version", 1);
            envelope.put("events", events());
        } catch (Exception ignored) {}
        return envelope.toString();
    }

    public synchronized void acknowledge(Set<String> eventIds) {
        if (eventIds == null || eventIds.isEmpty()) return;
        JSONArray previous = events();
        JSONArray next = new JSONArray();
        for (int i = 0; i < previous.length(); i++) {
            try {
                JSONObject event = previous.getJSONObject(i);
                if (!eventIds.contains(event.optString("event_id", ""))) next.put(event);
            } catch (Exception ignored) {}
        }
        prefs.edit().putString(KEY_EVENTS, next.toString()).apply();
    }

    public int queuedCount() { return events().length(); }

    private JSONArray events() {
        try { return new JSONArray(prefs.getString(KEY_EVENTS, "[]")); }
        catch (Exception e) { return new JSONArray(); }
    }

    private String durationBucket(long durationMs) {
        if (durationMs < 5000L) return "under_5s";
        if (durationMs < 15000L) return "5_to_15s";
        if (durationMs < 45000L) return "15_to_45s";
        return "over_45s";
    }
}
