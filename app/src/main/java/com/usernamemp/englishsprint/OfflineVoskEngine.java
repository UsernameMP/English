package com.usernamemp.englishsprint;

import android.content.Context;
import org.json.JSONObject;
import org.vosk.Model;
import org.vosk.Recognizer;
import java.io.File;
import java.io.FileInputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * Offline Russian model is shipped inside APK assets; extracted privately on first use.
 * Each model has manifest.json with locale, version, sha256 and model_file.
 * No online speech recognizer fallback: offline is a hard guarantee.
 */
public final class OfflineVoskEngine {
    private OfflineVoskEngine() { }
    private static final Object BUNDLE_LOCK = new Object();
    public static final String RU_ARCHIVE_SHA256 =
            "961d5ff98a17f4aa6de69864d0aa71fa5bac682301d2b5d17a3f24c5c99a46d4";
    public static void ensureBundled(Context ctx, String locale) throws Exception {
        if (!"ru".equals(locale)) throw new IllegalStateException("Only bundled Russian ASR is enabled");
        synchronized (BUNDLE_LOCK) {
            File manifest = new File(directory(ctx, locale), "manifest.json");
            if (manifest.isFile()) {
                try (FileInputStream in = new FileInputStream(manifest)) {
                    byte[] meta = new byte[(int) manifest.length()];
                    int offset = 0, n;
                    while (offset < meta.length && (n = in.read(meta,offset,meta.length-offset)) > 0)
                        offset += n;
                    if (offset == meta.length && RU_ARCHIVE_SHA256.equals(
                            new JSONObject(new String(meta,StandardCharsets.UTF_8))
                                .optString("archive_sha256","")))
                        return;
                } catch (Exception ignored) { /* Reinstall validated bundled model. */ }
            }
            try (java.io.InputStream asset = ctx.getAssets().open(
                    "models/vosk-model-small-ru-0.22.zip")) {
                importZip(ctx,locale,asset);
            }
            File installed = new File(directory(ctx,locale), "manifest.json");
            JSONObject verified;
            try (FileInputStream in = new FileInputStream(installed)) {
                java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream();
                byte[] buffer = new byte[4096]; int n;
                while ((n = in.read(buffer)) != -1) bytes.write(buffer,0,n);
                verified = new JSONObject(bytes.toString("UTF-8"));
            }
            if (!RU_ARCHIVE_SHA256.equals(verified.optString("archive_sha256",""))) {
                deleteRecursive(directory(ctx,locale));
                throw new SecurityException("APK offline ASR model SHA-256 mismatch");
            }
        }
    }
    public static File directory(Context ctx, String locale) {
        return new File(new File(ctx.getNoBackupFilesDir(), "vosk_models"),
                "en".equals(locale) ? "en" : "ru");
    }
    public static boolean hasModel(Context ctx, String locale) {
        return new File(directory(ctx,locale), "manifest.json").isFile();
    }
    public static final class Transcription {
        public final String text, modelVersion, modelSha256;
        Transcription(String text,String version,String sha) {
            this.text=text; modelVersion=version; modelSha256=sha;
        }
    }
    public static Transcription recognize(Context ctx, String locale, File pcm) throws Exception {
        File directory = directory(ctx,locale);
        File manifest = new File(directory, "manifest.json");
        if (!manifest.isFile()) throw new IllegalStateException("Offline ASR model not installed");
        byte[] meta = new byte[(int)manifest.length()];
        try (FileInputStream in = new FileInputStream(manifest)) {
            if (in.read(meta) != meta.length) throw new IllegalStateException("Invalid model manifest");
        }
        JSONObject m = new JSONObject(new String(meta,StandardCharsets.UTF_8));
        if (!locale.equals(m.getString("locale"))) throw new SecurityException("Model locale mismatch");
        String part = m.getString("model_file");
        File weights = new File(directory, part);
        if (!weights.getCanonicalPath().startsWith(directory.getCanonicalPath() + File.separator))
            throw new SecurityException("Model path escapes app storage");
        String pinned = m.getString("sha256").toLowerCase(java.util.Locale.ROOT);
        if (!pinned.matches("[0-9a-f]{64}")) throw new SecurityException("Missing model checksum");
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (FileInputStream in = new FileInputStream(weights)) {
            byte[] buffer = new byte[65536]; int n;
            while ((n = in.read(buffer)) >= 0) if (n > 0) digest.update(buffer,0,n);
        }
        StringBuilder actual = new StringBuilder();
        for (byte b : digest.digest()) actual.append(String.format(java.util.Locale.ROOT,"%02x",b & 255));
        if (!pinned.equals(actual.toString())) throw new SecurityException("Model checksum mismatch");
        String text;
        try (Model model = new Model(directory.getAbsolutePath());
             Recognizer rec = new Recognizer(model, 16000f);
             FileInputStream in = new FileInputStream(pcm)) {
            byte[] buffer = new byte[8192]; int n;
            while ((n = in.read(buffer)) >= 0) if (n > 0) rec.acceptWaveForm(buffer,n);
            text = new JSONObject(rec.getFinalResult()).optString("text", "");
        }
        return new Transcription(text,m.getString("version"),pinned);
    }

