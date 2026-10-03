package com.usernamemp.englishsprint;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

public final class WorkshopItem {
    public final String id;
    public final String icon;
    public final int priceCrystals;
    public final int requiredLevel;
    private final Map<String, String> names;
    private final Map<String, String> descriptions;

    public WorkshopItem(String id, String icon, int priceCrystals, int requiredLevel,
                        Map<String, String> names, Map<String, String> descriptions) {
        this.id = id;
        this.icon = icon;
        this.priceCrystals = priceCrystals;
        this.requiredLevel = requiredLevel;
        this.names = Collections.unmodifiableMap(new LinkedHashMap<>(names));
        this.descriptions = Collections.unmodifiableMap(new LinkedHashMap<>(descriptions));
    }

    public String name(Locale locale) { return localized(names, locale); }
    public String description(Locale locale) { return localized(descriptions, locale); }

    private String localized(Map<String, String> values, Locale locale) {
        String language = locale == null ? "en" : locale.getLanguage();
        String value = values.get(language);
        if (value == null || value.isEmpty()) value = values.get("en");
        return value == null ? id : value;
    }
}
