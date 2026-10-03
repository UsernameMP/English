package com.usernamemp.englishsprint;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.PackageInstaller;
import android.app.PendingIntent;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.Settings;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

public final class UpdateManager {
    public static final class UpdateInfo {
        public final String version;
        public final String downloadUrl;
        public final long sizeBytes;

        UpdateInfo(String version, String downloadUrl, long sizeBytes) {
            this.version = version;
            this.downloadUrl = downloadUrl;
            this.sizeBytes = sizeBytes;
        }

        public String sizeLabel() {
            if (sizeBytes <= 0) return "? MB";
            return String.format(Locale.US, "%.1f MB", sizeBytes / 1024.0 / 1024.0);
        }
    }

    public interface Callback {
        void onResult(UpdateInfo info, String error);
    }

    private static final String RELEASE_API =
            "https://api.github.com/repos/UsernameMP/English/releases/latest";

    private final Activity activity;

    public UpdateManager(Activity activity) {
        this.activity = activity;
    }

    public void check(Callback callback) {
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(RELEASE_API).openConnection();
                connection.setConnectTimeout(8000);
                connection.setReadTimeout(8000);
                connection.setRequestProperty("Accept", "application/vnd.github+json");
                connection.setRequestProperty("User-Agent", "English-Sprint-Pilot-Updater");
                int code = connection.getResponseCode();
                if (code != 200) throw new IllegalStateException("GitHub HTTP " + code);

                String json;
                try (InputStream in = new BufferedInputStream(connection.getInputStream())) {
                    json = readAll(in);
                }

                JSONObject root = new JSONObject(json);
                String tag = root.optString("tag_name", "");
                String version = normalizeTag(tag);
                JSONArray assets = root.optJSONArray("assets");
                String url = "";
                long size = 0;
                if (assets != null) {
                    for (int i = 0; i < assets.length(); i++) {
                        JSONObject asset = assets.getJSONObject(i);
                        String name = asset.optString("name", "");
                        if (name.endsWith(".apk")) {
                            url = asset.optString("browser_download_url", "");
                            size = asset.optLong("size", 0);
                            break;
                        }
                    }
                }

                UpdateInfo info = null;
                if (!url.isEmpty() && compareVersions(version, BuildConfig.VERSION_NAME) > 0) {
                    info = new UpdateInfo(version, url, size);
                }
                UpdateInfo finalInfo = info;
                activity.runOnUiThread(() -> callback.onResult(finalInfo, null));
            } catch (Exception e) {
                String message = e.getMessage() == null ? e.getClass().getSimpleName() : e.getMessage();
                activity.runOnUiThread(() -> callback.onResult(null, message));
            } finally {
                if (connection != null) connection.disconnect();
            }
        }, "update-check").start();
    }

    public void showCheckDialog() {
        ProgressDialog checking = ProgressDialog.show(
                activity, null, activity.getString(R.string.update_checking), true, false);
        check((info, error) -> {
            checking.dismiss();
            if (error != null) {
                message(activity.getString(R.string.update_failed));
                return;
            }
            if (info == null) {
                message(activity.getString(R.string.update_none));
                return;
            }

            new AlertDialog.Builder(activity)
                    .setTitle(activity.getString(R.string.update_available, info.version, info.sizeLabel()))
                    .setMessage(activity.getString(R.string.update_version_fmt, BuildConfig.VERSION_NAME))
                    .setPositiveButton(activity.getString(R.string.update_download),
                            (d, which) -> downloadAndInstall(info))
                    .setNegativeButton(activity.getString(R.string.dictionary_close), null)
                    .show();
        });
    }

    public void downloadAndInstall(UpdateInfo info) {
        ProgressDialog progress = new ProgressDialog(activity);
        progress.setTitle(activity.getString(R.string.update_downloading));
        progress.setProgressStyle(ProgressDialog.STYLE_HORIZONTAL);
        progress.setIndeterminate(info.sizeBytes <= 0);
        progress.setMax(100);
        progress.setCancelable(false);
        progress.show();

        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                File dir = activity.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
                if (dir == null) dir = activity.getCacheDir();
                if (!dir.exists()) dir.mkdirs();
                File apk = new File(dir, "english-sprint-update.apk");

                connection = (HttpURLConnection) new URL(info.downloadUrl).openConnection();
                connection.setConnectTimeout(10000);
                connection.setReadTimeout(30000);
                connection.setInstanceFollowRedirects(true);
                connection.setRequestProperty("User-Agent", "English-Sprint-Pilot-Updater");
                int code = connection.getResponseCode();
                if (code < 200 || code >= 300) throw new IllegalStateException("Download HTTP " + code);
                long total = connection.getContentLengthLong();

                try (InputStream in = new BufferedInputStream(connection.getInputStream());
                     OutputStream out = new BufferedOutputStream(new FileOutputStream(apk))) {
                    byte[] buffer = new byte[64 * 1024];
                    long copied = 0;
                    int read;
                    int lastProgress = -1;
                    while ((read = in.read(buffer)) != -1) {
                        out.write(buffer, 0, read);
                        copied += read;
                        if (total > 0) {
                            int percent = (int) Math.min(100, copied * 100 / total);
                            if (percent != lastProgress) {
                                lastProgress = percent;
                                int shown = percent;
                                activity.runOnUiThread(() -> progress.setProgress(shown));
                            }
                        }
                    }
                }

                if (!verifyDownloadedApk(apk)) {
                    apk.delete();
                    activity.runOnUiThread(() -> {
                        progress.dismiss();
                        message(activity.getString(R.string.update_bad_apk));
                    });
                    return;
                }

                activity.runOnUiThread(() -> {
                    progress.dismiss();
                    installApk(apk);
                });
            } catch (Exception e) {
                activity.runOnUiThread(() -> {
                    progress.dismiss();
                    message(activity.getString(R.string.update_failed));
                });
            } finally {
                if (connection != null) connection.disconnect();
            }
        }, "update-download").start();
    }

    private boolean verifyDownloadedApk(File apk) {
        try {
            PackageManager pm = activity.getPackageManager();
            int flags = Build.VERSION.SDK_INT >= Build.VERSION_CODES.P
                    ? PackageManager.GET_SIGNING_CERTIFICATES
                    : PackageManager.GET_SIGNATURES;

            PackageInfo archive = pm.getPackageArchiveInfo(apk.getAbsolutePath(), flags);
            PackageInfo current = pm.getPackageInfo(activity.getPackageName(), flags);
            if (archive == null || archive.applicationInfo == null) return false;
            if (!activity.getPackageName().equals(archive.packageName)) return false;
            if (versionCode(archive) <= versionCode(current)) return false;

            Set<String> archiveSigners = signerDigests(archive);
            Set<String> currentSigners = signerDigests(current);
            return !archiveSigners.isEmpty() && archiveSigners.equals(currentSigners);
        } catch (Exception e) {
            return false;
        }
    }

    private void installApk(File apk) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                    && !activity.getPackageManager().canRequestPackageInstalls()) {
                Intent settings = new Intent(
                        Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                        Uri.parse("package:" + activity.getPackageName()));
                activity.startActivity(settings);
                Toast.makeText(activity, R.string.update_enable_installs, Toast.LENGTH_LONG).show();
                return;
            }

            PackageInstaller installer = activity.getPackageManager().getPackageInstaller();
            PackageInstaller.SessionParams params =
                    new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
            params.setAppPackageName(activity.getPackageName());
            int sessionId = installer.createSession(params);

            try (PackageInstaller.Session session = installer.openSession(sessionId);
                 InputStream in = new BufferedInputStream(new java.io.FileInputStream(apk));
                 OutputStream out = session.openWrite("base.apk", 0, apk.length())) {
                byte[] buffer = new byte[64 * 1024];
                int read;
                while ((read = in.read(buffer)) != -1) out.write(buffer, 0, read);
                session.fsync(out);

                Intent callback = new Intent(activity, UpdateInstallReceiver.class)
                        .setAction("com.usernamemp.englishsprint.UPDATE_INSTALL");
                int pendingFlags = PendingIntent.FLAG_UPDATE_CURRENT;
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    pendingFlags |= PendingIntent.FLAG_MUTABLE;
                }
                PendingIntent pendingIntent =
                        PendingIntent.getBroadcast(activity, sessionId, callback, pendingFlags);
                session.commit(pendingIntent.getIntentSender());
            }
        } catch (Exception e) {
            message(activity.getString(R.string.update_failed));
        }
    }

    private static long versionCode(PackageInfo info) {
        return Build.VERSION.SDK_INT >= Build.VERSION_CODES.P
                ? info.getLongVersionCode()
                : info.versionCode;
    }

    private static Set<String> signerDigests(PackageInfo info) throws Exception {
        Signature[] signatures;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P && info.signingInfo != null) {
            signatures = info.signingInfo.hasMultipleSigners()
                    ? info.signingInfo.getApkContentsSigners()
                    : info.signingInfo.getSigningCertificateHistory();
        } else {
            signatures = info.signatures;
        }

        Set<String> result = new HashSet<>();
        if (signatures == null) return result;
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        for (Signature signature : signatures) {
            byte[] hash = digest.digest(signature.toByteArray());
            result.add(hex(hash));
        }
        return result;
    }

    private static String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder();
        for (byte b : bytes) out.append(String.format(Locale.US, "%02x", b & 0xff));
        return out.toString();
    }

    private static String normalizeTag(String tag) {
        String value = tag == null ? "" : tag.trim();
        value = value.replaceFirst("^pilot-v", "");
        value = value.replaceFirst("^v", "");
        return value;
    }

    private static int compareVersions(String a, String b) {
        String[] aa = a.split("[^0-9]+");
        String[] bb = b.split("[^0-9]+");
        int count = Math.max(aa.length, bb.length);
        for (int i = 0; i < count; i++) {
            int av = i < aa.length && !aa[i].isEmpty() ? Integer.parseInt(aa[i]) : 0;
            int bv = i < bb.length && !bb[i].isEmpty() ? Integer.parseInt(bb[i]) : 0;
            if (av != bv) return Integer.compare(av, bv);
        }
        return 0;
    }

    private void message(String text) {
        new AlertDialog.Builder(activity)
                .setMessage(text)
                .setPositiveButton(R.string.got_it, null)
                .show();
    }

    private static String readAll(InputStream in) throws Exception {
        java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int read;
        while ((read = in.read(buffer)) != -1) out.write(buffer, 0, read);
        return out.toString("UTF-8");
    }
}
