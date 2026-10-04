package com.usernamemp.englishsprint;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.Arrays;
import java.util.List;

public final class MetaGameStore {
    public static final String PET = "pet";
    public static final String DEFENSE = "defense";
    public static final String HERO = "hero";
    private final SharedPreferences prefs;
    private final EconomyStore economy;

    public MetaGameStore(Context context, EconomyStore economy) {
        this.prefs = context.getSharedPreferences("meta_game", Context.MODE_PRIVATE);
        this.economy = economy;
    }
    public List<String> modes() { return Arrays.asList(PET, DEFENSE, HERO); }
    public String preferredMode() { return prefs.getString("preferred_mode", PET); }
    public void setPreferredMode(String mode) {
        if (modes().contains(mode)) prefs.edit().putString("preferred_mode", mode).apply();
    }
    public int level(String mode, String item) { return prefs.getInt("level."+mode+"."+item, 0); }
    public boolean buyLevel(String mode, String item, int price) {
        if (!modes().contains(mode) || price < 0 || !economy.spend(price, "meta_purchase", mode+":"+item)) return false;
        String key="level."+mode+"."+item;
        prefs.edit().putInt(key, prefs.getInt(key,0)+1).apply();
        return true;
    }
}