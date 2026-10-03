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

import java.util.HashSet;
import java.util.Random;
import java.util.Set;

public final class Match3MiniGame implements MiniGame {
    private static final int SIZE = 6;
    private static final String[] GEMS = {"🔵","🟣","🟢","🟠","🔷","⭐"};

    private final Random random = new Random();
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final int[][] board = new int[SIZE][SIZE];
    private final Button[][] cells = new Button[SIZE][SIZE];

    private Activity activity;
    private MiniGameConfig config;
    private EconomyStore economy;
    private Runnable onFinished;
    private MiniGameSoundFx soundFx;
    private CountDownTimer timer;
    private TextView title;
    private TextView hint;
    private TextView timeView;
    private TextView scoreView;
    private LinearLayout root;

    private int selectedR = -1;
    private int selectedC = -1;
    private int score = 0;
    private boolean ended = false;
    private boolean locked = false;

    @Override public String id() { return "match3"; }

    @Override
    public void start(Activity activity, MiniGameConfig config, EconomyStore economy, Runnable onFinished) {
        this.activity = activity;
        this.config = config;
        this.economy = economy;
        this.onFinished = onFinished;
        this.soundFx = new MiniGameSoundFx(activity);
        this.score = 0;
        this.selectedR = this.selectedC = -1;
        this.ended = false;
        this.locked = false;

        initBoard();
        buildUi();
        startTimer();
    }

    private void buildUi() {
        root = new LinearLayout(activity);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(16), dp(22), dp(16), dp(22));
        root.setBackgroundColor(Color.rgb(246,247,251));

        title = label(config.title(java.util.Locale.getDefault()), 27, Color.rgb(24,29,38), Typeface.BOLD);
        title.setGravity(Gravity.CENTER);
        root.addView(title, matchWrap());

        hint = label(activity.getString(R.string.match3_hint), 14, Color.rgb(96,105,122), Typeface.NORMAL);
        hint.setGravity(Gravity.CENTER);
        hint.setPadding(0, dp(6), 0, dp(10));
        root.addView(hint, matchWrap());

