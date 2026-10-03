package com.usernamemp.englishsprint;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;
import java.util.Set;

public final class DictionaryStore {
    private static final String ASSET = "content/dictionary_en.json";
    private static final String PREFS = "english_sprint_dictionary";
    private static final String SAVED = "saved_lemmas";

    private final Context context;
    private final SharedPreferences prefs;
    private final Map<String, DictionaryEntry> byLemma = new LinkedHashMap<>();
    private final Map<String, DictionaryEntry> byForm = new HashMap<>();

    public DictionaryStore(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        load();
    }

    public DictionaryEntry lookup(String token) {
        if (token == null) return null;
        return byForm.get(normalize(token));
    }

    public boolean isSaved(DictionaryEntry entry) {
        return savedLemmaSet().contains(entry.lemma);
    }

    public void save(DictionaryEntry entry) {
        Set<String> saved = savedLemmaSet();
        saved.add(entry.lemma);
        prefs.edit().putStringSet(SAVED, saved).apply();
    }

    public void remove(DictionaryEntry entry) {
        Set<String> saved = savedLemmaSet();
        saved.remove(entry.lemma);
        prefs.edit().putStringSet(SAVED, saved).apply();
    }

    public int savedCount() {
        return savedLemmaSet().size();
    }

    public List<DictionaryEntry> savedEntries() {
        List<DictionaryEntry> result = new ArrayList<>();
        for (String lemma : savedLemmaSet()) {
            DictionaryEntry entry = byLemma.get(lemma);
            if (entry != null) result.add(entry);
        }
        result.sort(Comparator.comparing(e -> e.lemma));
        return result;
    }

    public List<Question> mixVocabulary(List<Question> base, int maxQuestions, long seed) {
        List<Question> result = new ArrayList<>(base);
        List<DictionaryEntry> saved = savedEntries();
        if (saved.isEmpty() || maxQuestions <= 0) return result;

        Random random = new Random(seed);
        Collections.shuffle(saved, random);
        int count = Math.min(maxQuestions, Math.min(saved.size(), 2));
        for (int i = 0; i < count; i++) {
            Question vocab = vocabularyQuestion(saved.get(i), random);
            int min = Math.min(3 + i * 4, result.size());
            int max = Math.min(result.size(), min + 3);
            int position = min >= max ? max : min + random.nextInt(max - min + 1);
            result.add(position, vocab);
        }
        return result;
    }

    private Question vocabularyQuestion(DictionaryEntry target, Random random) {
        Locale locale = Locale.getDefault();
        List<DictionaryEntry> distractorPool = new ArrayList<>(byLemma.values());
        distractorPool.remove(target);
        Collections.shuffle(distractorPool, random);

        List<String> optionTexts = new ArrayList<>();
        optionTexts.add(target.translation(locale));
        for (DictionaryEntry entry : distractorPool) {
            String value = entry.translation(locale);
            if (!optionTexts.contains(value)) optionTexts.add(value);
            if (optionTexts.size() >= 3) break;
        }

        int correctIndex = 0;
        for (int i = optionTexts.size() - 1; i > 0; i--) {
            int j = random.nextInt(i + 1);
            Collections.swap(optionTexts, i, j);
        }
        correctIndex = optionTexts.indexOf(target.translation(locale));

        List<String> tags = new ArrayList<>();
        tags.add("vocabulary");
        List<KnowledgeRef> knowledge = new ArrayList<>();
        knowledge.add(new KnowledgeRef("ENG.VOCAB.PERSONAL", 1.0));

        String full = target.definition(locale);
        if (!target.example.isEmpty()) full += "\n" + target.example;

        return new Question(
                "vocab_" + target.lemma,
                "english",
                5,
                11,
                "single_choice",
                tags,
                knowledge,
                Question.Type.GRAMMAR,
                1,
                context.getString(R.string.vocab_prompt, target.lemma),
                "",
                optionTexts,
                correctIndex,
                target.lemma + " — " + target.translation(locale),
                full,
                context.getString(R.string.personal_dictionary),
                "",
                "",
                "",
                "",
                "",
                "",
                true
        );
    }

    private void load() {
        try {
            JSONObject root = new JSONObject(readAsset(ASSET));
            JSONArray entries = root.getJSONArray("entries");
            for (int i = 0; i < entries.length(); i++) {
                JSONObject o = entries.getJSONObject(i);
                List<String> forms = new ArrayList<>();
                JSONArray formArray = o.optJSONArray("forms");
                if (formArray != null) {
                    for (int j = 0; j < formArray.length(); j++) forms.add(formArray.getString(j));
                }

                DictionaryEntry entry = new DictionaryEntry(
                        o.getString("lemma"),
                        forms,
                        o.optString("phonetic", ""),
                        o.optString("example", ""),
                        stringMap(o.optJSONObject("translation")),
                        stringMap(o.optJSONObject("definition"))
                );
                byLemma.put(entry.lemma, entry);
                byForm.put(normalize(entry.lemma), entry);
                for (String form : forms) byForm.put(normalize(form), entry);
            }
        } catch (Exception e) {
            throw new IllegalStateException("Dictionary asset failed to load", e);
        }
    }

    private Set<String> savedLemmaSet() {
        Set<String> existing = prefs.getStringSet(SAVED, Collections.emptySet());
        return new HashSet<>(existing == null ? Collections.emptySet() : existing);
    }

    private Map<String, String> stringMap(JSONObject object) {
        Map<String, String> result = new LinkedHashMap<>();
        if (object == null) return result;
        java.util.Iterator<String> keys = object.keys();
        while (keys.hasNext()) {
            String key = keys.next();
            result.put(key, object.optString(key, ""));
        }
        return result;
    }

    private String normalize(String raw) {
        String s = raw.toLowerCase(Locale.US).trim();
        s = s.replaceAll("^[^a-z']+|[^a-z']+$", "");
        if (s.endsWith("'s") && s.length() > 2) s = s.substring(0, s.length() - 2);
        return s;
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
