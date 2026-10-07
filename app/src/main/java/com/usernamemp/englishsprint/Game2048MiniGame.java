package com.usernamemp.englishsprint;
import android.widget.*;import java.util.*;
public final class Game2048MiniGame extends ArcadeMiniGame{
 private final int[][] q=new int[4][4];private final Random r=new Random();private TextView board;
 public String id(){return "game_2048";}protected String[] upgrades(){return new String[]{"start","luck","boost"};}protected String label(String u){return u;}
 protected void game(LinearLayout root){q[0][0]=2;spawn();for(int i=0;i<lv("start");i++)spawn();board=t("",21,1);root.addView(board,m());LinearLayout keys=new LinearLayout(a);for(String d:new String[]{"←","↑","↓","→"}){Button k=b(d);k.setOnClickListener(v->move(d));keys.addView(k,new LinearLayout.LayoutParams(0,dp(58),1));}root.addView(keys,m());draw();}
 private void move(String d){for(int z=0;z<4;z++){int[] x=new int[4];for(int i=0;i<4;i++){int rr=("↓".equals(d)?3-i:"↑".equals(d)?i:z),cc=("→".equals(d)?3-i:"←".equals(d)?i:z);x[i]=q[rr][cc];}x=merge(x);for(int i=0;i<4;i++){int rr=("↓".equals(d)?3-i:"↑".equals(d)?i:z),cc=("→".equals(d)?3-i:"←".equals(d)?i:z);q[rr][cc]=x[i];}}spawn();draw();}
 private int[] merge(int[] x){int[] y=new int[4];int n=0;for(int v:x)if(v>0)y[n++]=v;for(int i=0;i<3;i++)if(y[i]>0&&y[i]==y[i+1]){y[i]*=2;add(y[i]+lv("boost"));for(int j=i+1;j<3;j++)y[j]=y[j+1];y[3]=0;}return y;}
 private void spawn(){List<Integer>x=new ArrayList<>();for(int i=0;i<16;i++)if(q[i/4][i%4]==0)x.add(i);if(x.isEmpty())return;int k=x.get(r.nextInt(x.size()));q[k/4][k%4]=r.nextInt(Math.max(2,10-lv("luck")))==0?4:2;}
 private void draw(){StringBuilder s=new StringBuilder();for(int[] row:q){for(int v:row)s.append(String.format("%5s",v==0?"·":v));s.append("\n");}board.setText(s);}
}