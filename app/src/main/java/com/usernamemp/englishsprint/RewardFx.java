package com.usernamemp.englishsprint;

import android.animation.AnimatorSet;
import android.animation.ObjectAnimator;
import android.app.Activity;
import android.graphics.Color;
import android.content.SharedPreferences;
import android.graphics.Typeface;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.media.ToneGenerator;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.HapticFeedbackConstants;
import android.view.View;
import android.view.ViewGroup;
import android.view.animation.OvershootInterpolator;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.Random;

public final class RewardFx {
    public static final class Reaction {
        public final String symbol;
        public final String headline;
        public final String subline;
        public final boolean major;

        Reaction(String symbol, String headline, String subline, boolean major) {
            this.symbol = symbol;
            this.headline = headline;
            this.subline = subline;
            this.major = major;
        }
    }

    private static final String[][] QUOTES = {
            {"Don't count the days; make the days count.", "Muhammad Ali · boxer"},
            {"Nothing in life is to be feared; it is only to be understood.", "Marie Curie · scientist"},
            {"Success is the sum of small efforts, repeated day in and day out.", "Robert Collier · writer"},
            {"It always seems impossible until it's done.", "Nelson Mandela · statesman"},
            {"The secret of getting ahead is getting started.", "Mark Twain · writer"}
    };

    private final Activity activity;
    private final SharedPreferences settings;
    private final Random random = new Random();
    private final Handler handler = new Handler(Looper.getMainLooper());
    private ToneGenerator tone;

    public RewardFx(Activity activity) {
        this.activity = activity;
        this.settings = activity.getSharedPreferences("english_sprint_settings", Activity.MODE_PRIVATE);
        rebuildTone(settings.getInt("volume", 80));
    }

    public Reaction reaction(boolean correct, int combo) {
        if (correct) {
            if (combo >= 15) return new Reaction("🏆",
                    activity.getString(R.string.rank_unstoppable),
                    activity.getString(R.string.reaction_unstoppable_sub, combo), true);
            if (combo >= 10) return new Reaction("⚡",
                    activity.getString(R.string.rank_legend),
                    activity.getString(R.string.reaction_legend_sub, combo), true);
            if (combo >= 8) return new Reaction("🔥",
                    activity.getString(R.string.rank_machine),
                    activity.getString(R.string.reaction_machine_sub, combo), true);
            if (combo >= 5) return new Reaction("🥊",
                    activity.getString(R.string.rank_five),
                    activity.getString(R.string.reaction_five_sub, combo), true);
            if (combo == 3) return new Reaction("👍",
                    activity.getString(R.string.rank_warmup),
                    activity.getString(R.string.reaction_warmup_sub), true);
            if (combo == 2) return new Reaction("+",
                    activity.getString(R.string.reaction_streak), "×2", false);
            return new Reaction("+", activity.getString(R.string.reaction_correct), "+XP", false);
        }

        String[][] lines = {
                {"↻", activity.getString(R.string.reaction_ok), activity.getString(R.string.reaction_ok_sub)},
                {"→", activity.getString(R.string.reaction_next), activity.getString(R.string.reaction_next_sub)},
                {"◉", activity.getString(R.string.reaction_saved), activity.getString(R.string.reaction_saved_sub)},
                {"↗", activity.getString(R.string.reaction_next_round), activity.getString(R.string.reaction_next_round_sub)}
        };
        String[] line = lines[random.nextInt(lines.length)];
        return new Reaction(line[0], line[1], line[2], false);
    }

    public String quoteForMistake() {
        if (!settings.getBoolean("quotes", true)) return "";
        if (random.nextInt(3) != 0) return "";
        String[] q = QUOTES[random.nextInt(QUOTES.length)];
        return "“" + q[0] + "”\n" + q[1];
    }

    public void play(Reaction reaction, boolean correct, int combo) {
        if (correct && (combo == 3 || combo == 5 || combo == 8 || combo == 10 || combo == 15)) {
            majorBurst(reaction, combo);
        } else {
            smallPulse(reaction, correct);
        }
    }

    public int volume() {
        return settings.getInt("volume", 80);
    }

    public void setVolume(int volume) {
        int safe = Math.max(0, Math.min(100, volume));
        settings.edit().putInt("volume", safe).apply();
        rebuildTone(safe);
    }

    public void playNewRecord(int combo) {
        majorBurst(new Reaction("🏅",
                activity.getString(R.string.new_record),
                activity.getString(R.string.new_record_sub, combo), true), Math.max(combo, 10));
    }

