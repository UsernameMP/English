package com.usernamemp.englishsprint;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.CountDownTimer;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public final class MemoryMiniGame implements MiniGame {
    private static final String[] SYMBOLS={"🚀","🌟","🎯","🧩","🎵","⚙","🌈","💎"};
    private final Handler handler=new Handler(Looper.getMainLooper());

    @Override public String id(){ return "memory"; }

    @Override
    public void start(Activity activity, MiniGameConfig config, EconomyStore economy, Runnable onFinished){
        final boolean[] ended={false};
        final boolean[] locked={false};
        final int[] first={-1};
        final int[] pairs={0};
        final Button[] buttons=new Button[16];

        List<String> deck=new ArrayList<>();
        for(String s:SYMBOLS){ deck.add(s); deck.add(s); }
        Collections.shuffle(deck);

        LinearLayout root=new LinearLayout(activity);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(activity,18),dp(activity,24),dp(activity,18),dp(activity,24));
        root.setBackgroundColor(Color.rgb(246,247,251));

        TextView title=label(activity,config.title(java.util.Locale.getDefault()),27,Color.rgb(24,29,38),Typeface.BOLD);
        title.setGravity(Gravity.CENTER); root.addView(title,matchWrap());
        TextView hint=label(activity,activity.getString(R.string.memory_hint),14,Color.rgb(96,105,122),Typeface.NORMAL);
        hint.setGravity(Gravity.CENTER); hint.setPadding(0,dp(activity,6),0,dp(activity,10)); root.addView(hint,matchWrap());

        LinearLayout stats=new LinearLayout(activity); stats.setOrientation(LinearLayout.HORIZONTAL);
        TextView time=label(activity,activity.getString(R.string.minigame_time_fmt,config.durationSeconds),16,Color.rgb(47,82,235),Typeface.BOLD);
        TextView pairView=label(activity,activity.getString(R.string.memory_pairs_fmt,0),16,Color.rgb(24,29,38),Typeface.BOLD);
        stats.addView(time,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f));
        pairView.setGravity(Gravity.END);
        stats.addView(pairView,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f));
        root.addView(stats,matchWrap());

        GridLayout grid=new GridLayout(activity); grid.setColumnCount(4); grid.setRowCount(4);
        grid.setPadding(0,dp(activity,16),0,dp(activity,12));
        int side=Math.max(dp(activity,64),Math.min(dp(activity,78),
                (activity.getResources().getDisplayMetrics().widthPixels-dp(activity,42))/4));

        final CountDownTimer[] timer=new CountDownTimer[1];
        final Runnable[] finish=new Runnable[1];

        for(int i=0;i<16;i++){
            final int idx=i;
            Button b=new Button(activity);
            b.setText("?");
            b.setTextSize(25);
            b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
            b.setTextColor(Color.rgb(47,82,235));
            b.setAllCaps(false);
            b.setPadding(0,0,0,0);
            b.setBackground(round(Color.WHITE,dp(activity,14),dp(activity,1),Color.rgb(225,229,239)));
            GridLayout.LayoutParams lp=new GridLayout.LayoutParams(); lp.width=side; lp.height=side;
            lp.setMargins(dp(activity,3),dp(activity,3),dp(activity,3),dp(activity,3));
            grid.addView(b,lp); buttons[i]=b;

            b.setOnClickListener(v->{
                if(ended[0]||locked[0]||!b.isEnabled()||idx==first[0])return;
                b.setText(deck.get(idx));
                b.setTextColor(Color.rgb(24,29,38));
                if(first[0]<0){ first[0]=idx; return; }

                int a=first[0]; first[0]=-1; locked[0]=true;
                if(deck.get(a).equals(deck.get(idx))){
                    buttons[a].setEnabled(false); b.setEnabled(false);
                    pairs[0]++; pairView.setText(activity.getString(R.string.memory_pairs_fmt,pairs[0]));
                    locked[0]=false;
                    if(pairs[0]==8) finish[0].run();
                }else{
                    handler.postDelayed(()->{
                        if(ended[0])return;
                        buttons[a].setText("?"); buttons[a].setTextColor(Color.rgb(47,82,235));
                        b.setText("?"); b.setTextColor(Color.rgb(47,82,235));
                        locked[0]=false;
                    },480);
                }
            });
        }
        root.addView(grid);

        Button skip=new Button(activity);
        skip.setText(activity.getString(R.string.minigame_skip)); skip.setAllCaps(false); skip.setTextSize(15);
        root.addView(skip,matchWrap());

        finish[0]=()->{
            if(ended[0])return;
            ended[0]=true; locked[0]=true;
            if(timer[0]!=null)timer[0].cancel();
            int score=pairs[0];
            int bonus=Math.min(config.scoreBonusCap,score/Math.max(1,config.scoreBonusEvery));
            int reward=config.completionReward+bonus;
            if(reward>0)economy.credit(reward,"minigame_complete",config.id);
            for(Button b:buttons)b.setEnabled(false);
            title.setText(activity.getString(R.string.minigame_finished));
            hint.setText(activity.getString(R.string.minigame_result_fmt,score,reward));
            time.setText("💎 "+economy.balance());

            Button cont=new Button(activity); cont.setText(activity.getString(R.string.minigame_continue));
            cont.setAllCaps(false); cont.setTextColor(Color.WHITE); cont.setTextSize(18); cont.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
            cont.setBackground(round(Color.rgb(47,82,235),dp(activity,14),0,Color.TRANSPARENT));
            cont.setMinHeight(dp(activity,56)); cont.setOnClickListener(v->onFinished.run());
            LinearLayout.LayoutParams lp=matchWrap(); lp.topMargin=dp(activity,12); root.addView(cont,lp);
        };

        skip.setOnClickListener(v->{ if(timer[0]!=null)timer[0].cancel(); ended[0]=true; onFinished.run(); });
        timer[0]=new CountDownTimer(config.durationSeconds*1000L,1000L){
            @Override public void onTick(long ms){time.setText(activity.getString(R.string.minigame_time_fmt,(int)Math.ceil(ms/1000.0)));}
            @Override public void onFinish(){ended[0]=false;finish[0].run();}
        };
        activity.setContentView(root); timer[0].start();
    }

    private static android.graphics.drawable.GradientDrawable round(int fill,int radius,int sw,int stroke){
        android.graphics.drawable.GradientDrawable g=new android.graphics.drawable.GradientDrawable();
        g.setColor(fill);g.setCornerRadius(radius);if(sw>0)g.setStroke(sw,stroke);return g;
    }
    private static TextView label(Activity a,String s,float sp,int color,int style){TextView v=new TextView(a);v.setText(s);v.setTextSize(sp);v.setTextColor(color);v.setTypeface(Typeface.DEFAULT,style);return v;}
    private static LinearLayout.LayoutParams matchWrap(){return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT);}
    private static int dp(Activity a,int v){return Math.round(v*a.getResources().getDisplayMetrics().density);}
}