    /** Internal bundled ZIP unpacker; this is not a user-visible import flow. */
    private static String importZip(Context ctx, String locale, java.io.InputStream input) throws Exception {
        if (!"ru".equals(locale) && !"en".equals(locale))
            throw new IllegalArgumentException("Unsupported locale");
        File models = new File(ctx.getNoBackupFilesDir(), "vosk_models");
        if (!models.isDirectory() && !models.mkdirs()) throw new java.io.IOException("No model directory");
        File zipFile = new File(ctx.getCacheDir(), "model-import-" + java.util.UUID.randomUUID() + ".zip");
        File staging = new File(models, locale + "-staging-" + java.util.UUID.randomUUID());
        final long maxZip = 120L * 1024 * 1024;
        final long maxUnpacked = 300L * 1024 * 1024;
        try {
            MessageDigest zipHash = MessageDigest.getInstance("SHA-256");
            try (java.io.FileOutputStream out = new java.io.FileOutputStream(zipFile)) {
                byte[] bytes = new byte[65536]; long size=0; int n;
                while ((n=input.read(bytes)) != -1) {
                    size+=n;
                    if(size>maxZip) throw new java.io.IOException("ZIP exceeds 120 MiB");
                    out.write(bytes,0,n); zipHash.update(bytes,0,n);
                }
            }
            if (!staging.mkdirs()) throw new java.io.IOException("Cannot stage model");
            String prefix=null;
            long unpacked=0; int entries=0;
            try (java.util.zip.ZipInputStream zip=new java.util.zip.ZipInputStream(
                    new FileInputStream(zipFile))) {
                java.util.zip.ZipEntry e;
                byte[] buffer=new byte[65536];
                while((e=zip.getNextEntry()) != null) {
                    if(++entries>5000) throw new SecurityException("Too many model files");
                    String path=e.getName().replace('\\','/');
                    if (path.startsWith("/") || path.contains("../") || path.startsWith("../"))
                        throw new SecurityException("Unsafe model ZIP path");
                    if(prefix==null) {
                        int split=path.indexOf('/');
                        prefix=split<0?"":path.substring(0,split+1);
                    }
                    if(!path.startsWith(prefix)) throw new SecurityException("Mixed ZIP roots");
                    path=path.substring(prefix.length());
                    if(path.isEmpty()) continue;
                    if(path.startsWith("/") || path.contains("..") || path.indexOf(':')>=0)
                        throw new SecurityException("Unsafe model file");
                    File target = new File(staging,path);
                    if(!target.getCanonicalPath().startsWith(staging.getCanonicalPath()+File.separator))
                        throw new SecurityException("Model path escape");
                    if(e.isDirectory()) {
                        if(!target.isDirectory() && !target.mkdirs())
                            throw new java.io.IOException("Model directory creation failed");
                        continue;
                    }
                    if (!target.getParentFile().isDirectory() && !target.getParentFile().mkdirs())
                        throw new java.io.IOException("Model directory unavailable");
                    try (java.io.FileOutputStream out=new java.io.FileOutputStream(target)) {
                        int n;
                        while((n=zip.read(buffer))!=-1) {
                            unpacked+=n;
                            if(unpacked>maxUnpacked) throw new java.io.IOException("Unpacked model too large");
                            out.write(buffer,0,n);
                        }
                    }
                    zip.closeEntry();
                }
            }
            File weights=new File(staging,"am/final.mdl");
            File conf=new File(staging,"conf/model.conf");
            if (!weights.isFile() || !conf.isFile())
                throw new java.io.IOException("Not a Vosk model: missing am/final.mdl or conf/model.conf");
            MessageDigest hash=MessageDigest.getInstance("SHA-256");
            try(FileInputStream in=new FileInputStream(weights)) {
                byte[] b=new byte[65536];int n;
                while((n=in.read(b))!=-1) if(n>0) hash.update(b,0,n);
            }
            String modelSha=hex(hash.digest());
            JSONObject manifest=new JSONObject();
            manifest.put("locale",locale);
            manifest.put("version",prefix==null?"user-imported":prefix.replace("/",""));
            manifest.put("sha256",modelSha);
            manifest.put("model_file","am/final.mdl");
            manifest.put("archive_sha256",hex(zipHash.digest()));
            manifest.put("origin","user_imported_unverified");
            try (java.io.FileOutputStream out=new java.io.FileOutputStream(new File(staging,"manifest.json"))) {
                out.write(manifest.toString().getBytes(StandardCharsets.UTF_8));
            }
            File destination=directory(ctx,locale);
            File previous=new File(models,locale+"-previous");
            deleteRecursive(previous);
            if(destination.exists() && !destination.renameTo(previous))
                throw new java.io.IOException("Existing model cannot be replaced");
            if(!staging.renameTo(destination)) {
                if(previous.exists()) previous.renameTo(destination);
                throw new java.io.IOException("Model activation failed");
            }
            deleteRecursive(previous);
            return modelSha;
        } finally {
            zipFile.delete();
            deleteRecursive(staging);
            try { input.close(); } catch (Exception ignored) {}
        }
    }
    private static String hex(byte[] bytes) {
        StringBuilder b=new StringBuilder();
        for(byte v:bytes) b.append(String.format(java.util.Locale.ROOT,"%02x",v & 255));
        return b.toString();
    }
    private static void deleteRecursive(File f) {
        if(f == null || !f.exists()) return;
        if(f.isDirectory()) {
            File[] children=f.listFiles();
            if(children!=null) for(File child:children) deleteRecursive(child);
        }
        f.delete();
    }
}
