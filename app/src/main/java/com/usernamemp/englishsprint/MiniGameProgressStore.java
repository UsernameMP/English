package com.usernamemp.englishsprint;
import android.content.Context;
import android.content.SharedPreferences;
public final class MiniGameProgressStore {
 private final SharedPreferences p; private final EconomyStore e;
 public MiniGameProgressStore(Context c,EconomyStore e){p=c.getSharedPreferences("minigame_progress",Context.MODE_PRIVATE);this.e=e;}
 public int level(String g,String u){return p.getInt(g+"."+u,0);}
 public int price(String g,String u){return 8+7*level(g,u);}
 public boolean buy(String g,String u){int n=price(g,u);if(!e.spend(n,"minigame_upgrade",g+":"+u))return false;p.edit().putInt(g+"."+u,level(g,u)+1).apply();return true;}
}