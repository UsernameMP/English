package com.usernamemp.englishsprint;
import android.widget.*;import java.util.*;
public final class BlockPuzzleMiniGame extends ArcadeMiniGame{
 private final boolean[][] q=new boolean[8][8];private final Random r=new Random();private TextView board;private int piece=3;
 public String id(){return "block_puzzle";}protected String[] upgrades(){return new String[]{"reroll","bomb","slot"};}protected String label(String u){return u;}
 protected void game(LinearLayout root){board=t("",19,1);root.addView(board,m());LinearLayout keys=new LinearLayout(a);for(int c=0;c<8;c++){final int x=c;Button k=b(""+(c+1));k.setOnClickListener(v->place(x));keys.addView(k,new LinearLayout.LayoutParams(0,dp(50),1));}root.addView(keys,m());draw();}
 private void place(int c){int len=Math.min(5,piece+lv("slot")/2);for(int y=7;y>=0;y--){boolean ok=true;for(int x=c;x<Math.min(8,c+len);x++)ok&=!q[y][x];if(ok){for(int x=c;x<Math.min(8,c+len);x++)q[y][x]=true;add(len);clear();piece=1+r.nextInt(3+Math.min(2,lv("reroll")));draw();return;}}if(lv("bomb")>0){for(int y=0;y<8;y++)q[y][c]=false;draw();}}
 private void clear(){for(int y=0;y<8;y++){boolean f=true;for(int x=0;x<8;x++)f&=q[y][x];if(f){Arrays.fill(q[y],false);add(25);}}}
 private void draw(){StringBuilder s=new StringBuilder();for(boolean[] row:q){for(boolean v:row)s.append(v?"■ ":"□ ");s.append("\n");}board.setText(s);}
}