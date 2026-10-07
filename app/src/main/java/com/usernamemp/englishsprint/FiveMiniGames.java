package com.usernamemp.englishsprint;

import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.widget.Button;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.*;

final class Game2048MiniGame extends ArcadeMiniGame {
    private final int[][] b=new int[4][4]; private final Random r=new Random(); private TextView board;
    public String id(){return "game_2048";} protected String[] upgrades(){return new String[]{"start","undo","luck"};}
    protected String upgradeLabel(String u){return "start".equals(u)?"Start":"undo".equals(u)?"Undo":"Luck";}
    protected void buildGame(LinearLayout root){b[0][0]=2;for(int i=0;i<level("start");i++)spawn();spawn();board=text("",22,1);root.addView(board,match());LinearLayout x=new LinearLayout(activity);for(String d:new String[]{"←","↑","↓","→"}){Button q=button(d);q.setOnClickListener(v->move(d));x.addView(q,new LinearLayout.LayoutParams(0,dp(58),1));}root.addView(x,match());draw();}
    private void move(String d){int[][] old=copy();for(int k=0;k<4;k++){int[] a=new int[4];for(int i=0;i<4;i++){int rr=("↓".equals(d)?3-i:"↑".equals(d)?i:k),cc=("→".equals(d)?3-i:"←".equals(d)?i:k);a[i]=b[rr][cc];}a=merge(a);for(int i=0;i<4;i++){int rr=("↓".equals(d)?3-i:"↑".equals(d)?i:k),cc=("→".equals(d)?3-i:"←".equals(d)?i:k);b[rr][cc]=a[i];}}if(!Arrays.deepEquals(old,b)){spawn();addScore(2);draw();}}
    private int[] merge(int[] a){int[] z=new int[4];int p=0;for(int v:a)if(v>0)z[p++]=v;for(int i=0;i<3;i++)if(z[i]>0&&z[i]==z[i+1]){z[i]*=2;addScore(z[i]);for(int j=i+1;j<3;j++)z[j]=z[j+1];z[3]=0;}return z;}
    private void spawn(){List<Integer> e=new ArrayList<>();for(int i=0;i<16;i++)if(b[i/4][i%4]==0)e.add(i);if(!e.isEmpty()){int x=e.get(r.nextInt(e.size()));b[x/4][x%4]=(r.nextInt(10+level("luck"))==0)?4:2;}}
    private int[][] copy(){int[][]x=new int[4][4];for(int i=0;i<4;i++)x[i]=b[i].clone();return x;}
    private void draw(){StringBuilder s=new StringBuilder();for(int[] row:b){for(int v:row)s.append(String.format("%5s",v==0?"·":v));s.append("\n");}board.setText(s.toString());}
}

final class SnakeMiniGame extends ArcadeMiniGame {
    private final Handler h=new Handler(Looper.getMainLooper());private final Random r=new Random();private final LinkedList<Integer> snake=new LinkedList<>();private TextView board;private int dir=1,food=55;private boolean running;
    public String id(){return "snake";}protected String[] upgrades(){return new String[]{"shield","magnet","length"};}protected String upgradeLabel(String u){return "shield".equals(u)?"Shield":"magnet".equals(u)?"Magnet":"Length";}
    protected void buildGame(LinearLayout root){snake.clear();snake.add(44);for(int i=0;i<level("length");i++)snake.add(43-i);board=text("",18,1);root.addView(board,match());LinearLayout x=new LinearLayout(activity);for(String d:new String[]{"←","↑","↓","→"}){Button q=button(d);q.setOnClickListener(v->dir="←".equals(d)?-1:"→".equals(d)?1:"↑".equals(d)?-10:10);x.addView(q,new LinearLayout.LayoutParams(0,dp(58),1));}root.addView(x,match());running=true;tick();}
    private void tick(){if(!running)return;int head=snake.getFirst(),row=head/10,col=head%10,n=head+dir;if((dir==1&&col==9)||(dir==-1&&col==0)||n<0||n>=100||snake.contains(n)){if(level("shield")>0){dir=-dir;h.postDelayed(this::tick,260);return;}running=false;return;}snake.addFirst(n);if(n==food||nearFood(n)){addScore(10);spawnFood();}else snake.removeLast();draw();h.postDelayed(this::tick,Math.max(110,300-level("magnet")*12));}
    private boolean nearFood(int n){return level("magnet")>=2&&Math.abs(n/10-food/10)+Math.abs(n%10-food%10)<=1;}private void spawnFood(){do food=r.nextInt(100);while(snake.contains(food));}
    private void draw(){StringBuilder s=new StringBuilder();for(int i=0;i<100;i++){s.append(i==food?"◆":snake.contains(i)?"●":"·");if(i%10==9)s.append("\n");}board.setText(s.toString());}
}