        LinearLayout stats = new LinearLayout(activity);
        stats.setOrientation(LinearLayout.HORIZONTAL);
        timeView = label(activity.getString(R.string.minigame_time_fmt, config.durationSeconds),
                16, Color.rgb(47,82,235), Typeface.BOLD);
        scoreView = label(activity.getString(R.string.minigame_score_fmt, score),
                16, Color.rgb(24,29,38), Typeface.BOLD);
        stats.addView(timeView, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        scoreView.setGravity(Gravity.END);
        stats.addView(scoreView, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        root.addView(stats, matchWrap());

        GridLayout grid = new GridLayout(activity);
        grid.setColumnCount(SIZE);
        grid.setRowCount(SIZE);
        grid.setPadding(0, dp(14), 0, dp(12));

        int side = Math.max(dp(46), Math.min(dp(58),
                (activity.getResources().getDisplayMetrics().widthPixels - dp(32)) / SIZE));

        for (int r = 0; r < SIZE; r++) {
            for (int c = 0; c < SIZE; c++) {
                final int rr = r;
                final int cc = c;
                Button b = new Button(activity);
                b.setTextSize(24);
                b.setAllCaps(false);
                b.setPadding(0,0,0,0);
                b.setMinWidth(0);
                b.setMinHeight(0);
                b.setBackground(round(Color.WHITE, dp(12), dp(1), Color.rgb(225,229,239)));

                GridLayout.LayoutParams lp = new GridLayout.LayoutParams();
                lp.width = side;
                lp.height = side;
                lp.setMargins(dp(2),dp(2),dp(2),dp(2));
                grid.addView(b, lp);
                cells[r][c] = b;
                b.setOnClickListener(v -> onCell(rr, cc));
            }
        }

        refresh();
        root.addView(grid);

        Button skip = new Button(activity);
        skip.setText(activity.getString(R.string.minigame_skip));
        skip.setAllCaps(false);
        skip.setTextSize(15);
        skip.setOnClickListener(v -> {
            if (timer != null) timer.cancel();
            ended = true;
            onFinished.run();
        });
        root.addView(skip, matchWrap());

        activity.setContentView(root);
    }

    private void startTimer() {
        timer = new CountDownTimer(config.durationSeconds * 1000L, 1000L) {
            @Override public void onTick(long ms) {
                timeView.setText(activity.getString(
                        R.string.minigame_time_fmt,
                        (int) Math.ceil(ms / 1000.0)));
            }

            @Override public void onFinish() {
                finishGame();
            }
        };
        timer.start();
    }

    private void onCell(int r, int c) {
        if (ended || locked) return;

        if (selectedR < 0) {
            selectedR = r;
            selectedC = c;
            soundFx.select();
            showSelection(r, c);
            return;
        }

        int r0 = selectedR;
        int c0 = selectedC;
        selectedR = selectedC = -1;

        if (Math.abs(r-r0) + Math.abs(c-c0) != 1) {
            refresh();
            selectedR = r;
            selectedC = c;
            soundFx.select();
            showSelection(r, c);
            return;
        }

        locked = true;
        soundFx.swap();
        animateSwap(r0, c0, r, c, () -> {
            if (ended) return;

            swap(r0, c0, r, c);
            refresh();
            Set<Integer> matched = findMatches();

            if (matched.isEmpty()) {
                soundFx.invalid();
                animateSwap(r0, c0, r, c, () -> {
                    if (ended) return;
                    swap(r0, c0, r, c);
                    refresh();
                    locked = false;
                });
                return;
            }

            resolveMatches(matched, 1);
        });
    }

    private void resolveMatches(Set<Integer> matched, int cascade) {
        if (ended) return;
        locked = true;
        soundFx.match(cascade);
        animateScorePulse();

        for (int index : matched) {
            int r = index / SIZE;
            int c = index % SIZE;
            board[r][c] = -1;
        }

        animatePop(matched, () -> {
            if (ended) return;

            score += matched.size() * cascade;
            scoreView.setText(activity.getString(R.string.minigame_score_fmt, score));
            collapseAndRefill();
            refresh();

            animateDrop(matched, () -> {
                if (ended) return;

                Set<Integer> next = findMatches();
                if (!next.isEmpty()) {
                    handler.postDelayed(() -> resolveMatches(next, cascade + 1), 55);
                    return;
                }

                if (!hasPossibleMove()) {
                    animateReshuffle(() -> locked = false);
                } else {
                    locked = false;
                }
            });
        });
    }

    private void animateSwap(int r1, int c1, int r2, int c2, Runnable after) {
        Button a = cells[r1][c1];
        Button b = cells[r2][c2];

        float dx = b.getX() - a.getX();
        float dy = b.getY() - a.getY();

        a.bringToFront();
        b.bringToFront();
        a.animate().translationX(dx).translationY(dy).setDuration(145).start();
        b.animate().translationX(-dx).translationY(-dy).setDuration(145).start();

        handler.postDelayed(() -> {
            a.animate().cancel();
            b.animate().cancel();
            a.setTranslationX(0f);
            a.setTranslationY(0f);
            b.setTranslationX(0f);
            b.setTranslationY(0f);
            after.run();
        }, 155);
    }

    private void animatePop(Set<Integer> matched, Runnable after) {
        for (int index : matched) {
            Button b = cells[index / SIZE][index % SIZE];
            b.animate()
                    .alpha(0f)
                    .scaleX(0.15f)
                    .scaleY(0.15f)
                    .rotation(14f)
                    .setDuration(145)
                    .start();
        }

        handler.postDelayed(() -> {
            for (int index : matched) {
                Button b = cells[index / SIZE][index % SIZE];
                b.setText("");
                b.setAlpha(0.08f);
                b.setScaleX(1f);
                b.setScaleY(1f);
                b.setRotation(0f);
            }
            after.run();
        }, 155);
    }

    private void animateDrop(Set<Integer> matched, Runnable after) {
        Set<Integer> affectedColumns = new HashSet<>();
        for (int index : matched) affectedColumns.add(index % SIZE);

        for (int c : affectedColumns) {
            for (int r = 0; r < SIZE; r++) {
                Button b = cells[r][c];
                b.setTranslationY(-dp(34 + (SIZE - r) * 4));
                b.setAlpha(0.28f);
                b.animate()
                        .translationY(0f)
                        .alpha(1f)
                        .setDuration(185 + r * 12L)
                        .start();
            }
        }

        handler.postDelayed(after, 270);
    }

    private void animateReshuffle(Runnable after) {
        if (ended) return;
        locked = true;
        hint.setText(activity.getString(R.string.match3_shuffle));
        soundFx.reshuffle();

        for (Button[] row : cells) {
            for (Button b : row) {
                b.animate().alpha(0.12f).scaleX(0.82f).scaleY(0.82f).setDuration(125).start();
            }
        }

        handler.postDelayed(() -> {
            if (ended) return;
            initBoard();
            refresh();
            for (Button[] row : cells) {
                for (Button b : row) {
                    b.setAlpha(0.12f);
                    b.setScaleX(0.82f);
                    b.setScaleY(0.82f);
                    b.animate().alpha(1f).scaleX(1f).scaleY(1f).setDuration(170).start();
                }
            }
            hint.setText(activity.getString(R.string.match3_hint));
            handler.postDelayed(after, 180);
        }, 135);
    }

    private void animateScorePulse() {
        scoreView.setScaleX(1.22f);
        scoreView.setScaleY(1.22f);
        scoreView.animate().scaleX(1f).scaleY(1f).setDuration(190).start();
    }

    private void showSelection(int r, int c) {
        refresh();
        Button b = cells[r][c];
        b.setBackground(round(
                Color.rgb(232,237,255),
                dp(12),
                dp(2),
                Color.rgb(47,82,235)));
        b.setScaleX(1.06f);
        b.setScaleY(1.06f);
    }

    private void initBoard() {
        int guard = 0;
        do {
            for (int r = 0; r < SIZE; r++) {
                for (int c = 0; c < SIZE; c++) {
                    int value;
                    do {
                        value = random.nextInt(GEMS.length);
                    } while ((c >= 2 && board[r][c-1] == value && board[r][c-2] == value)
                            || (r >= 2 && board[r-1][c] == value && board[r-2][c] == value));
                    board[r][c] = value;
                }
            }
            guard++;
        } while (!hasPossibleMove() && guard < 40);
    }

    private Set<Integer> findMatches() {
        Set<Integer> out = new HashSet<>();

        for (int r = 0; r < SIZE; r++) {
            int start = 0;
            for (int c = 1; c <= SIZE; c++) {
                if (c < SIZE && board[r][start] >= 0 && board[r][c] == board[r][start]) continue;
                if (board[r][start] >= 0 && c - start >= 3) {
                    for (int x = start; x < c; x++) out.add(r * SIZE + x);
                }
                start = c;
            }
        }

        for (int c = 0; c < SIZE; c++) {
            int start = 0;
            for (int r = 1; r <= SIZE; r++) {
                if (r < SIZE && board[start][c] >= 0 && board[r][c] == board[start][c]) continue;
                if (start < SIZE && board[start][c] >= 0 && r - start >= 3) {
                    for (int x = start; x < r; x++) out.add(x * SIZE + c);
                }
                start = r;
            }
        }
        return out;
    }

    private void collapseAndRefill() {
        for (int c = 0; c < SIZE; c++) {
            int write = SIZE - 1;
            for (int r = SIZE - 1; r >= 0; r--) {
                if (board[r][c] >= 0) board[write--][c] = board[r][c];
            }
            while (write >= 0) board[write--][c] = random.nextInt(GEMS.length);
        }
    }

    private boolean hasPossibleMove() {
        for (int r = 0; r < SIZE; r++) {
            for (int c = 0; c < SIZE; c++) {
                if (c + 1 < SIZE) {
                    swap(r,c,r,c+1);
                    boolean ok = !findMatches().isEmpty();
                    swap(r,c,r,c+1);
                    if (ok) return true;
                }
                if (r + 1 < SIZE) {
                    swap(r,c,r+1,c);
                    boolean ok = !findMatches().isEmpty();
                    swap(r,c,r+1,c);
                    if (ok) return true;
                }
            }
        }
        return false;
    }

    private void swap(int r1, int c1, int r2, int c2) {
        int t = board[r1][c1];
        board[r1][c1] = board[r2][c2];
        board[r2][c2] = t;
    }

    private void refresh() {
        for (int r = 0; r < SIZE; r++) {
            for (int c = 0; c < SIZE; c++) {
                Button b = cells[r][c];
                if (b == null) continue;
                b.animate().cancel();
                b.setTranslationX(0f);
                b.setTranslationY(0f);
                b.setRotation(0f);
                b.setAlpha(1f);
                b.setScaleX(1f);
                b.setScaleY(1f);
                b.setText(board[r][c] >= 0 ? GEMS[board[r][c]] : "");
                b.setBackground(round(Color.WHITE, dp(12), dp(1), Color.rgb(225,229,239)));
            }
        }
    }

    private void finishGame() {
        if (ended) return;
        ended = true;
        locked = true;
        if (timer != null) timer.cancel();

        int bonus = Math.min(config.scoreBonusCap,
                score / Math.max(1, config.scoreBonusEvery));
        int reward = config.completionReward + bonus;
        if (reward > 0) economy.credit(reward, "minigame_complete", config.id);

        for (Button[] row : cells) for (Button b : row) b.setEnabled(false);
        title.setText(activity.getString(R.string.minigame_finished));
        hint.setText(activity.getString(R.string.minigame_result_fmt, score, reward));
        timeView.setText("💎 " + economy.balance());

        Button cont = new Button(activity);
        cont.setText(activity.getString(R.string.minigame_continue));
        cont.setAllCaps(false);
        cont.setTextColor(Color.WHITE);
        cont.setTextSize(18);
        cont.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        cont.setBackground(round(Color.rgb(47,82,235), dp(14), 0, Color.TRANSPARENT));
        cont.setMinHeight(dp(56));
        cont.setOnClickListener(v -> onFinished.run());

        LinearLayout.LayoutParams lp = matchWrap();
        lp.topMargin = dp(12);
        root.addView(cont, lp);
    }

    private android.graphics.drawable.GradientDrawable round(
            int fill, int radius, int strokeWidth, int stroke) {
        android.graphics.drawable.GradientDrawable g =
                new android.graphics.drawable.GradientDrawable();
        g.setColor(fill);
        g.setCornerRadius(radius);
        if (strokeWidth > 0) g.setStroke(strokeWidth, stroke);
        return g;
    }

    private TextView label(String value, float sp, int color, int style) {
        TextView v = new TextView(activity);
        v.setText(value);
        v.setTextSize(sp);
        v.setTextColor(color);
        v.setTypeface(Typeface.DEFAULT, style);
        return v;
    }

    private LinearLayout.LayoutParams matchWrap() {
        return new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private int dp(int value) {
        return Math.round(value * activity.getResources().getDisplayMetrics().density);
    }
}
