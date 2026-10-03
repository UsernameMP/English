package com.usernamemp.englishsprint;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public final class DictionaryEntry {
    public final String lemma;
    public final List<String> forms;
    public final String phonetic;
    public final String example;
    private final Map<String, String> translations;
    private final Map<String, String> definitions;

    public DictionaryEntry(
            String lemma,
            List<String> forms,
            String phonetic,
            String example,
            Map<String, String> translations,
            Map<String, String> definitions
    ) {
        this.lemma = lemma;
        this.forms = Collections.unmodifiableList(forms);
        this.phonetic = phonetic == null ? "" : phonetic;
        this.example = example == null ? "" : example;
        this.translations = Collections.unmodifiableMap(new LinkedHashMap<>(translations));
        this.definitions = Collections.unmodifiableMap(new LinkedHashMap<>(definitions));
    }

    public String translation(Locale locale) {
        return localized(translations, locale, lemma);
    }

    public String definition(Locale locale) {
        return localized(definitions, locale, translation(locale));
    }

    private static String localized(Map<String, String> values, Locale locale, String fallback) {
        String lang = locale == null ? "en" : locale.getLanguage();
        String value = values.get(lang);
        if (value == null || value.isEmpty()) value = values.get("en");
        if (value == null || value.isEmpty()) value = values.get("ru");
        if ((value == null || value.isEmpty()) && !values.isEmpty()) value = values.values().iterator().next();
        return value == null || value.isEmpty() ? fallback : value;
    }
}
