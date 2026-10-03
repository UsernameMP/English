package com.usernamemp.englishsprint;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Random;
import java.util.Set;

public final class QuestionBank {
    private static final String ASSET = "content/english_g5_vso.json";
    private static List<Question> cache = Collections.emptyList();
    private static List<String> skills = Collections.emptyList();

    private QuestionBank() {}

    public static synchronized void init(Context context) {
        if (!cache.isEmpty()) return;
        try {
            String json = readAsset(context, ASSET);
            JSONObject bank = new JSONObject(json);
            JSONArray array = bank.getJSONArray("questions");
            List<Question> loaded = new ArrayList<>();
            Set<String> skillSet = new LinkedHashSet<>();

            for (int i = 0; i < array.length(); i++) {
                JSONObject o = array.getJSONObject(i);
                JSONArray sk = o.getJSONArray("skills");
                List<String> questionSkills = new ArrayList<>();
                for (int j = 0; j < sk.length(); j++) {
                    String s = sk.getString(j);
                    questionSkills.add(s);
                    skillSet.add(s);
                }

                JSONObject stimulus = o.optJSONObject("stimulus");
                String text = stimulus == null || stimulus.isNull("text") ? "" : stimulus.optString("text", "");
                String audio = stimulus == null || stimulus.isNull("audio") ? "" : stimulus.optString("audio", "");
                String script = stimulus == null || stimulus.isNull("script") ? "" : stimulus.optString("script", "");

                JSONArray optionArray = o.getJSONArray("options");
                List<String> options = new ArrayList<>();
                List<String> optionIds = new ArrayList<>();
                for (int j = 0; j < optionArray.length(); j++) {
                    JSONObject option = optionArray.getJSONObject(j);
                    optionIds.add(option.getString("id"));
                    options.add(option.getString("text"));
                }

                JSONArray answers = o.getJSONArray("answer");
                String answerId = answers.getString(0);
                int correctIndex = optionIds.indexOf(answerId);
                if (correctIndex < 0) throw new IllegalStateException("Unknown answer id in " + o.getString("id"));

                JSONObject feedback = o.getJSONObject("feedback");
                JSONObject source = o.optJSONObject("source");
                JSONObject review = o.optJSONObject("review");

                loaded.add(new Question(
                        o.getString("id"),
                        o.optString("subject", "english"),
                        o.optInt("grade_min", 5),
                        o.optInt("grade_max", 6),
                        o.optString("interaction", "single_choice"),
                        questionSkills,
                        mapType(o.optString("mode", "grammar")),
                        o.optInt("difficulty", 1),
                        o.getString("prompt"),
                        text,
                        options,
                        correctIndex,
                        feedback.optString("short", ""),
                        feedback.optString("full", ""),
                        feedback.optString("rule", ""),
                        o.isNull("evidence") ? "" : o.optString("evidence", ""),
                        audio,
                        script,
                        source == null ? "" : source.optString("competition", ""),
                        source == null ? "" : source.optString("region", ""),
                        source == null ? "" : source.optString("year", ""),
                        review != null && "verified".equals(review.optString("status", ""))
                ));
            }

            cache = Collections.unmodifiableList(loaded);
            List<String> skillList = new ArrayList<>(skillSet);
            skillList.sort(String::compareTo);
            skills = Collections.unmodifiableList(skillList);
        } catch (Exception e) {
            throw new IllegalStateException("Question bank failed to load: " + ASSET, e);
        }
    }

    public static List<Question> all() {
        ensureInit();
        return cache;
    }

    public static List<String> skills() {
        ensureInit();
        return skills;
    }

    public static List<Question> byType(Question.Type type) {
        ensureInit();
        List<Question> result = new ArrayList<>();
        for (Question q : cache) if (q.type == type) result.add(q);
        return result;
    }

    public static List<Question> adaptiveSession(ProgressStore progress, int count, long seed) {
        ensureInit();
        Random random = new Random(seed);
        List<Question> pool = new ArrayList<>(cache);
        Collections.shuffle(pool, random);

        // Weak skills are prioritised. Recent mistakes get an extra boost.
        pool.sort(Comparator.comparingDouble(q ->
                progress.mastery(q.skill) - Math.min(progress.recentMistakes(q.skill), 4) * 0.08));

        List<Question> result = new ArrayList<>();
        List<String> recentSkills = new ArrayList<>();
        for (Question q : pool) {
            int same = 0;
            for (String s : recentSkills) if (s.equals(q.skill)) same++;
            if (same >= 2) continue;
            result.add(q);
            recentSkills.add(q.skill);
            if (recentSkills.size() > 7) recentSkills.remove(0);
            if (result.size() >= count) break;
        }
        return result;
    }

    public static List<Question> sprint(int count, long seed) {
        ensureInit();
        List<Question> result = new ArrayList<>();
        addRandomFrom(result, Question.Type.LISTENING, 3, seed + 1);
        addRandomFrom(result, Question.Type.READING, 4, seed + 2);
        addRandomFrom(result, Question.Type.GRAMMAR, 10, seed + 3);
        addRandomFrom(result, Question.Type.STORY, 5, seed + 4);
        Collections.shuffle(result, new Random(seed + 5));
        if (result.size() > count) return new ArrayList<>(result.subList(0, count));
        return result;
    }

    private static void addRandomFrom(List<Question> out, Question.Type type, int count, long seed) {
        List<Question> list = byType(type);
        Collections.shuffle(list, new Random(seed));
        out.addAll(list.subList(0, Math.min(count, list.size())));
    }

    private static Question.Type mapType(String mode) {
        switch (mode) {
            case "reading": return Question.Type.READING;
            case "listening": return Question.Type.LISTENING;
            case "story": return Question.Type.STORY;
            default: return Question.Type.GRAMMAR;
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

    private static void ensureInit() {
        if (cache.isEmpty()) throw new IllegalStateException("QuestionBank.init(context) must be called first");
    }
}
