package com.usernamemp.englishsprint;

import android.content.Context;
import android.media.MediaPlayer;
import android.speech.tts.TextToSpeech;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.Locale;

public final class AudioEngine implements TextToSpeech.OnInitListener {
    private final Context context;
    private final TextToSpeech tts;
    private boolean ttsReady = false;
    private MediaPlayer player;

    public AudioEngine(Context context) {
        this.context = context.getApplicationContext();
        this.tts = new TextToSpeech(this.context, this);
    }

    @Override
    public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS) {
            tts.setLanguage(Locale.US);
            tts.setSpeechRate(0.88f);
            tts.setPitch(1.0f);
            ttsReady = true;
        }
    }

    public void play(Question question) {
        stop();
        if (question.audioAsset != null && !question.audioAsset.isEmpty()) {
            try {
                File cached = new File(context.getCacheDir(),
                        question.audioAsset.replace("/", "_"));
                if (!cached.exists() || cached.length() == 0) {
                    try (InputStream in = context.getAssets().open(question.audioAsset);
                         FileOutputStream out = new FileOutputStream(cached)) {
                        byte[] buffer = new byte[16 * 1024];
                        int read;
                        while ((read = in.read(buffer)) > 0) {
                            out.write(buffer, 0, read);
                        }
                    }
                }
                player = new MediaPlayer();
                player.setDataSource(cached.getAbsolutePath());
                player.prepare();
                player.start();
                return;
            } catch (Exception ignored) {
                // Fall through to system TTS. The CI-built APK normally contains bundled WAV files.
            }
        }

        if (ttsReady && question.speechText != null && !question.speechText.isEmpty()) {
            tts.speak(question.speechText, TextToSpeech.QUEUE_FLUSH, null, question.id);
        }
    }

    public void stop() {
        try {
            if (player != null) {
                if (player.isPlaying()) player.stop();
                player.release();
                player = null;
            }
        } catch (Exception ignored) {
        }
        if (ttsReady) tts.stop();
    }

    public void shutdown() {
        stop();
        tts.shutdown();
    }
}
