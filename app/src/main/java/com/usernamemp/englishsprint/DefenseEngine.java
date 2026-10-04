package com.usernamemp.englishsprint;

import java.util.ArrayList;
import java.util.List;

/** UI-independent deterministic defense simulation. No educational dependencies. */
public final class DefenseEngine {
    public static final class Defense {
        public final String id; public final int damage; public final int cooldown;
        public Defense(String id,int damage,int cooldown){this.id=id;this.damage=damage;this.cooldown=Math.max(1,cooldown);}
    }
    public static final class Result {
        public final boolean survived; public final int remainingBase; public final int defeated;
        Result(boolean survived,int remainingBase,int defeated){this.survived=survived;this.remainingBase=remainingBase;this.defeated=defeated;}
    }
    private final List<Defense> defenses=new ArrayList<>();
    public void add(Defense d){defenses.add(d);}
    public Result simulate(int waves,int enemiesPerWave,int enemyHp){
        int base=100, defeated=0, tick=0;
        for(int w=0;w<waves;w++) for(int e=0;e<enemiesPerWave;e++){
            int hp=enemyHp;
            for(int step=0;step<8 && hp>0;step++,tick++)
                for(Defense d:defenses) if(tick%d.cooldown==0) hp-=d.damage;
            if(hp<=0) defeated++; else base=Math.max(0,base-10);
            if(base==0) return new Result(false,0,defeated);
        }
        return new Result(true,base,defeated);
    }
}