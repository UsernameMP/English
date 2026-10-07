package com.usernamemp.englishsprint;
import android.widget.*;
public final class TowerDefenseMiniGame extends ArcadeMiniGame{
 private TextView state;private int wave=1,base=100;
 public String id(){return "tower_defense";}protected String[] upgrades(){return new String[]{"damage","range","rate"};}protected String label(String u){return u;}protected void game(LinearLayout root){state=t("",18,1);root.addView(state,m());Button x=b("▶ Next wave");x.setMinHeight(dp(72));x.setOnClickListener(v->wave());root.addView(x,m());draw();}protected void changed(){draw();}
 private void wave(){DefenseEngine d=new DefenseEngine();d.add(new DefenseEngine.Defense("fire",5+lv("damage")*2,Math.max(1,3-lv("rate")/3)));d.add(new DefenseEngine.Defense("ice",3+lv("range"),2));DefenseEngine.Result z=d.simulate(1,2+wave/2,12+wave*3);if(z.survived){add(10+wave*3);wave++;}else base=Math.max(0,base-15);draw();}
 private void draw(){if(state!=null)state.setText("🏰 Base "+base+"\nWave "+wave+"\n🔥 Damage "+lv("damage")+"  ❄ Range "+lv("range")+"  ⚡ Rate "+lv("rate"));}
}