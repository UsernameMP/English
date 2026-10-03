package com.usernamemp.englishsprint;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

public final class ContentPack {
    public final String id;
    public final String asset;
    public final String subject;
    public final int gradeMin;
    public final int gradeMax;
    public final String competition;
    public final String region;
    public final String season;
    private final Map<String, String> titles;
    private final Map<String, String> subtitles;

    public ContentPack(
            String id,
            String asset,
            String subject,
            int gradeMin,
            int gradeMax,
            String competition,
            String region,
            String season,
            Map<String, String> titles,
            Map<String, String> subtitles
    ) {
        this.id = id;
        this.asset = asset;
        this.subject = subject;
        this.gradeMin = gradeMin;
        this.gradeMax = gradeMax;
        this.competition = competition;
        this.region = region;
        this.season = season;
        this.titles = Collections.unmodifiableMap(new LinkedHashMap<>(titles));
        this.subtitles = Collections.unmodifiableMap(new LinkedHashMap<>(subtitles));
    }

    public String title(Locale locale) {
        return localized(titles, locale, id);
    }

    public String subtitle(Locale locale) {
        return localized(subtitles, locale, "");
    }

    private static String localized(Map<String, String> values, Locale locale, String fallback) {
        String lang = locale == null ? "en" : locale.getLanguage();
        String value = values.get(lang);
        if (value == null || value.isEmpty()) value = values.get("en");
        if (value == null || value.isEmpty()) value = values.get("ru");
        return value == null || value.isEmpty() ? fallback : value;
    }
}
