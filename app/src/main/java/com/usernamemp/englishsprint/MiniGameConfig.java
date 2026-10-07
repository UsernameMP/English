package com.usernamemp.englishsprint;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

public final class MiniGameConfig {
    public final String id;
    public final boolean enabled;
    public final String status;
    public final int moduleApiVersion;
    public final int durationSeconds;
    public final int completionReward;
    public final int scoreBonusEvery;
    public final int scoreBonusCap;
    private final Map<String, String> titles;

    public MiniGameConfig(
            String id,
            boolean enabled,
            String status,
            int moduleApiVersion,
            int durationSeconds,
            int completionReward,
            int scoreBonusEvery,
            int scoreBonusCap,
            Map<String, String> titles
    ) {
        this.id = id;
        this.enabled = enabled;
        this.status = status;
        this.moduleApiVersion = moduleApiVersion;
        this.durationSeconds = durationSeconds;
        this.completionReward = completionReward;
        this.scoreBonusEvery = scoreBonusEvery;
        this.scoreBonusCap = scoreBonusCap;
        this.titles = Collections.unmodifiableMap(new LinkedHashMap<>(titles));
    }

    public boolean isProduction() { return enabled && "production".equals(status); }

    public MiniGameConfig withoutRewards() {
        return new MiniGameConfig(
                id, enabled, status, moduleApiVersion, durationSeconds,
                0, scoreBonusEvery, 0, titles
        );
    }

    public String title(Locale locale) {
        String lang = locale == null ? "en" : locale.getLanguage();
        String value = titles.get(lang);
        if (value == null || value.isEmpty()) value = titles.get("en");
        if (value == null || value.isEmpty()) value = titles.get("ru");
        return value == null || value.isEmpty() ? id : value;
    }
}
