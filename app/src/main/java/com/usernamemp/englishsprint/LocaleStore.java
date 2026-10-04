package com.usernamemp.englishsprint;

import android.app.Activity;
import android.content.Context;
import android.content.res.Configuration;
import java.util.Locale;

public final class LocaleStore {
    private static final String PREFS="english_sprint_settings", KEY="ui_locale";
    public static String current(Context c){ return c.getSharedPreferences(PREFS,Context.MODE_PRIVATE).getString(KEY,"system"); }
    public static void apply(Context c){
        String tag=current(c); if("system".equals(tag)) return;
        Locale locale=Locale.forLanguageTag(tag); Locale.setDefault(locale);
        Configuration cfg=new Configuration(c.getResources().getConfiguration());
        cfg.setLocale(locale); c.getResources().updateConfiguration(cfg,c.getResources().getDisplayMetrics());
    }
    public static void set(Activity a,String tag){
        a.getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString(KEY,tag).apply();
        if(!"system".equals(tag)){ Locale locale=Locale.forLanguageTag(tag); Locale.setDefault(locale); Configuration cfg=new Configuration(a.getResources().getConfiguration()); cfg.setLocale(locale); a.getResources().updateConfiguration(cfg,a.getResources().getDisplayMetrics()); }
        a.recreate();
    }
}