    private void rebuildTone(int volume) {
        if (tone != null) {
            try { tone.release(); } catch (Exception ignored) {}
            tone = null;
        }
        try {
            tone = new ToneGenerator(AudioManager.STREAM_MUSIC, volume);
        } catch (Exception ignored) {
        }
    }

    private void majorBurst(Reaction reaction, int combo) {
        View decor = activity.getWindow().getDecorView();
        if (settings.getBoolean("haptic", true)) {
            decor.performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);
        }

        if (settings.getBoolean("sound", true)) {
            playPositiveChime(true, combo);
        }

        FrameLayout host = activity.findViewById(android.R.id.content);
        if (host == null) return;

        LinearLayout card = new LinearLayout(activity);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setGravity(Gravity.CENTER);
        card.setPadding(dp(26), dp(22), dp(26), dp(22));
        card.setBackground(Shapes.round(Color.rgb(18, 23, 38), dp(24), 0, Color.TRANSPARENT));
        card.setAlpha(0f);
        card.setScaleX(0.45f);
        card.setScaleY(0.45f);

        TextView symbol = label(reaction.symbol, 52, Color.WHITE, Typeface.BOLD);
        TextView headline = label(reaction.headline, 28, Color.WHITE, Typeface.BOLD);
        TextView sub = label(reaction.subline, 16, Color.rgb(205, 216, 255), Typeface.BOLD);
        symbol.setGravity(Gravity.CENTER);
        headline.setGravity(Gravity.CENTER);
        sub.setGravity(Gravity.CENTER);
        sub.setPadding(0, dp(6), 0, 0);

