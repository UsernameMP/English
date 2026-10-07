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
import java.util.HashSet;
import java.util.Set;
import java.security.MessageDigest;

public final class QuestionBank {
    private static final String CATALOG_ASSET = "content/catalog.json";
    private static final String KNOWLEDGE_ASSET = "content/knowledge_units.json";
    private static final String BLUEPRINT_ASSET = "content/competition_blueprints.json";

    private static List<Question> cache = Collections.emptyList();
    private static List<String> skills = Collections.emptyList();
    private static Map<String, KnowledgeUnit> knowledgeUnits = Collections.emptyMap();
    private static List<String> currentKnowledgeIds = Collections.emptyList();
    private static KnowledgeAtlas knowledgeAtlas;
    private static ContentPack currentPack;
    private static List<ContentPack> availablePacks = Collections.emptyList();
    private static Map<String, Double> blueprintWeights = Collections.emptyMap();

    private QuestionBank() {}

    public static synchronized void init(Context context) {
        if (!cache.isEmpty()) return;
        try {
            JSONObject catalog = new JSONObject(readAsset(context, CATALOG_ASSET));
            String defaultPackId = catalog.getString("default_pack");
            JSONArray packs = catalog.getJSONArray("packs");

            EntitlementStore entitlements = new EntitlementStore(context);
            List<ContentPack> accessible = new ArrayList<>();
            LinkedHashMap<String, KnowledgeUnit> globalUnits = loadKnowledgeRegistry(context);
            Set<String> globalUnitIds = globalUnits.keySet();
            for (int i = 0; i < packs.length(); i++) {
                JSONObject candidate = packs.getJSONObject(i);
                if (!candidate.optBoolean("enabled", true)) continue;
                String candidateId = candidate.getString("id");
                String candidateRaw = readAsset(context, candidate.getString("asset"));
                verifyPackIntegrity(candidate, candidateRaw);
                JSONObject candidateBank = new JSONObject(candidateRaw);
                if (entitlements.accessDecision(
                        candidateId,
                        candidate.optString("subject", ""),
                        candidate.optInt("grade_min", 1),
                        candidate.optInt("grade_max", 12),
                        candidate.optString("competition", ""),
                        candidate.optString("season", "")).allowed) {
                    accessible.add(parsePack(candidateBank.getJSONObject("pack"), candidate.getString("asset")));
                }
            }
            if (accessible.isEmpty()) throw new IllegalStateException("No accessible content packs");
            availablePacks = Collections.unmodifiableList(accessible);

            String selectedPackId = context.getSharedPreferences("english_sprint_settings", Context.MODE_PRIVATE)
                    .getString("selected_pack", defaultPackId);
            boolean selectedAccessible = false;
            for (ContentPack pack : accessible) if (pack.id.equals(selectedPackId)) selectedAccessible = true;
            if (!selectedAccessible) selectedPackId = defaultPackId;

            JSONObject catalogPack = null;
            for (int i = 0; i < packs.length(); i++) {
                JSONObject candidate = packs.getJSONObject(i);
                if (selectedPackId.equals(candidate.getString("id"))) {
                    catalogPack = candidate;
                    break;
                }
            }
            if (catalogPack == null) {
                throw new IllegalStateException("Selected content pack not found: " + selectedPackId);
            }

            if (!entitlements.canAccessPack(
                    selectedPackId,
                    catalogPack.optString("subject", ""),
                    catalogPack.optInt("grade_min", 1),
                    catalogPack.optInt("grade_max", 12),
                    catalogPack.optString("competition", ""),
                    catalogPack.optString("season", ""))) {
                throw new IllegalStateException("No entitlement for content pack: " + selectedPackId);
            }

            String asset = catalogPack.getString("asset");
            String bankRaw = readAsset(context, asset);
            verifyPackIntegrity(catalogPack, bankRaw);
            JSONObject bank = new JSONObject(bankRaw);
            JSONObject packJson = bank.getJSONObject("pack");
            currentPack = parsePack(packJson, asset);

            LinkedHashMap<String, KnowledgeUnit> units = globalUnits;
            List<String> legacySkills = new ArrayList<>();
            for (KnowledgeUnit unit : units.values()) {
                if (!unit.legacySkill.isEmpty() && !legacySkills.contains(unit.legacySkill)) {
                    legacySkills.add(unit.legacySkill);
                }
            }

            knowledgeAtlas = new KnowledgeAtlas(context, globalUnitIds);
            blueprintWeights = loadBlueprint(context, selectedPackId, globalUnitIds);

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

                JSONArray optionArray = o.optJSONArray("options");
                List<String> options = new ArrayList<>();
                List<String> optionIds = new ArrayList<>();
                if (optionArray != null) {
                    for (int j = 0; j < optionArray.length(); j++) {
                        JSONObject option = optionArray.getJSONObject(j);
                        optionIds.add(option.getString("id"));
                        options.add(option.getString("text"));
                    }
                }

                List<String> matchingLeft = new ArrayList<>();
                List<String> matchingRight = new ArrayList<>();
                List<String> matchingLeftIds = new ArrayList<>();
                List<String> matchingRightIds = new ArrayList<>();
                JSONArray matchingLeftJson = o.optJSONArray("matching_left");
                JSONArray matchingRightJson = o.optJSONArray("matching_right");
                if (matchingLeftJson != null) {
                    for (int j = 0; j < matchingLeftJson.length(); j++) {
                        JSONObject item = matchingLeftJson.getJSONObject(j);
                        matchingLeftIds.add(item.getString("id"));
                        matchingLeft.add(item.getString("text"));
                    }
                }
                if (matchingRightJson != null) {
                    for (int j = 0; j < matchingRightJson.length(); j++) {
                        JSONObject item = matchingRightJson.getJSONObject(j);
                        matchingRightIds.add(item.getString("id"));
                        matchingRight.add(item.getString("text"));
                    }
                }

                JSONArray answers = o.getJSONArray("answer");
                List<String> acceptedAnswers = new ArrayList<>();
                for (int j = 0; j < answers.length(); j++) acceptedAnswers.add(answers.getString(j));
                String interaction = o.optString("interaction", "single_choice");
                List<Integer> correctIndices = new ArrayList<>();
                if ("single_choice".equals(interaction) || "multi_choice".equals(interaction)
                        || "sequence".equals(interaction)) {
                    for (String answer : acceptedAnswers) {
                        int index = optionIds.indexOf(answer);
                        if (index < 0) throw new IllegalStateException("Unknown answer id in " + o.getString("id"));
                        if (!correctIndices.contains(index)) correctIndices.add(index);
                    }
                }
                List<Integer> matchingAnswer = new ArrayList<>();
                if ("matching".equals(interaction)) {
                    for (String leftId : matchingLeftIds) matchingAnswer.add(-1);
                    for (String answer : acceptedAnswers) {
                        String[] pair = answer.split(":", 2);
                        if (pair.length != 2) throw new IllegalStateException("Invalid matching pair in " + o.getString("id"));
                        int leftIndex = matchingLeftIds.indexOf(pair[0]);
                        int rightIndex = matchingRightIds.indexOf(pair[1]);
                        if (leftIndex < 0 || rightIndex < 0) throw new IllegalStateException("Unknown matching id in " + o.getString("id"));
                        matchingAnswer.set(leftIndex, rightIndex);
                    }
                    if (matchingAnswer.contains(-1)) throw new IllegalStateException("Incomplete matching answer in " + o.getString("id"));
                }
                int correctIndex = correctIndices.size() == 1 ? correctIndices.get(0) : -1;

                JSONObject answerPolicy = o.optJSONObject("answer_policy");
                double tolerance = answerPolicy == null ? 0.0 : answerPolicy.optDouble("tolerance", 0.0);
                Double minimum = answerPolicy != null && answerPolicy.has("min")
                        ? answerPolicy.getDouble("min") : null;
                Double maximum = answerPolicy != null && answerPolicy.has("max")
                        ? answerPolicy.getDouble("max") : null;
                String unit = answerPolicy == null ? "" : answerPolicy.optString("unit", "");

                JSONObject feedback = o.getJSONObject("feedback");
                JSONObject source = o.optJSONObject("source");
                JSONObject review = o.optJSONObject("review");

                loaded.add(new Question(
                        o.getString("id"),
                        o.optString("subject", currentPack.subject),
                        o.optInt("grade_min", currentPack.gradeMin),
                        o.optInt("grade_max", currentPack.gradeMax),
                        interaction,
                        questionSkills,
                        knowledge,
                        prerequisites,
                        mapType(o.optString("mode", "grammar")),
                        o.optInt("difficulty", 1),
                        o.getString("prompt"),
                        text,
                        options,
                        matchingLeft,
                        matchingRight,
                        matchingAnswer,
                        correctIndex,
                        correctIndices,
                        acceptedAnswers,
                        tolerance,
                        minimum,
                        maximum,
                        unit,
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
            LinkedHashMap<String, Boolean> assessed = new LinkedHashMap<>();
            for (Question question : loaded) {
                for (KnowledgeRef ref : question.knowledge) assessed.put(ref.id, true);
            }
            currentKnowledgeIds = Collections.unmodifiableList(new ArrayList<>(assessed.keySet()));
        } catch (Exception e) {
            throw new IllegalStateException("Content pack failed to load", e);
        }
    }

    public static ContentPack currentPack() {
        ensureInit();
        return currentPack;
    }

    public static List<ContentPack> availablePacks() {
        ensureInit();
        return availablePacks;
    }

    public static synchronized void selectPack(Context context, String packId) {
        boolean allowed = false;
        for (ContentPack pack : availablePacks) if (pack.id.equals(packId)) allowed = true;
        if (!allowed) throw new IllegalArgumentException("Pack is not accessible: " + packId);
        context.getSharedPreferences("english_sprint_settings", Context.MODE_PRIVATE)
                .edit().putString("selected_pack", packId).apply();
        cache = Collections.emptyList();
        skills = Collections.emptyList();
        knowledgeUnits = Collections.emptyMap();
        currentKnowledgeIds = Collections.emptyList();
        knowledgeAtlas = null;
        blueprintWeights = Collections.emptyMap();
        currentPack = null;
        init(context);
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
        return new ArrayList<>(currentKnowledgeIds);
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

        pool.sort(Comparator.comparingDouble(q -> adaptivePriority(q, progress)));

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

    public static List<String> recommendedKnowledge(ProgressStore progress, int count) {
        List<Question> questions = adaptiveSession(progress, Math.max(count * 3, count), 42L);
        List<String> result = new ArrayList<>();
        for (Question q : questions) {
            for (String prerequisite : q.prerequisites) {
                if (progress.masteryKnowledge(prerequisite) < 0.65 && !result.contains(prerequisite)) {
                    result.add(prerequisite);
                    if (result.size() >= count) return result;
                }
            }
            String assessed = q.primaryKnowledgeId();
            if (!result.contains(assessed)) result.add(assessed);
            if (result.size() >= count) return result;
        }
        return result;
    }

    private static double adaptivePriority(Question q, ProgressStore progress) {
        double direct = progress.masteryKnowledge(q.primaryKnowledgeId())
                - Math.min(progress.recentMistakesKnowledge(q.primaryKnowledgeId()), 4) * 0.08;
        double blocked = 0.0;
        for (String prerequisite : q.prerequisites) {
            blocked += Math.max(0.0, 0.65 - progress.masteryKnowledge(prerequisite));
        }
        if (!q.prerequisites.isEmpty()) blocked /= q.prerequisites.size();
        double dueBoost = progress.isDue(q.primaryKnowledgeId()) ? 0.22 : 0.0;
        double targetWeight = blueprintWeights.getOrDefault(q.primaryKnowledgeId(), 0.0);
        return direct + blocked * 1.5 - dueBoost - targetWeight * 0.25;
    }

    public static double blueprintWeight(String knowledgeId) {
        ensureInit();
        return blueprintWeights.getOrDefault(knowledgeId, 0.0);
    }

    public static Map<String, Double> blueprintWeights() {
        ensureInit();
        return new LinkedHashMap<>(blueprintWeights);
    }

    private static void verifyPackIntegrity(JSONObject catalogPack, String raw) throws Exception {
        String expected = catalogPack.optString("sha256", "");
        String version = catalogPack.optString("content_version", "");
        if (expected.isEmpty() || version.isEmpty()) {
            throw new IllegalStateException("Pack integrity metadata is missing: " + catalogPack.optString("id"));
        }
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        StringBuilder actual = new StringBuilder();
        for (byte b : digest.digest(raw.getBytes(StandardCharsets.UTF_8))) actual.append(String.format(Locale.ROOT, "%02x", b));
        if (!expected.equals(actual.toString())) {
            throw new IllegalStateException("Pack digest mismatch: " + catalogPack.optString("id"));
        }
        JSONObject bank = new JSONObject(raw);
        if (!version.equals(bank.optString("content_version", ""))) {
            throw new IllegalStateException("Pack content version mismatch: " + catalogPack.optString("id"));
        }
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

    private static LinkedHashMap<String, KnowledgeUnit> loadKnowledgeRegistry(Context context) throws Exception {
        JSONObject root = new JSONObject(readAsset(context, KNOWLEDGE_ASSET));
        JSONArray array = root.getJSONArray("knowledge_units");
        LinkedHashMap<String, KnowledgeUnit> units = new LinkedHashMap<>();
        for (int i = 0; i < array.length(); i++) {
            JSONObject u = array.getJSONObject(i);
            KnowledgeUnit unit = new KnowledgeUnit(
                    u.getString("id"), u.optString("kind", "concept"),
                    u.optString("legacy_skill", ""), parseStringMap(u.optJSONObject("labels")));
            if (units.put(unit.id, unit) != null) {
                throw new IllegalStateException("Duplicate global knowledge unit: " + unit.id);
            }
        }
        return units;
    }

    private static Map<String, Double> loadBlueprint(Context context, String packId,
                                                      Set<String> knownIds) throws Exception {
        JSONObject root = new JSONObject(readAsset(context, BLUEPRINT_ASSET));
        JSONArray blueprints = root.getJSONArray("blueprints");
        LinkedHashMap<String, Double> weights = new LinkedHashMap<>();
        for (int i = 0; i < blueprints.length(); i++) {
            JSONObject blueprint = blueprints.getJSONObject(i);
            if (!packId.equals(blueprint.getString("pack_id"))) continue;
            JSONArray coverage = blueprint.getJSONArray("coverage");
            for (int j = 0; j < coverage.length(); j++) {
                JSONObject row = coverage.getJSONObject(j);
                String id = row.getString("knowledge_id");
                if (!knownIds.contains(id)) throw new IllegalStateException("Unknown blueprint unit: " + id);
                weights.put(id, row.getDouble("weight"));
            }
            break;
        }
        if (weights.isEmpty()) throw new IllegalStateException("No competition blueprint for " + packId);
        return Collections.unmodifiableMap(weights);
    }

    private static Question.Type mapType(String mode) {
        switch (mode) {
            case "reading": return Question.Type.READING;
            case "listening": return Question.Type.LISTENING;
            case "story": return Question.Type.STORY;
            case "grammar": return Question.Type.GRAMMAR;
            default: return Question.Type.PRACTICE;
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
