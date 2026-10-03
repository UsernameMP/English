package com.usernamemp.englishsprint;

import android.app.Activity;
import android.content.SharedPreferences;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;

public final class MiniGameSoundFx {
    private final SharedPreferences settings;

    public MiniGameSoundFx(Activity activity) {
        settings = activity.getSharedPreferences("english_sprint_settings", Activity.MODE_PRIVATE);
    }

    public void select() { play(new double[]{520.0}, 34, 0.18); }
    public void swap() { play(new double[]{500.0, 650.0}, 42, 0.20); }
    public void invalid() { play(new double[]{330.0, 260.0}, 52, 0.16); }
    public void match(int cascade) {
        double base = Math.min(1250.0, 700.0 + cascade * 115.0);
        play(new double[]{base, base * 1.20, base * 1.48}, 58, Math.min(0.30, 0.21 + cascade * 0.025));
    }
    public void reshuffle() { play(new double[]{380.0, 470.0, 590.0}, 48, 0.18); }

    private void play(double[] frequencies, int noteMs, double strength) {
        if (!settings.getBoolean("sound", true)) return;
        int volumeSetting = Math.max(0, Math.min(100, settings.getInt("volume", 80)));
        if (volumeSetting == 0) return;

        new Thread(() -> {
            try {
                final int sampleRate = 22050;
                int gapMs = 10;
                int noteSamples = sampleRate * noteMs / 1000;
                int gapSamples = sampleRate * gapMs / 1000;
                byte[] pcm = new byte[frequencies.length * (noteSamples + gapSamples) * 2];
                int offset = 0;
                double volume = volumeSetting / 100.0;

                for (double frequency : frequencies) {
                    for (int i = 0; i < noteSamples; i++) {
                        double t = i / (double) sampleRate;
                        double attack = Math.min(1.0, i / (sampleRate * 0.006));
                        double release = Math.min(1.0, (noteSamples - i) / (sampleRate * 0.018));
                        double envelope = Math.max(0.0, Math.min(attack, release));
                        double wave = Math.sin(2.0 * Math.PI * frequency * t)
                                + 0.12 * Math.sin(2.0 * Math.PI * frequency * 2.0 * t);
                        short sample = (short) (Short.MAX_VALUE * strength * volume * envelope * wave);
                        pcm[offset++] = (byte) (sample & 0xff);
                        pcm[offset++] = (byte) ((sample >> 8) & 0xff);
                    }
                    for (int i = 0; i < gapSamples; i++) {
                        pcm[offset++] = 0;
                        pcm[offset++] = 0;
                    }
                }

                AudioTrack track = new AudioTrack(
                        AudioManager.STREAM_MUSIC,
                        sampleRate,
                        AudioFormat.CHANNEL_OUT_MONO,
                        AudioFormat.ENCODING_PCM_16BIT,
                        pcm.length,
                        AudioTrack.MODE_STATIC
                );
                track.write(pcm, 0, pcm.length);
                track.play();
                Thread.sleep(Math.max(120L, frequencies.length * (noteMs + gapMs) + 40L));
                try { track.stop(); } catch (Exception ignored) {}
                track.release();
            } catch (Exception ignored) {
            }
        }, "minigame-sfx").start();
    }
}
