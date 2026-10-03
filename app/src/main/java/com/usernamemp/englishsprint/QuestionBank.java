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
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;

public final class QuestionBank {
    private static final String CATALOG_ASSET = "content/catalog.json";

    private static List<Question> cache = Collections.emptyList();
    private static List<String> skills = Collections.emptyList();
    private static Map<String, KnowledgeUnit> knowledgeUnits = Collections.emptyMap();
    private static KnowledgeAtlas knowledgeAtlas;
    private static ContentPack currentPack;

    private QuestionBank() {}

    public static synchronized void init(Context context) {
        if (!cache.isEmpty()) return;
        try {
            JSONObject catalog = new JSONObject(readAsset(context, CATALOG_ASSET));
            String defaultPackId = catalog.getString("default_pack");
            JSONArray packs = catalog.getJSONArray("packs");

            JSONObject catalogPack = null;
            for (int i = 0; i < packs.length(); i++) {
                JSONObject candidate = packs.getJSONObject(i);
                if (defaultPackId.equals(candidate.getString("id"))) {
                    catalogPack = candidate;
                    break;
                }
            }
            if (catalogPack == null) {
                throw new IllegalStateException("Default content pack not found: " + defaultPackId);
            }

            EntitlementStore entitlements = new EntitlementStore(context);
            if (!entitlements.canAccessPack(defaultPackId)) {
                throw new IllegalStateException("No entitlement for content pack: " + defaultPackId);
            }

            String asset = catalogPack.getString("asset");
            JSONObject bank = new JSONObject(readAsset(context, asset));
            JSONObject packJson = bank.getJSONObject("pack");
            currentPack = parsePack(packJson, asset);

            LinkedHashMap<String, KnowledgeUnit> units = new LinkedHashMap<>();
            JSONArray unitArray = bank.getJSONArray("knowledge_units");
            List<String> legacySkills = new ArrayList<>();
            for (int i = 0; i < unitArray.length(); i++) {
                JSONObject u = unitArray.getJSONObject(i);
                Map<String, String> labels = parseStringMap(u.optJSONObject("labels"));
                KnowledgeUnit unit = new KnowledgeUnit(
                        u.getString("id"),
                        u.optString("kind", "concept"),
                        u.optString("legacy_skill", ""),
                        labels
                );
                if (units.containsKey(unit.id)) {
                    throw new IllegalStateException("Duplicate knowledge unit: " + unit.id);
                }
                units.put(unit.id, unit);
                if (!unit.legacySkill.isEmpty() && !legacySkills.contains(unit.legacySkill)) {
                    legacySkills.add(unit.legacySkill);
                }
            }

            knowledgeAtlas = new KnowledgeAtlas(context, units.keySet());

            JSONArray array = bank.getJSONArray("questions");
            List<Question> loaded = new ArrayList<>();

            for (int i = 0; i < array.length(); i++) {
                JSONObject o = array.getJSONObject(i);

                JSONArray sk = o.optJSONArray("skills");
                List<String> questionSkills = new ArrayList<>();
                if (sk != null) {
                    for (int j = 0; j < sk.length(); j++) questionSkills.add(sk.getString(j));
                }

                JSONArray knowledgeJson = o.getJSONArray("knowledge");
                List<KnowledgeRef> knowledge = new ArrayList<>();
                for (int j = 0; j < knowledgeJson.length(); j++) {
                    JSONObject ref = knowledgeJson.getJSONObject(j);
                    String id = ref.getString("id");
                    if (!units.containsKey(id)) {
                        throw new IllegalStateException("Unknown knowledge unit " + id + " in " + o.getString("id"));
                    }
                    knowledge.add(new KnowledgeRef(id, ref.optDouble("weight", 1.0)));
                }
                if (knowledge.isEmpty()) {
                    throw new IllegalStateException("Question has no knowledge unit: " + o.getString("id"));
                }

                List<String> prerequisites = new ArrayList<>();
                JSONArray prerequisiteJson = o.optJSONArray("prerequisites");
                if (prerequisiteJson != null) {
                    for (int j = 0; j < prerequisiteJson.length(); j++) {
                        String prerequisite = prerequisiteJson.getString(j);
                        if (!units.containsKey(prerequisite)) {
                            throw new IllegalStateException("Unknown prerequisite " + prerequisite
                                    + " in " + o.getString("id"));
                        }
                        if (!prerequisites.contains(prerequisite)) prerequisites.add(prerequisite);
                    }
                }
                if (prerequisites.isEmpty()) {
                    prerequisites.addAll(knowledgeAtlas.prerequisitesFor(knowledge));
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
                if (correctIndex < 0) {
                    throw new IllegalStateException("Unknown answer id in " + o.getString("id"));
                }

                JSONObject feedback = o.getJSONObject("feedback");
                JSONObject source = o.optJSONObject("source");
                JSONObject review = o.optJSONObject("review");

                loaded.add(new Question(
                        o.getString("id"),
                        o.optString("subject", currentPack.subject),
                        o.optInt("grade_min", currentPack.gradeMin),
                        o.optInt("grade_max", currentPack.gradeMax),
                        o.optString("interaction", "single_choice"),
                        questionSkills,
                        knowledge,
                        prerequisites,
                        mapType(o.optString("mode", "grammar")),
                        o.optInt("difficulty", 1),
                        o.getString("prompt"),
                        text,
                        options,
                        correctIndex,
                        localizedField(feedback, "short", Locale.getDefault()),
                        localizedField(feedback, "full", Locale.getDefault()),
                        localizedField(feedback, "rule", Locale.getDefault()),
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
            skills = Collections.unmodifiableList(legacySkills);
            knowledgeUnits = Collections.unmodifiableMap(units);
        } catch (Exception e) {
            throw new IllegalStateException("Content pack failed to load", e);
        }
    }

    public static ContentPack currentPack() {
        ensureInit();
        return currentPack;
    }

    public static List<Question> all() {
        ensureInit();
        return cache;
    }

    public static List<String> skills() {
        ensureInit();
        return skills;
    }

    public static List<String> knowledgeIds() {
        ensureInit();
        return new ArrayList<>(knowledgeUnits.keySet());
    }

    public static KnowledgeUnit knowledgeUnit(String id) {
        ensureInit();
        return knowledgeUnits.get(id);
    }

    public static List<String> prerequisitesForKnowledge(String id) {
        ensureInit();
        return knowledgeAtlas == null ? Collections.emptyList() : knowledgeAtlas.prerequisitesFor(id);
    }

    public static List<KnowledgeRelation> knowledgeRelations() {
        ensureInit();
        return knowledgeAtlas == null ? Collections.emptyList() : knowledgeAtlas.all();
    }

    public static String knowledgeLabel(String id, Locale locale) {
        KnowledgeUnit unit = knowledgeUnit(id);
        return unit == null ? id : unit.label(locale);
    }

    public static String legacySkillForKnowledge(String id) {
        KnowledgeUnit unit = knowledgeUnit(id);
        return unit == null ? "" : unit.legacySkill;
    }

    public static String primaryKnowledgeForLegacy(String legacySkill) {
        ensureInit();
        for (KnowledgeUnit unit : knowledgeUnits.values()) {
            if (unit.legacySkill.equals(legacySkill)) return unit.id;
        }
        return legacySkill;
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

        pool.sort(Comparator.comparingDouble(q ->
                progress.masteryKnowledge(q.primaryKnowledgeId())
                        - Math.min(progress.recentMistakesKnowledge(q.primaryKnowledgeId()), 4) * 0.08));

        List<Question> result = new ArrayList<>();
        List<String> recentKnowledge = new ArrayList<>();
        for (Question q : pool) {
            String primary = q.primaryKnowledgeId();
            int same = 0;
            for (String id : recentKnowledge) if (id.equals(primary)) same++;
            if (same >= 2) continue;
            result.add(q);
            recentKnowledge.add(primary);
            if (recentKnowledge.size() > 7) recentKnowledge.remove(0);
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

    private static ContentPack parsePack(JSONObject pack, String asset) throws Exception {
        return new ContentPack(
                pack.getString("id"),
                asset,
                pack.getString("subject"),
                pack.getInt("grade_min"),
                pack.getInt("grade_max"),
                pack.optString("competition", ""),
                pack.optString("region", ""),
                pack.optString("season", ""),
                parseStringMap(pack.optJSONObject("title")),
                parseStringMap(pack.optJSONObject("subtitle"))
        );
    }

    private static String localizedField(JSONObject object, String key, Locale locale) {
        Object value = object.opt(key);
        if (value instanceof JSONObject) {
            JSONObject localized = (JSONObject) value;
            String lang = locale == null ? "en" : locale.getLanguage();
            String text = localized.optString(lang, "");
            if (text.isEmpty()) text = localized.optString("en", "");
            if (text.isEmpty()) text = localized.optString("ru", "");
            if (text.isEmpty()) {
                java.util.Iterator<String> keys = localized.keys();
                if (keys.hasNext()) text = localized.optString(keys.next(), "");
            }
            return text;
        }
        return object.optString(key, "");
    }

    private static Map<String, String> parseStringMap(JSONObject object) {
        LinkedHashMap<String, String> result = new LinkedHashMap<>();
        if (object == null) return result;
        java.util.Iterator<String> keys = object.keys();
        while (keys.hasNext()) {
            String key = keys.next();
            result.put(key, object.optString(key, ""));
        }
        return result;
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
