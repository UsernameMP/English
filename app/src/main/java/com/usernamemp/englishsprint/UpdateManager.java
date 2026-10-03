package com.usernamemp.englishsprint;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;
import android.widget.Toast;

import androidx.core.content.FileProvider;

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

    private static final String UPDATE_MANIFEST =
            "https://raw.githubusercontent.com/UsernameMP/English/apk-dist/latest.json";
    private static final String PREFS = "english_sprint_updater";
    private static final String KEY_PENDING_APK = "pending_verified_apk";

    private final Activity activity;
    private final SharedPreferences prefs;

    public UpdateManager(Activity activity) {
        this.activity = activity;
        this.prefs = activity.getSharedPreferences(PREFS, Activity.MODE_PRIVATE);
    }

    public void check(Callback callback) {
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(UPDATE_MANIFEST).openConnection();
                connection.setConnectTimeout(8000);
                connection.setReadTimeout(8000);
                connection.setRequestProperty("Accept", "application/json");
                connection.setRequestProperty("User-Agent", "English-Sprint-Pilot-Updater");
                int code = connection.getResponseCode();
                if (code != 200) throw new IllegalStateException("GitHub HTTP " + code);

                String json;
                try (InputStream in = new BufferedInputStream(connection.getInputStream())) {
                    json = readAll(in);
                }

                JSONObject root = new JSONObject(json);
                String version = root.optString("versionName", "");
                long remoteCode = root.optLong("versionCode", 0);
                String url = root.optString("apkUrl", "");
                long size = root.optLong("sizeBytes", 0);

                long currentCode;
                try {
                    PackageInfo self = activity.getPackageManager()
                            .getPackageInfo(activity.getPackageName(), 0);
                    currentCode = versionCode(self);
                } catch (Exception e) {
                    currentCode = 0;
                }

                UpdateInfo info = null;
                if (!url.isEmpty() && remoteCode > currentCode
                        && compareVersions(version, BuildConfig.VERSION_NAME) >= 0) {
                    info = new UpdateInfo(version, url, size);
                }
                UpdateInfo finalInfo = info;
                activity.runOnUiThread(() -> callback.onResult(finalInfo, null));
            } catch (Exception e) {
                String message = e.getMessage() == null
                        ? e.getClass().getSimpleName()
                        : e.getMessage();
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
                    .setTitle(activity.getString(
                            R.string.update_available, info.version, info.sizeLabel()))
                    .setMessage(activity.getString(
                            R.string.update_version_fmt, BuildConfig.VERSION_NAME))
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
                File dir = new File(activity.getCacheDir(), "updates");
                if (!dir.exists() && !dir.mkdirs()) {
                    throw new IllegalStateException("Cannot create update cache");
                }
                File apk = new File(dir, "english-sprint-update.apk");

                connection = (HttpURLConnection) new URL(info.downloadUrl).openConnection();
                connection.setConnectTimeout(10000);
                connection.setReadTimeout(30000);
                connection.setInstanceFollowRedirects(true);
                connection.setRequestProperty("User-Agent", "English-Sprint-Pilot-Updater");
                int code = connection.getResponseCode();
                if (code < 200 || code >= 300) {
                    throw new IllegalStateException("Download HTTP " + code);
                }
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

                prefs.edit().putString(KEY_PENDING_APK, apk.getAbsolutePath()).apply();
                activity.runOnUiThread(() -> {
                    progress.dismiss();
                    installVerifiedApk(apk);
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

    public void tryInstallPendingUpdate() {
        String path = prefs.getString(KEY_PENDING_APK, "");
        if (path.isEmpty()) return;

        File apk = new File(path);
        if (!apk.isFile() || !verifyDownloadedApk(apk)) {
            clearPending();
            return;
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                && !activity.getPackageManager().canRequestPackageInstalls()) {
            return;
        }

        installVerifiedApk(apk);
    }

    private boolean verifyDownloadedApk(File apk) {
        try {
            PackageManager pm = activity.getPackageManager();
            int flags = Build.VERSION.SDK_INT >= Build.VERSION_CODES.P
                    ? PackageManager.GET_SIGNING_CERTIFICATES
                    : PackageManager.GET_SIGNATURES;

            PackageInfo archive = pm.getPackageArchiveInfo(apk.getAbsolutePath(), flags);
            PackageInfo current = pm.getPackageInfo(activity.getPackageName(), flags);
            if (archive == null) return false;
            if (!activity.getPackageName().equals(archive.packageName)) return false;
            if (versionCode(archive) <= versionCode(current)) return false;

            Set<String> archiveSigners = signerDigests(archive);
            Set<String> currentSigners = signerDigests(current);
            return !archiveSigners.isEmpty() && archiveSigners.equals(currentSigners);
        } catch (Exception e) {
            return false;
        }
    }

    private void installVerifiedApk(File apk) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                    && !activity.getPackageManager().canRequestPackageInstalls()) {
                prefs.edit().putString(KEY_PENDING_APK, apk.getAbsolutePath()).apply();
                Intent settings = new Intent(
                        Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                        Uri.parse("package:" + activity.getPackageName()));
                activity.startActivity(settings);
                Toast.makeText(
                        activity,
                        R.string.update_enable_installs,
                        Toast.LENGTH_LONG
                ).show();
                return;
            }

            Uri uri = FileProvider.getUriForFile(
                    activity,
                    activity.getPackageName() + ".fileprovider",
                    apk
            );

            Intent install = new Intent(Intent.ACTION_VIEW);
            install.setDataAndType(uri, "application/vnd.android.package-archive");
            install.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            install.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);

            clearPending();
            activity.startActivity(install);
        } catch (ActivityNotFoundException e) {
            prefs.edit().putString(KEY_PENDING_APK, apk.getAbsolutePath()).apply();
            message(activity.getString(R.string.update_installer_missing));
        } catch (Exception e) {
            prefs.edit().putString(KEY_PENDING_APK, apk.getAbsolutePath()).apply();
            message(activity.getString(R.string.update_failed));
        }
    }

    private void clearPending() {
        prefs.edit().remove(KEY_PENDING_APK).apply();
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
