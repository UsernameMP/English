package com.usernamemp.englishsprint;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;

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
import java.util.Locale;
import java.util.Map;
import java.util.Set;

public final class ShopStore {
    public static final String PREFS = "english_sprint_shop";

    private final Context context;
    private final SharedPreferences prefs;
    private final EconomyStore economy;
    private final List<ShopItem> items = new ArrayList<>();
    private final Map<String, ShopItem> bySku = new LinkedHashMap<>();

    public ShopStore(Context context, EconomyStore economy) {
        this.context = context.getApplicationContext();
        this.economy = economy;
        this.prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        load();
        reconcilePurchases();
    }

    public List<ShopItem> items() { return Collections.unmodifiableList(items); }

    public boolean isOwned(ShopItem item) {
        return ownedSet().contains(item.sku);
    }

    public boolean isEquipped(ShopItem item) {
        return item.sku.equals(prefs.getString("equipped_" + item.type, ""));
    }

    public boolean buyAndEquip(ShopItem item) {
        if (!isOwned(item)) {
            if (!economy.spend(item.priceCrystals, "shop_purchase", item.sku)) return false;
            Set<String> owned = ownedSet();
            owned.add(item.sku);
            prefs.edit().putStringSet("owned", owned).apply();
        }
        prefs.edit().putString("equipped_" + item.type, item.sku).apply();
        return true;
    }

    public String equippedSku(String type) {
        return prefs.getString("equipped_" + type, "");
    }

    public int backgroundColor(int fallback) {
        ShopItem item = bySku.get(equippedSku("background"));
        if (item == null) return fallback;
        try { return Color.parseColor(item.payload.optString("color")); }
        catch (Exception e) { return fallback; }
    }

    public int buttonRadius(int fallback) {
        ShopItem item = bySku.get(equippedSku("button"));
        return item == null ? fallback : Math.max(4, Math.min(32, item.payload.optInt("radius", fallback)));
    }

    public int frameStrokeColor(int fallback) {
        ShopItem item = bySku.get(equippedSku("frame"));
        if (item == null) return fallback;
        try { return Color.parseColor(item.payload.optString("color")); }
        catch (Exception e) { return fallback; }
    }

    public String customTitle(Locale locale) {
        ShopItem item = bySku.get(equippedSku("title"));
        if (item == null) return "";
        JSONObject labels = item.payload.optJSONObject("label");
        if (labels == null) return item.name(locale);
        String lang = locale == null ? "en" : locale.getLanguage();
        String value = labels.optString(lang, "");
        if (value.isEmpty()) value = labels.optString("en", "");
        if (value.isEmpty()) value = labels.optString("ru", "");
        return value;
    }

    public String soundPack() {
        ShopItem item = bySku.get(equippedSku("sound"));
        return item == null ? "default" : item.payload.optString("pack", "default");
    }

    private void reconcilePurchases() {
        Set<String> owned = ownedSet();
        boolean changed = false;
        for (ShopItem item : items) {
            if (!owned.contains(item.sku) && economy.hasDebit("shop_purchase", item.sku)) {
                owned.add(item.sku);
                changed = true;
            }
        }
        if (changed) prefs.edit().putStringSet("owned", owned).apply();
    }

    private Set<String> ownedSet() {
        Set<String> stored = prefs.getStringSet("owned", Collections.emptySet());
        return new HashSet<>(stored == null ? Collections.emptySet() : stored);
    }

    private void load() {
        try {
            JSONObject root = new JSONObject(readAsset("game/shop_catalog.json"));
            JSONArray array = root.getJSONArray("items");
            for (int i = 0; i < array.length(); i++) {
                JSONObject o = array.getJSONObject(i);
                ShopItem item = new ShopItem(
                        o.getString("sku"),
                        o.getString("type"),
                        Math.max(0, o.getInt("price_crystals")),
                        o.optJSONObject("payload"),
                        stringMap(o.optJSONObject("name")),
                        stringMap(o.optJSONObject("description"))
                );
                items.add(item);
                bySku.put(item.sku, item);
            }
        } catch (Exception e) {
            throw new IllegalStateException("Shop catalog failed to load", e);
        }
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
