package com.usernamemp.englishsprint;

import org.json.JSONObject;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

public final class ShopItem {
    public final String sku;
    public final String type;
    public final int priceCrystals;
    public final JSONObject payload;
    private final Map<String, String> names;
    private final Map<String, String> descriptions;

    ShopItem(String sku, String type, int priceCrystals, JSONObject payload,
             Map<String, String> names, Map<String, String> descriptions) {
        this.sku = sku;
        this.type = type;
        this.priceCrystals = priceCrystals;
        this.payload = payload == null ? new JSONObject() : payload;
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