final class BlockPuzzleMiniGame extends ArcadeMiniGame {
    private final boolean[][] b=new boolean[8][8];private final Random r=new Random();private TextView board;private int piece=3;
    public String id(){return "block_puzzle";}protected String[] upgrades(){return new String[]{"reroll","bomb","slot"};}protected String upgradeLabel(String u){return "reroll".equals(u)?"Reroll":"bomb".equals(u)?"Bomb":"Slot";}
    protected void buildGame(LinearLayout root){board=text("",20,1);root.addView(board,match());TextView hint=text("Tap a column to place the current bar",13,0);root.addView(hint,match());LinearLayout cols=new LinearLayout(activity);for(int c=0;c<8;c++){final int cc=c;Button q=button(""+(c+1));q.setOnClickListener(v->place(cc));cols.addView(q,new LinearLayout.LayoutParams(0,dp(52),1));}root.addView(cols,match());draw();}
    private void place(int c){int len=Math.min(5,piece+level("slot")/2);for(int row=7;row>=0;row--){boolean ok=true;for(int x=c;x<Math.min(8,c+len);x++)if(b[row][x])ok=false;if(ok){for(int x=c;x<Math.min(8,c+len);x++)b[row][x]=true;addScore(len);clear();piece=1+r.nextInt(3+Math.min(2,level("reroll")));draw();return;}}if(level("bomb")>0){for(int y=0;y<8;y++)b[y][c]=false;draw();}}
    private void clear(){for(int y=0;y<8;y++){boolean full=true;for(int x=0;x<8;x++)full&=b[y][x];if(full){Arrays.fill(b[y],false);addScore(25);}}}
    private void draw(){StringBuilder s=new StringBuilder();for(boolean[] row:b){for(boolean v:row)s.append(v?"■ ":"□ ");s.append("\n");}board.setText(s.toString());}
}

final class TowerDefenseMiniGame extends ArcadeMiniGame {
    private TextView state;private int wave=1,base=100;
    public String id(){return "tower_defense";}protected String[] upgrades(){return new String[]{"damage","range","rate"};}protected String upgradeLabel(String u){return "damage".equals(u)?"Damage":"range".equals(u)?"Range":"Rate";}
    protected void buildGame(LinearLayout root){state=text("",18,1);root.addView(state,match());Button waveButton=button("▶ Next wave");waveButton.setMinHeight(dp(70));waveButton.setOnClickListener(v->wave());root.addView(waveButton,match());draw();}
    protected void onUpgradeChanged(){draw();}
    private void wave(){DefenseEngine e=new DefenseEngine();e.add(new DefenseEngine.Defense("fire",5+level("damage")*2,Math.max(1,3-level("rate")/3)));e.add(new DefenseEngine.Defense("ice",3+level("range"),2));DefenseEngine.Result x=e.simulate(1,2+wave/2,12+wave*3);if(x.survived){addScore(10+wave*3);wave++;}else base=Math.max(0,base-15);draw();}
    private void draw(){if(state!=null)state.setText("🏰 Base "+base+"\nWave "+wave+"\n🔥 Damage Lv."+level("damage")+"   ❄ Range Lv."+level("range")+"   ⚡ Rate Lv."+level("rate"));}
}

final class FallingBlocksMiniGame extends ArcadeMiniGame {
    private final int[][] b=new int[12][8];private final Random r=new Random();private TextView board;private int piece=2;
    public String id(){return "falling_blocks";}protected String[] upgrades(){return new String[]{"preview","hold","rescue"};}protected String upgradeLabel(String u){return "preview".equals(u)?"Preview":"hold".equals(u)?"Hold":"Rescue";}
    protected void buildGame(LinearLayout root){board=text("",18,1);root.addView(board,match());LinearLayout cols=new LinearLayout(activity);for(int c=0;c<8;c++){final int cc=c;Button q=button("▼");q.setOnClickListener(v->drop(cc));cols.addView(q,new LinearLayout.LayoutParams(0,dp(52),1));}root.addView(cols,match());draw();}
    private void drop(int c){int len=piece;int y=0;while(y+len<12&&b[y+len][c]==0)y++;if(y==0&&b[0][c]!=0){if(level("rescue")>0)for(int x=0;x<8;x++)b[11][x]=0;else return;}for(int i=0;i<len&&y+i<12;i++)b[y+i][c]=1;addScore(len);clear();piece=1+r.nextInt(3);draw();}
    private void clear(){for(int y=0;y<12;y++){boolean full=true;for(int x=0;x<8;x++)full&=b[y][x]>0;if(full){for(int yy=y;yy>0;yy--)b[yy]=b[yy-1].clone();b[0]=new int[8];addScore(30);}}}
    private void draw(){StringBuilder s=new StringBuilder();if(level("preview")>0)s.append("Next: ").append(piece).append(" blocks\n");for(int[] row:b){for(int v:row)s.append(v>0?"■ ":"· ");s.append("\n");}board.setText(s.toString());}
}