        card.addView(symbol);
        card.addView(headline);
        card.addView(sub);

        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.CENTER);
        lp.leftMargin = dp(24);
        lp.rightMargin = dp(24);
        host.addView(card, lp);

        AnimatorSet in = new AnimatorSet();
        in.playTogether(
                ObjectAnimator.ofFloat(card, View.ALPHA, 0f, 1f),
                ObjectAnimator.ofFloat(card, View.SCALE_X, 0.45f, 1f),
                ObjectAnimator.ofFloat(card, View.SCALE_Y, 0.45f, 1f)
        );
        in.setDuration(260);
        in.setInterpolator(new OvershootInterpolator(1.4f));
        in.start();

        handler.postDelayed(() -> {
            if (card.getParent() == null) return;
            AnimatorSet out = new AnimatorSet();
            out.playTogether(
                    ObjectAnimator.ofFloat(card, View.ALPHA, 1f, 0f),
                    ObjectAnimator.ofFloat(card, View.SCALE_X, 1f, 1.08f),
                    ObjectAnimator.ofFloat(card, View.SCALE_Y, 1f, 1.08f)
            );
            out.setDuration(220);
            out.addListener(new android.animation.AnimatorListenerAdapter() {
                @Override public void onAnimationEnd(android.animation.Animator animation) {
                    if (card.getParent() != null) host.removeView(card);
                }
            });
            out.start();
        }, 900);
    }

    private void smallPulse(Reaction reaction, boolean positive) {
        if (settings.getBoolean("sound", true)) {
            if (positive) {
                playPositiveChime(false, 1);
            } else if (tone != null) {
                try { tone.startTone(ToneGenerator.TONE_PROP_NACK, 70); } catch (Exception ignored) {}
            }
        }

        FrameLayout host = activity.findViewById(android.R.id.content);
        if (host == null) return;

        TextView chip = label(reaction.symbol + "  " + reaction.headline, 15,
                positive ? Color.rgb(15, 105, 67) : Color.rgb(96, 105, 122),
                Typeface.BOLD);
        chip.setPadding(dp(16), dp(10), dp(16), dp(10));
        chip.setBackground(Shapes.round(Color.WHITE, dp(24), dp(1), Color.rgb(225, 229, 239)));
        chip.setAlpha(0f);
        chip.setTranslationY(dp(18));

        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.TOP | Gravity.CENTER_HORIZONTAL);
        lp.topMargin = dp(74);
        host.addView(chip, lp);

        AnimatorSet in = new AnimatorSet();
        in.playTogether(
                ObjectAnimator.ofFloat(chip, View.ALPHA, 0f, 1f),
                ObjectAnimator.ofFloat(chip, View.TRANSLATION_Y, dp(18), 0f)
        );
        in.setDuration(150);
        in.start();

        handler.postDelayed(() -> {
            if (chip.getParent() == null) return;
            AnimatorSet out = new AnimatorSet();
            out.playTogether(
                    ObjectAnimator.ofFloat(chip, View.ALPHA, 1f, 0f),
                    ObjectAnimator.ofFloat(chip, View.TRANSLATION_Y, 0f, -dp(14))
            );
            out.setDuration(170);
            out.addListener(new android.animation.AnimatorListenerAdapter() {
                @Override public void onAnimationEnd(android.animation.Animator animation) {
                    if (chip.getParent() != null) host.removeView(chip);
                }
            });
            out.start();
        }, 520);
    }

    private void playPositiveChime(boolean major, int combo) {
        final int volume = Math.max(0, Math.min(100, settings.getInt("volume", 80)));
        final String pack = soundPack();

        new Thread(() -> {
            try {
                double[] notes;
                int noteMs;
                if ("soft".equals(pack)) {
                    notes = major ? new double[]{659.25, 783.99, 987.77, 1318.51}
                            : new double[]{783.99, 987.77, 1174.66};
                    noteMs = major ? 105 : 70;
                } else if ("arcade".equals(pack)) {
                    notes = major ? new double[]{783.99, 1046.50, 1318.51, 1760.00}
                            : new double[]{987.77, 1318.51, 1567.98};
                    noteMs = major ? 90 : 62;
                } else {
                    notes = major ? new double[]{659.25, 880.00, 1174.66, 1567.98}
                            : new double[]{880.00, 1174.66, 1567.98};
                    noteMs = major ? 95 : 65;
                }

                if (major && combo >= 10) {
                    notes = new double[]{659.25, 880.00, 1174.66, 1567.98, 2093.00};
                }

                byte[] pcm = buildChime(notes, noteMs, major ? 22 : 14, volume / 100.0);
                AudioTrack track = new AudioTrack(
                        AudioManager.STREAM_MUSIC,
                        22050,
                        AudioFormat.CHANNEL_OUT_MONO,
                        AudioFormat.ENCODING_PCM_16BIT,
                        pcm.length,
                        AudioTrack.MODE_STATIC
                );
                track.write(pcm, 0, pcm.length);
                track.play();
                Thread.sleep(Math.max(220, notes.length * (noteMs + (major ? 22 : 14)) + 90L));
                try { track.stop(); } catch (Exception ignored) {}
                track.release();
            } catch (Exception ignored) {
            }
        }, major ? "reward-chime-major" : "reward-chime").start();
    }

    private byte[] buildChime(double[] frequencies, int noteMs, int gapMs, double volume) {
        final int sampleRate = 22050;
        int noteSamples = sampleRate * noteMs / 1000;
        int gapSamples = sampleRate * gapMs / 1000;
        int total = frequencies.length * (noteSamples + gapSamples);
        byte[] out = new byte[total * 2];
        int offset = 0;

        for (double frequency : frequencies) {
            for (int i = 0; i < noteSamples; i++) {
                double t = i / (double) sampleRate;
                double attack = Math.min(1.0, i / (sampleRate * 0.010));
                double release = Math.min(1.0, (noteSamples - i) / (sampleRate * 0.025));
                double envelope = Math.max(0.0, Math.min(attack, release));
                double fundamental = Math.sin(2.0 * Math.PI * frequency * t);
                double sparkle = 0.22 * Math.sin(2.0 * Math.PI * frequency * 2.0 * t);
                short sample = (short) (Short.MAX_VALUE * 0.36 * volume * envelope * (fundamental + sparkle));
                out[offset++] = (byte) (sample & 0xff);
                out[offset++] = (byte) ((sample >> 8) & 0xff);
            }
            for (int i = 0; i < gapSamples; i++) {
                out[offset++] = 0;
                out[offset++] = 0;
            }
        }
        return out;
    }

    private String soundPack() {
        return activity.getSharedPreferences(ShopStore.PREFS, Activity.MODE_PRIVATE)
                .getString("equipped_sound", "default");
    }

    public void shutdown() {
        if (tone != null) {
            tone.release();
            tone = null;
        }
    }

    private TextView label(String text, float sp, int color, int style) {
        TextView v = new TextView(activity);
        v.setText(text);
        v.setTextSize(sp);
        v.setTextColor(color);
        v.setTypeface(Typeface.DEFAULT, style);
        return v;
    }

    private int dp(int value) {
        return Math.round(value * activity.getResources().getDisplayMetrics().density);
    }

    static final class Shapes {
        static android.graphics.drawable.GradientDrawable round(int fill, int radius, int strokeWidth, int stroke) {
            android.graphics.drawable.GradientDrawable g = new android.graphics.drawable.GradientDrawable();
            g.setColor(fill);
            g.setCornerRadius(radius);
            if (strokeWidth > 0) g.setStroke(strokeWidth, stroke);
            return g;
        }
    }
}
