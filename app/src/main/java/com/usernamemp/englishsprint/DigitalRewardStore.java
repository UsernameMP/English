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

public final class DigitalRewardStore {
    private static final String PREFS = "english_sprint_digital_rewards";

    private final Context context;
    private final SharedPreferences prefs;
    private final EconomyStore economy;
    private final List<DigitalRewardItem> items = new ArrayList<>();

    public DigitalRewardStore(Context context, EconomyStore economy) {
        this.context = context.getApplicationContext();
        this.economy = economy;
        this.prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        load();
        reconcileOwnedRedemptions();
    }

    public List<DigitalRewardItem> items() {
        return Collections.unmodifiableList(items);
    }

    public boolean isRedeemed(DigitalRewardItem item) {
        return redeemedSet().contains(item.sku);
    }

    public boolean canRedeemLocally(DigitalRewardItem item) {
        return item.enabled
                && !item.backendRequired
                && "asset".equals(item.fulfillmentMode)
                && !item.asset.isEmpty()
                && "owned_original".equals(item.rightsStatus);
    }

    public boolean redeemOwnedAsset(DigitalRewardItem item) {
        if (isRedeemed(item)) return true;
        if (!canRedeemLocally(item)) return false;
        if (!economy.spend(item.priceCrystals, "digital_reward", item.sku)) return false;

        Set<String> redeemed = redeemedSet();
        redeemed.add(item.sku);
        prefs.edit().putStringSet("redeemed", redeemed).apply();
        return true;
    }

    public String readOwnedAsset(DigitalRewardItem item) {
        if (!isRedeemed(item) || item.asset.isEmpty()) return "";
        try { return readAsset(item.asset); }
        catch (Exception e) { return ""; }
    }

    private void reconcileOwnedRedemptions() {
        Set<String> redeemed = redeemedSet();
        boolean changed = false;
        for (DigitalRewardItem item : items) {
            if (!redeemed.contains(item.sku)
                    && canRedeemLocally(item)
                    && economy.hasDebit("digital_reward", item.sku)) {
                redeemed.add(item.sku);
                changed = true;
            }
        }
        if (changed) prefs.edit().putStringSet("redeemed", redeemed).apply();
    }

    private Set<String> redeemedSet() {
        Set<String> stored = prefs.getStringSet("redeemed", Collections.emptySet());
        return new HashSet<>(stored == null ? Collections.emptySet() : stored);
    }

    private void load() {
        try {
            JSONObject root = new JSONObject(readAsset("game/reward_catalog.json"));
            JSONArray array = root.getJSONArray("items");
            for (int i = 0; i < array.length(); i++) {
                JSONObject o = array.getJSONObject(i);
                items.add(new DigitalRewardItem(o,
                        stringMap(o.optJSONObject("name")),
                        stringMap(o.optJSONObject("description"))));
            }
        } catch (Exception e) {
            throw new IllegalStateException("Digital reward catalog failed to load", e);
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
