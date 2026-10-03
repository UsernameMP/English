package com.usernamemp.englishsprint;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.CountDownTimer;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.Locale;

public final class TapSparkMiniGame implements MiniGame {
    @Override
    public String id() {
        return "tap_spark";
    }

    @Override
    public void start(Activity activity, MiniGameConfig config, EconomyStore economy, Runnable onFinished) {
        final int[] score = {0};
        final boolean[] ended = {false};

        LinearLayout root = new LinearLayout(activity);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(activity, 22), dp(activity, 28), dp(activity, 22), dp(activity, 28));
        root.setBackgroundColor(Color.rgb(246, 247, 251));

        TextView title = label(activity, config.title(Locale.getDefault()), 28, Color.rgb(24, 29, 38), Typeface.BOLD);
        title.setGravity(Gravity.CENTER);
        root.addView(title, matchWrap());

        TextView subtitle = label(activity,
                activity.getString(R.string.minigame_tap_hint),
                15, Color.rgb(96, 105, 122), Typeface.NORMAL);
        subtitle.setGravity(Gravity.CENTER);
        subtitle.setPadding(0, dp(activity, 8), 0, dp(activity, 18));
        root.addView(subtitle, matchWrap());

        TextView timerText = label(activity,
                activity.getString(R.string.minigame_time_fmt, config.durationSeconds),
                18, Color.rgb(47, 82, 235), Typeface.BOLD);
        timerText.setGravity(Gravity.CENTER);
        root.addView(timerText, matchWrap());

        TextView scoreText = label(activity,
                activity.getString(R.string.minigame_score_fmt, 0),
                20, Color.rgb(24, 29, 38), Typeface.BOLD);
        scoreText.setGravity(Gravity.CENTER);
        scoreText.setPadding(0, dp(activity, 10), 0, dp(activity, 20));
        root.addView(scoreText, matchWrap());

        Button tap = new Button(activity);
        tap.setText("⚡ TAP");
        tap.setTextSize(30);
        tap.setAllCaps(false);
        tap.setTextColor(Color.WHITE);
        tap.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        tap.setMinHeight(dp(activity, 180));
        tap.setBackground(Shapes.round(Color.rgb(47, 82, 235), dp(activity, 34), 0, Color.TRANSPARENT));
        root.addView(tap, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(activity, 190)));

        Button skip = new Button(activity);
        skip.setText(activity.getString(R.string.minigame_skip));
        skip.setAllCaps(false);
        skip.setTextSize(16);
        LinearLayout.LayoutParams skipLp = matchWrap();
        skipLp.topMargin = dp(activity, 18);
        root.addView(skip, skipLp);

        final CountDownTimer[] timer = new CountDownTimer[1];

        Runnable finishCompleted = () -> {
            if (ended[0]) return;
            ended[0] = true;
            if (timer[0] != null) timer[0].cancel();
            int bonus = Math.min(config.scoreBonusCap, score[0] / config.scoreBonusEvery);
            int reward = config.completionReward + bonus;
            if (reward > 0) economy.credit(reward, "minigame_complete", config.id);

            tap.setEnabled(false);
            skip.setEnabled(false);
            title.setText(activity.getString(R.string.minigame_finished));
            subtitle.setText(activity.getString(R.string.minigame_result_fmt, score[0], reward));
            timerText.setText("💎 " + economy.balance());

            Button continueButton = new Button(activity);
            continueButton.setText(activity.getString(R.string.minigame_continue));
            continueButton.setAllCaps(false);
            continueButton.setTextSize(18);
            continueButton.setTextColor(Color.WHITE);
            continueButton.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
            continueButton.setBackground(Shapes.round(Color.rgb(47, 82, 235), dp(activity, 14), 0, Color.TRANSPARENT));
            continueButton.setMinHeight(dp(activity, 58));
            continueButton.setOnClickListener(v -> onFinished.run());

            LinearLayout.LayoutParams lp = matchWrap();
            lp.topMargin = dp(activity, 16);
            root.addView(continueButton, lp);
        };

        tap.setOnClickListener(v -> {
            if (ended[0]) return;
            score[0]++;
            scoreText.setText(activity.getString(R.string.minigame_score_fmt, score[0]));
            String[] symbols = {"⚡", "✨", "💥", "⭐", "🔥"};
            tap.setText(symbols[score[0] % symbols.length] + " TAP");
        });

        skip.setOnClickListener(v -> {
            if (ended[0]) return;
            ended[0] = true;
            if (timer[0] != null) timer[0].cancel();
            onFinished.run();
        });

        timer[0] = new CountDownTimer(config.durationSeconds * 1000L, 1000L) {
            @Override public void onTick(long millisUntilFinished) {
                int seconds = (int) Math.ceil(millisUntilFinished / 1000.0);
                timerText.setText(activity.getString(R.string.minigame_time_fmt, seconds));
            }

            @Override public void onFinish() {
                finishCompleted.run();
            }
        };

        activity.setContentView(root);
        timer[0].start();
    }

    private static TextView label(Activity activity, String value, float sp, int color, int style) {
        TextView view = new TextView(activity);
        view.setText(value);
        view.setTextSize(sp);
        view.setTextColor(color);
        view.setTypeface(Typeface.DEFAULT, style);
        return view;
    }

    private static LinearLayout.LayoutParams matchWrap() {
        return new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private static int dp(Activity activity, int value) {
        return Math.round(value * activity.getResources().getDisplayMetrics().density);
    }
}
