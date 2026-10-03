package com.usernamemp.englishsprint;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.CountDownTimer;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.HashSet;
import java.util.Random;
import java.util.Set;

public final class Match3MiniGame implements MiniGame {
    private static final int SIZE = 6;
    private static final String[] GEMS = {"🔵","🟣","🟢","🟠","🔷","⭐"};

    private final Random random = new Random();
    private final int[][] board = new int[SIZE][SIZE];
    private final Button[][] cells = new Button[SIZE][SIZE];

    private int selectedR = -1;
    private int selectedC = -1;
    private int score = 0;
    private boolean ended = false;
    private boolean locked = false;

    @Override public String id() { return "match3"; }

    @Override
    public void start(Activity activity, MiniGameConfig config, EconomyStore economy, Runnable onFinished) {
        score = 0;
        selectedR = selectedC = -1;
        ended = false;
        locked = false;
        initBoard();

        LinearLayout root = new LinearLayout(activity);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(activity, 16), dp(activity, 22), dp(activity, 16), dp(activity, 22));
        root.setBackgroundColor(Color.rgb(246,247,251));

        TextView title = label(activity, config.title(java.util.Locale.getDefault()), 27, Color.rgb(24,29,38), Typeface.BOLD);
        title.setGravity(Gravity.CENTER);
        root.addView(title, matchWrap());

        TextView hint = label(activity, activity.getString(R.string.match3_hint), 14, Color.rgb(96,105,122), Typeface.NORMAL);
        hint.setGravity(Gravity.CENTER);
        hint.setPadding(0, dp(activity,6), 0, dp(activity,10));
        root.addView(hint, matchWrap());

