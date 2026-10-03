package com.usernamemp.englishsprint;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class KnowledgeAtlas {
    private final List<KnowledgeRelation> relations = new ArrayList<>();
    private final Map<String, List<KnowledgeRelation>> byFrom = new HashMap<>();

    public KnowledgeAtlas(Context context, Set<String> knownIds) {
        try {
            JSONObject root = new JSONObject(readAsset(context, "content/knowledge_atlas.json"));
            JSONArray array = root.getJSONArray("relations");
            for (int i = 0; i < array.length(); i++) {
                JSONObject o = array.getJSONObject(i);
                KnowledgeRelation relation = new KnowledgeRelation(
                        o.getString("from"), o.getString("type"), o.getString("to"));
                if (!knownIds.contains(relation.from) || !knownIds.contains(relation.to)) {
                    throw new IllegalStateException("Atlas relation references unknown unit: "
                            + relation.from + " -> " + relation.to);
                }
                relations.add(relation);
                byFrom.computeIfAbsent(relation.from, k -> new ArrayList<>()).add(relation);
            }
            validateRequiresAcyclic(knownIds);
        } catch (Exception e) {
            throw new IllegalStateException("Knowledge Atlas failed to load", e);
        }
    }

    public List<KnowledgeRelation> all() {
        return Collections.unmodifiableList(relations);
    }

    public List<String> related(String from, String type) {
        List<String> result = new ArrayList<>();
        for (KnowledgeRelation r : byFrom.getOrDefault(from, Collections.emptyList())) {
            if (type.equals(r.type)) result.add(r.to);
        }
        return result;
    }

    public List<String> prerequisitesFor(String knowledgeId) {
        LinkedHashSet<String> result = new LinkedHashSet<>();
        collectRequires(knowledgeId, result, new HashSet<>());
        return new ArrayList<>(result);
    }

    public List<String> prerequisitesFor(List<KnowledgeRef> assessed) {
        LinkedHashSet<String> result = new LinkedHashSet<>();
        for (KnowledgeRef ref : assessed) result.addAll(prerequisitesFor(ref.id));
        return new ArrayList<>(result);
    }

    private void collectRequires(String id, LinkedHashSet<String> out, Set<String> visiting) {
        if (!visiting.add(id)) return;
        for (KnowledgeRelation r : byFrom.getOrDefault(id, Collections.emptyList())) {
            if (!"requires".equals(r.type)) continue;
            collectRequires(r.to, out, visiting);
            out.add(r.to);
        }
        visiting.remove(id);
    }

    private void validateRequiresAcyclic(Set<String> ids) {
        Set<String> visiting = new HashSet<>();
        Set<String> done = new HashSet<>();
        for (String id : ids) dfs(id, visiting, done);
    }

    private void dfs(String id, Set<String> visiting, Set<String> done) {
        if (done.contains(id)) return;
        if (!visiting.add(id)) throw new IllegalStateException("requires cycle at " + id);
        for (KnowledgeRelation r : byFrom.getOrDefault(id, Collections.emptyList())) {
            if ("requires".equals(r.type)) dfs(r.to, visiting, done);
        }
        visiting.remove(id);
        done.add(id);
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
