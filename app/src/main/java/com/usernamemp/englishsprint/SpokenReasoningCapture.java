package com.usernamemp.englishsprint;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.UUID;

/** Single foreground session. Uncompressed PCM exists only in app-private cache. */
public final class SpokenReasoningCapture {
    private static final int HZ = 16000;
    private static final int MAX_BYTES = 16000 * 2 * 90;
    private final Context context;
    private AudioRecord recorder;
    private Thread worker;
    private File raw;
    private volatile boolean active;
    private volatile String failure;

    public SpokenReasoningCapture(Context context) { this.context = context; }

    public synchronized void start() throws Exception {
        if (active) throw new IllegalStateException("Already recording");
        if (context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED)
            throw new SecurityException("Microphone not permitted");
        int min = AudioRecord.getMinBufferSize(HZ, AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT);
        if (min <= 0) throw new IOException("16kHz mono recording unsupported");
        recorder = new AudioRecord(MediaRecorder.AudioSource.MIC, HZ,
                AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT,
                Math.max(8192,min * 2));
        if (recorder.getState() != AudioRecord.STATE_INITIALIZED) {
            recorder.release();
            recorder = null;
            throw new IOException("Microphone unavailable");
        }
        raw = new File(context.getCacheDir(), "reasoning_" + UUID.randomUUID() + ".pcm");
        failure = null;
        try { recorder.startRecording(); }
        catch (RuntimeException e) { recorder.release(); recorder=null; throw e; }
        active = true;
        worker = new Thread(() -> {
            byte[] bytes = new byte[8192];
            int total = 0;
            try (FileOutputStream out = new FileOutputStream(raw)) {
                while (active && total < MAX_BYTES) {
                    int count = recorder.read(bytes, 0, Math.min(bytes.length, MAX_BYTES-total));
                    if (count < 0) { failure = "Audio input error: " + count; break; }
                    if (count > 0) { out.write(bytes,0,count); total += count; }
                }
            } catch (Exception e) { failure = e.getClass().getSimpleName(); }
            active = false;
        }, "rift-voice-pcm");
        worker.start();
    }
    public synchronized boolean isRecording() { return active; }
    public synchronized File stop() throws Exception {
        active = false;
        if (recorder != null) {
            try { recorder.stop(); } catch (IllegalStateException ignored) { }
        }
        if (worker != null) worker.join(4000);
        if (worker != null && worker.isAlive()) {
            // Do not let the microphone leak if a read thread becomes unresponsive.
            if (recorder != null) recorder.release();
            recorder = null;
            worker.join(1000);
            if (worker.isAlive()) throw new IOException("Recording did not stop");
        }
        if (recorder != null) recorder.release();
        recorder = null;
        worker = null;
        File completed = raw;
        raw = null;
        if (completed == null || !completed.exists() || completed.length() < 3200 || failure != null) {
            if (completed != null) completed.delete();
            throw new IOException(failure == null ? "No audio received" : failure);
        }
        return completed;
    }
    public synchronized void cancel() {
        try { File f = stop(); if (f != null) f.delete(); }
        catch (Exception ignored) { if (raw != null) raw.delete(); raw = null; }
    }
}
