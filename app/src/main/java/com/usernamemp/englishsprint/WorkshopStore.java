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
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class WorkshopStore {
    private static final String PREFS = "english_sprint_workshop";
    private final Context context;
    private final SharedPreferences prefs;
    private final EconomyStore economy;
    private final List<WorkshopItem> items = new ArrayList<>();

    public WorkshopStore(Context context, EconomyStore economy) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        this.economy = economy;
        load();
        reconcilePurchases();
    }

    public List<WorkshopItem> items() { return Collections.unmodifiableList(items); }
    public int builtCount() { return owned().size(); }
    public boolean isBuilt(WorkshopItem item) { return owned().contains(item.id); }

    public synchronized String build(WorkshopItem item, int playerLevel) {
        if (isBuilt(item)) return "owned";
        if (playerLevel < item.requiredLevel) return "level";
        if (!economy.spend(item.priceCrystals, "workshop_build", item.id)) return "crystals";
        Set<String> next = owned();
        next.add(item.id);
        prefs.edit().putStringSet("built", next).apply();
        return "built";
    }

    private void reconcilePurchases() {
        Set<String> next = owned();
        boolean changed = false;
        for (WorkshopItem item : items) {
            if (!next.contains(item.id) && economy.hasDebit("workshop_build", item.id)) {
                next.add(item.id);
                changed = true;
            }
        }
        if (changed) prefs.edit().putStringSet("built", next).apply();
    }

    private Set<String> owned() {
        Set<String> stored = prefs.getStringSet("built", Collections.emptySet());
        return new HashSet<>(stored == null ? Collections.emptySet() : stored);
    }

    private void load() {
        try {
            JSONObject root = new JSONObject(readAsset("game/workshop_catalog.json"));
            JSONArray array = root.getJSONArray("structures");
            for (int i = 0; i < array.length(); i++) {
                JSONObject o = array.getJSONObject(i);
                items.add(new WorkshopItem(o.getString("id"), o.optString("icon", "◇"),
                        o.getInt("price_crystals"), o.getInt("required_level"),
                        stringMap(o.getJSONObject("name")), stringMap(o.getJSONObject("description"))));
            }
        } catch (Exception e) {
            throw new IllegalStateException("Workshop catalog failed to load", e);
        }
    }

    private Map<String, String> stringMap(JSONObject source) {
        Map<String, String> result = new LinkedHashMap<>();
        java.util.Iterator<String> keys = source.keys();
        while (keys.hasNext()) { String key = keys.next(); result.put(key, source.optString(key, "")); }
        return result;
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
