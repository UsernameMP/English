package com.usernamemp.englishsprint;

import android.content.Context;
import android.content.res.AssetManager;
import com.k2fsa.sherpa.onnx.FeatureConfig;
import com.k2fsa.sherpa.onnx.OnlineModelConfig;
import com.k2fsa.sherpa.onnx.OnlineRecognizer;
import com.k2fsa.sherpa.onnx.OnlineRecognizerConfig;
import com.k2fsa.sherpa.onnx.OnlineRecognizerResult;
import com.k2fsa.sherpa.onnx.OnlineStream;
import com.k2fsa.sherpa.onnx.OnlineToneCtcModelConfig;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.security.MessageDigest;
import java.util.Locale;

/** T-One 71M recognizer. Only microphone PCM is decoded; no network or audio uploads. */
public final class OfflineTOneEngine {
    private OfflineTOneEngine() {}
    private static final Object LOCK = new Object();
    private static final String MODEL_ASSET = "models/t-one-71m/model.onnx";
    private static final String TOKENS_ASSET = "models/t-one-71m/tokens.txt";
    public static final String VERSION = "t-one-71m-2025-09-08-sherpa-onnx-1.13.8";
    // Actual SHA-256 of the upstream Hugging Face LFS object at pinned revision 9d63341.
    public static final String MODEL_SHA256 =
            "5ded080e2a6c86ecc11bcb0902d77524eb3e8b0844cb0c0754347f5aafb4dabc";

    public static final class Transcription {
        public final String text, modelVersion, modelSha256;
        Transcription(String text, String version, String sha) {
            this.text = text;
            this.modelVersion = version;
            this.modelSha256 = sha;
        }
    }

    private static File directory(Context ctx) {
        return new File(ctx.getNoBackupFilesDir(), "t-one-71m-2025-09-08");
    }

    private static String sha256(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream in = new FileInputStream(file)) {
            byte[] b = new byte[65536];
            int n;
            while ((n = in.read(b)) != -1) if (n > 0) digest.update(b, 0, n);
        }
        StringBuilder value = new StringBuilder(64);
        for (byte b : digest.digest())
            value.append(String.format(Locale.ROOT, "%02x", b & 255));
        return value.toString();
    }

    private static void extract(AssetManager assets, String assetName, File output)
            throws IOException {
        File temp = new File(output.getParentFile(), output.getName() + ".part");
        try {
            try (InputStream in = assets.open(assetName);
                 FileOutputStream out = new FileOutputStream(temp)) {
                byte[] buffer = new byte[65536];
                int size;
                while ((size = in.read(buffer)) != -1) if (size > 0) out.write(buffer, 0, size);
                out.getFD().sync();
            }
            if (!temp.renameTo(output))
                throw new IOException("Cannot commit offline ASR model asset");
        } finally {
            if (temp.exists()) temp.delete();
        }
    }

    private static byte[] fileBytes(File file) throws IOException {
        if (file.length() > 16000L * 2 * 90 + 2)
            throw new IOException("PCM exceeds 90 seconds");
        try (InputStream in = new FileInputStream(file);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buf = new byte[65536];
            int n;
            while ((n = in.read(buf)) != -1) if (n > 0) out.write(buf, 0, n);
            return out.toByteArray();
        }
    }

    public static void ensureBundled(Context ctx, String locale) throws Exception {
        if (!"ru".equals(locale)) throw new IllegalArgumentException("Russian ASR only");
        synchronized (LOCK) {
            File dir = directory(ctx);
            if (!dir.isDirectory() && !dir.mkdirs())
                throw new IOException("Cannot prepare ASR private storage");
            File model = new File(dir, "model.onnx");
            File tokens = new File(dir, "tokens.txt");
            if (!model.isFile() || !MODEL_SHA256.equals(sha256(model))) {
                if (model.exists() && !model.delete()) throw new IOException("Corrupt model locked");
                extract(ctx.getAssets(), MODEL_ASSET, model);
                if (!MODEL_SHA256.equals(sha256(model))) {
                    model.delete();
                    throw new SecurityException("Bundled T-One model checksum mismatch");
                }
            }
            if (!tokens.isFile() || tokens.length() < 100)
                extract(ctx.getAssets(), TOKENS_ASSET, tokens);
            // T-One exported tokens MUST provide the CTC blank token.
            if (!new String(fileBytes(tokens),
                    java.nio.charset.StandardCharsets.UTF_8).contains("<blk> 34"))
                throw new SecurityException("T-One vocabulary is invalid");
        }
    }

    public static Transcription recognize(Context ctx, String locale, File rawPcm)
            throws Exception {
        ensureBundled(ctx, locale);
        File dir = directory(ctx);
        File model = new File(dir, "model.onnx");
        File tokens = new File(dir, "tokens.txt");
        if (rawPcm.length() > 16000L * 2 * 90 + 2)
            throw new IOException("Voice attempt exceeds 90 seconds");
        byte[] pcm = fileBytes(rawPcm);
        float[] samples = Pcm16To8kResampler.convert(pcm);
        if (samples.length < 800) throw new IOException("Speech segment too short");

        // Published Android AAR exposes Kotlin data classes, not the JVM Builder API.
        OnlineToneCtcModelConfig tOne = new OnlineToneCtcModelConfig();
        tOne.setModel(model.getAbsolutePath());
        OnlineModelConfig modelConfig = new OnlineModelConfig();
        modelConfig.setToneCtc(tOne);
        modelConfig.setTokens(tokens.getAbsolutePath());
        modelConfig.setNumThreads(2);
        modelConfig.setProvider("cpu");
        modelConfig.setDebug(false);

        FeatureConfig features = new FeatureConfig();
        features.setSampleRate(8000);
        features.setFeatureDim(80);
        features.setDither(0f);

        OnlineRecognizerConfig cfg = new OnlineRecognizerConfig();
        cfg.setModelConfig(modelConfig);
        cfg.setFeatConfig(features);
        cfg.setEnableEndpoint(false);
        cfg.setDecodingMethod("greedy_search");

        OnlineRecognizer recognizer = new OnlineRecognizer(null, cfg);
        OnlineStream stream = null;
        try {
            stream = recognizer.createStream("");
            // Upstream T-One example pads 0.3 seconds before and 0.6 after speech.
            stream.acceptWaveform(new float[2400], 8000);
            for (int offset = 0; offset < samples.length; offset += 2400) {
                int count = Math.min(2400, samples.length - offset);
                float[] block = new float[count];
                System.arraycopy(samples, offset, block, 0, count);
                stream.acceptWaveform(block, 8000);
                while (recognizer.isReady(stream)) recognizer.decode(stream);
            }
            stream.acceptWaveform(new float[4800], 8000);
            stream.inputFinished();
            while (recognizer.isReady(stream)) recognizer.decode(stream);
            OnlineRecognizerResult result = recognizer.getResult(stream);
            // Do not normalize punctuation, repetitions, numbers, negatives or corrections.
            return new Transcription(result.getText(), VERSION, MODEL_SHA256);
        } finally {
            if (stream != null) stream.release();
            recognizer.release();
        }
    }
}
