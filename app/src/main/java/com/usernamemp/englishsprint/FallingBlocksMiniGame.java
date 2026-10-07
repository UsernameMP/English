package com.usernamemp.englishsprint;
import android.widget.*;import java.util.*;
public final class FallingBlocksMiniGame extends ArcadeMiniGame{
 private final int[][] q=new int[12][8];private final Random r=new Random();private TextView board;private int piece=2;
 public String id(){return "falling_blocks";}protected String[] upgrades(){return new String[]{"preview","hold","rescue"};}protected String label(String u){return u;}
 protected void game(LinearLayout root){board=t("",17,1);root.addView(board,m());LinearLayout keys=new LinearLayout(a);for(int c=0;c<8;c++){final int x=c;Button k=b("▼");k.setOnClickListener(v->drop(x));keys.addView(k,new LinearLayout.LayoutParams(0,dp(50),1));}root.addView(keys,m());draw();}
 private void drop(int c){int y=0;while(y+piece<12&&q[y+piece][c]==0)y++;if(q[y][c]!=0){if(lv("rescue")>0)q[11]=new int[8];else return;}for(int i=0;i<piece&&y+i<12;i++)q[y+i][c]=1;add(piece);clear();piece=1+r.nextInt(3);draw();}
 private void clear(){for(int y=0;y<12;y++){boolean f=true;for(int x=0;x<8;x++)f&=q[y][x]>0;if(f){for(int z=y;z>0;z--)q[z]=q[z-1].clone();q[0]=new int[8];add(30);}}}
 private void draw(){StringBuilder s=new StringBuilder();if(lv("preview")>0)s.append("Next: ").append(piece).append("\n");for(int[] row:q){for(int v:row)s.append(v>0?"■ ":"· ");s.append("\n");}board.setText(s);}
}