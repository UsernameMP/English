package com.usernamemp.englishsprint;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

public final class KnowledgeUnit {
    public final String id;
    public final String kind;
    public final String legacySkill;
    private final Map<String, String> labels;

    public KnowledgeUnit(String id, String kind, String legacySkill, Map<String, String> labels) {
        this.id = id;
        this.kind = kind;
        this.legacySkill = legacySkill == null ? "" : legacySkill;
        this.labels = Collections.unmodifiableMap(new LinkedHashMap<>(labels));
    }

    public String label(Locale locale) {
        String lang = locale == null ? "en" : locale.getLanguage();
        String value = labels.get(lang);
        if (value == null || value.isEmpty()) value = labels.get("en");
        if (value == null || value.isEmpty()) value = labels.get("ru");
        return value == null || value.isEmpty() ? id : value;
    }
}
