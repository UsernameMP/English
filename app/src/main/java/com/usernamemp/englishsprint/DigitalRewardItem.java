package com.usernamemp.englishsprint;

import org.json.JSONObject;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

public final class DigitalRewardItem {
    public final String sku;
    public final String type;
    public final int priceCrystals;
    public final boolean enabled;
    public final boolean backendRequired;
    public final String fulfillmentMode;
    public final String asset;
    public final String rightsStatus;
    private final Map<String, String> names;
    private final Map<String, String> descriptions;

    DigitalRewardItem(JSONObject o, Map<String, String> names, Map<String, String> descriptions) {
        this.sku = o.optString("sku");
        this.type = o.optString("type");
        this.priceCrystals = Math.max(0, o.optInt("price_crystals", 0));
        this.enabled = o.optBoolean("enabled", false);
        this.backendRequired = o.optBoolean("backend_required", false);
        JSONObject fulfillment = o.optJSONObject("fulfillment");
        this.fulfillmentMode = fulfillment == null ? "" : fulfillment.optString("mode", "");
        this.asset = fulfillment == null ? "" : fulfillment.optString("asset", "");
        JSONObject rights = o.optJSONObject("rights");
        this.rightsStatus = rights == null ? "" : rights.optString("status", "");
        this.names = Collections.unmodifiableMap(new LinkedHashMap<>(names));
        this.descriptions = Collections.unmodifiableMap(new LinkedHashMap<>(descriptions));
    }

    public String name(Locale locale) { return localized(names, locale, sku); }
    public String description(Locale locale) { return localized(descriptions, locale, ""); }

    private static String localized(Map<String, String> map, Locale locale, String fallback) {
        String lang = locale == null ? "en" : locale.getLanguage();
        String value = map.get(lang);
        if (value == null || value.isEmpty()) value = map.get("en");
        if (value == null || value.isEmpty()) value = map.get("ru");
        return value == null || value.isEmpty() ? fallback : value;
    }
}