        LinearLayout stats = new LinearLayout(activity);
        stats.setOrientation(LinearLayout.HORIZONTAL);
        TextView time = label(activity, activity.getString(R.string.minigame_time_fmt, config.durationSeconds), 16, Color.rgb(47,82,235), Typeface.BOLD);
        TextView scoreView = label(activity, activity.getString(R.string.minigame_score_fmt, score), 16, Color.rgb(24,29,38), Typeface.BOLD);
        stats.addView(time, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        scoreView.setGravity(Gravity.END);
        stats.addView(scoreView, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        root.addView(stats, matchWrap());

        GridLayout grid = new GridLayout(activity);
        grid.setColumnCount(SIZE);
        grid.setRowCount(SIZE);
        grid.setPadding(0, dp(activity,14), 0, dp(activity,12));
        int side = Math.max(dp(activity,46), Math.min(dp(activity,58),
                (activity.getResources().getDisplayMetrics().widthPixels - dp(activity,32)) / SIZE));

        for (int r=0;r<SIZE;r++) {
            for (int c=0;c<SIZE;c++) {
                final int rr=r, cc=c;
                Button b = new Button(activity);
                b.setTextSize(24);
                b.setAllCaps(false);
                b.setPadding(0,0,0,0);
                b.setMinWidth(0);
                b.setMinHeight(0);
                b.setBackground(round(Color.WHITE, dp(activity,12), dp(activity,1), Color.rgb(225,229,239)));
                GridLayout.LayoutParams lp = new GridLayout.LayoutParams();
                lp.width = side;
                lp.height = side;
                lp.setMargins(dp(activity,2),dp(activity,2),dp(activity,2),dp(activity,2));
                grid.addView(b, lp);
                cells[r][c]=b;
                b.setOnClickListener(v -> onCell(activity, rr, cc, scoreView, hint));
            }
        }
        refresh();
        root.addView(grid);

        Button skip = new Button(activity);
        skip.setText(activity.getString(R.string.minigame_skip));
        skip.setAllCaps(false);
        skip.setTextSize(15);
        root.addView(skip, matchWrap());

        final CountDownTimer[] timer = new CountDownTimer[1];
        Runnable finish = () -> {
            if (ended) return;
            ended = true;
            locked = true;
            if (timer[0] != null) timer[0].cancel();
            int bonus = Math.min(config.scoreBonusCap, score / Math.max(1, config.scoreBonusEvery));
            int reward = config.completionReward + bonus;
            if (reward > 0) economy.credit(reward, "minigame_complete", config.id);

            for(Button[] row:cells) for(Button b:row) b.setEnabled(false);
            title.setText(activity.getString(R.string.minigame_finished));
            hint.setText(activity.getString(R.string.minigame_result_fmt, score, reward));
            time.setText("💎 " + economy.balance());

            Button cont = new Button(activity);
            cont.setText(activity.getString(R.string.minigame_continue));
            cont.setAllCaps(false);
            cont.setTextColor(Color.WHITE);
            cont.setTextSize(18);
            cont.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
            cont.setBackground(round(Color.rgb(47,82,235), dp(activity,14),0,Color.TRANSPARENT));
            cont.setMinHeight(dp(activity,56));
            cont.setOnClickListener(v -> onFinished.run());
            LinearLayout.LayoutParams lp=matchWrap(); lp.topMargin=dp(activity,12);
            root.addView(cont,lp);
        };

        skip.setOnClickListener(v -> {
            if (timer[0]!=null) timer[0].cancel();
            ended=true;
            onFinished.run();
        });

        timer[0]=new CountDownTimer(config.durationSeconds*1000L,1000L){
            @Override public void onTick(long ms){
                time.setText(activity.getString(R.string.minigame_time_fmt,(int)Math.ceil(ms/1000.0)));
            }
            @Override public void onFinish(){ ended=false; finish.run(); }
        };
        activity.setContentView(root);
        timer[0].start();
    }

    private void onCell(Activity activity, int r, int c, TextView scoreView, TextView hint) {
        if (ended || locked) return;
        if (selectedR < 0) {
            selectedR=r; selectedC=c;
            cells[r][c].setBackground(round(Color.rgb(232,237,255), dp(activity,12), dp(activity,2), Color.rgb(47,82,235)));
            return;
        }

        int r0=selectedR, c0=selectedC;
        selectedR=selectedC=-1;
        refresh();
        if (Math.abs(r-r0)+Math.abs(c-c0)!=1) {
            selectedR=r; selectedC=c;
            cells[r][c].setBackground(round(Color.rgb(232,237,255), dp(activity,12), dp(activity,2), Color.rgb(47,82,235)));
            return;
        }

        swap(r0,c0,r,c);
        Set<Integer> matched=findMatches();
        if (matched.isEmpty()) {
            swap(r0,c0,r,c);
            refresh();
            return;
        }

        locked=true;
        int gained=0;
        while(!matched.isEmpty()) {
            gained += matched.size();
            clearCollapseRefill(matched);
            matched=findMatches();
        }
        score += gained;
        scoreView.setText(activity.getString(R.string.minigame_score_fmt,score));
        refresh();
        if (!hasPossibleMove()) {
            hint.setText(activity.getString(R.string.match3_shuffle));
            initBoard();
            refresh();
        }
        locked=false;
    }

    private void initBoard() {
        int guard=0;
        do {
            for(int r=0;r<SIZE;r++) for(int c=0;c<SIZE;c++) {
                int value;
                do { value=random.nextInt(GEMS.length); }
                while((c>=2 && board[r][c-1]==value && board[r][c-2]==value)
                        || (r>=2 && board[r-1][c]==value && board[r-2][c]==value));
                board[r][c]=value;
            }
            guard++;
        } while(!hasPossibleMove() && guard<30);
    }

    private Set<Integer> findMatches() {
        Set<Integer> out=new HashSet<>();
        for(int r=0;r<SIZE;r++){
            int start=0;
            for(int c=1;c<=SIZE;c++){
                if(c<SIZE && board[r][c]==board[r][start]) continue;
                if(c-start>=3) for(int x=start;x<c;x++) out.add(r*SIZE+x);
                start=c;
            }
        }
        for(int c=0;c<SIZE;c++){
            int start=0;
            for(int r=1;r<=SIZE;r++){
                if(r<SIZE && board[r][c]==board[start][c]) continue;
                if(r-start>=3) for(int x=start;x<r;x++) out.add(x*SIZE+c);
                start=r;
            }
        }
        return out;
    }

    private void clearCollapseRefill(Set<Integer> matched){
        for(int c=0;c<SIZE;c++){
            int write=SIZE-1;
            for(int r=SIZE-1;r>=0;r--){
                if(!matched.contains(r*SIZE+c)) board[write--][c]=board[r][c];
            }
            while(write>=0) board[write--][c]=random.nextInt(GEMS.length);
        }
    }

    private boolean hasPossibleMove(){
        for(int r=0;r<SIZE;r++) for(int c=0;c<SIZE;c++){
            if(c+1<SIZE){
                swap(r,c,r,c+1); boolean ok=!findMatches().isEmpty(); swap(r,c,r,c+1); if(ok)return true;
            }
            if(r+1<SIZE){
                swap(r,c,r+1,c); boolean ok=!findMatches().isEmpty(); swap(r,c,r+1,c); if(ok)return true;
            }
        }
        return false;
    }

    private void swap(int r1,int c1,int r2,int c2){
        int t=board[r1][c1]; board[r1][c1]=board[r2][c2]; board[r2][c2]=t;
    }

    private void refresh(){
        for(int r=0;r<SIZE;r++) for(int c=0;c<SIZE;c++){
            if(cells[r][c]==null) continue;
            cells[r][c].setText(GEMS[board[r][c]]);
            cells[r][c].setBackground(round(Color.WHITE,12,1,Color.rgb(225,229,239)));
        }
    }

    private static android.graphics.drawable.GradientDrawable round(int fill,int radius,int sw,int stroke){
        android.graphics.drawable.GradientDrawable g=new android.graphics.drawable.GradientDrawable();
        g.setColor(fill); g.setCornerRadius(radius); if(sw>0)g.setStroke(sw,stroke); return g;
    }
    private static TextView label(Activity a,String s,float sp,int color,int style){
        TextView v=new TextView(a); v.setText(s); v.setTextSize(sp); v.setTextColor(color); v.setTypeface(Typeface.DEFAULT,style); return v;
    }
    private static LinearLayout.LayoutParams matchWrap(){return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT);}
    private static int dp(Activity a,int v){return Math.round(v*a.getResources().getDisplayMetrics().density);}
}
