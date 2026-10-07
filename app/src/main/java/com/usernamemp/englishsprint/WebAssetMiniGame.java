package com.usernamemp.englishsprint;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.CountDownTimer;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.webkit.WebViewAssetLoader;

import java.io.ByteArrayInputStream;

public abstract class WebAssetMiniGame implements MiniGame {
    private static final String APP_ASSET_HOST = "appassets.androidplatform.net";
    private static final String APP_ASSET_BASE = "https://" + APP_ASSET_HOST + "/assets/";

    private CountDownTimer timer;
    private WebView webView;
    private Runnable done;
    private EconomyStore economy;
    private MiniGameConfig config;
    private boolean rewardGranted;
    private boolean closed;
    private TextView timeView;
    private TextView rewardView;

    protected abstract String assetEntry();
    protected boolean needsTouchMouseBridge() { return false; }
    protected boolean needsCanvasFit() { return false; }
    protected boolean needsScaledCanvasTouchBridge() { return false; }
    protected boolean needsAimReleaseTouchBridge() { return false; }
    protected String adaptationScript() { return ""; }

    @Override
    public final void start(Activity activity, MiniGameConfig config, EconomyStore economy, Runnable onFinished) {
        stop();
        this.config = config;
        this.economy = economy;
        this.done = onFinished;
        this.rewardGranted = false;
        this.closed = false;

        LinearLayout root = new LinearLayout(activity);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.BLACK);

        LinearLayout header = new LinearLayout(activity);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(activity, 8), dp(activity, 4), dp(activity, 8), dp(activity, 4));
        header.setBackgroundColor(Color.rgb(246, 247, 251));

        Button close = new Button(activity);
        close.setText("✕");
        close.setAllCaps(false);
        close.setTextSize(18);
        close.setOnClickListener(v -> finishSession(false));
        header.addView(close, new LinearLayout.LayoutParams(dp(activity, 48), dp(activity, 44)));

        TextView title = text(activity, config.title(java.util.Locale.getDefault()), 16, Typeface.BOLD);
        header.addView(title, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        timeView = text(activity, config.durationSeconds + "s", 14, Typeface.BOLD);
        header.addView(timeView, new LinearLayout.LayoutParams(dp(activity, 56), ViewGroup.LayoutParams.WRAP_CONTENT));

        rewardView = text(activity, config.completionReward > 0 ? "💎 " + economy.balance() : "", 14, Typeface.BOLD);
        header.addView(rewardView, new LinearLayout.LayoutParams(dp(activity, 76), ViewGroup.LayoutParams.WRAP_CONTENT));
        root.addView(header, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(activity, 52)));

        webView = new WebView(activity);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setLoadWithOverviewMode(false);
        settings.setUseWideViewPort(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setBlockNetworkLoads(false);

        WebViewAssetLoader assetLoader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(activity))
                .build();

        webView.setBackgroundColor(Color.BLACK);
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);
        webView.setVerticalScrollBarEnabled(false);
        webView.setHorizontalScrollBarEnabled(false);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return localOrBlocked(assetLoader, request == null ? null : request.getUrl());
            }

            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, String url) {
                return localOrBlocked(assetLoader, url == null ? null : Uri.parse(url));
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request == null ? null : request.getUrl();
                return !isLocalAssetUri(uri);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                if (!isLocalAssetUri(url == null ? null : Uri.parse(url))) return;
                view.evaluateJavascript(WebGamePatches.COMMON, null);
                String patch = adaptationScript();
                if (patch != null && !patch.isEmpty()) view.evaluateJavascript(patch, null);
                if (needsCanvasFit()) view.evaluateJavascript(CANVAS_FIT, null);
                if (needsScaledCanvasTouchBridge()) {
                    view.evaluateJavascript(SCALED_CANVAS_TOUCH_BRIDGE, null);
                } else if (needsAimReleaseTouchBridge()) {
                    view.evaluateJavascript(AIM_RELEASE_TOUCH_BRIDGE, null);
                } else if (needsTouchMouseBridge()) {
                    view.evaluateJavascript(TOUCH_MOUSE_BRIDGE, null);
                }
            }
        });
        root.addView(webView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        activity.setContentView(root);
        webView.loadUrl(APP_ASSET_BASE + assetEntry());

        timer = new CountDownTimer(config.durationSeconds * 1000L, 1000L) {
            @Override public void onTick(long millisUntilFinished) {
                if (timeView != null) timeView.setText((millisUntilFinished / 1000L + 1L) + "s");
            }

            @Override public void onFinish() {
                timer = null;
                if (timeView != null) timeView.setText("0s");
                finishSession(true);
            }
        };
        timer.start();
    }

    @Override
    public final void stop() {
        cancelTimer();
        destroyWebView();
        closed = true;
        done = null;
        config = null;
        economy = null;
    }

    private void finishSession(boolean completedFullSession) {
        if (closed) return;
        closed = true;
        cancelTimer();

        if (completedFullSession && !rewardGranted && config != null
                && config.completionReward > 0 && economy != null) {
            economy.credit(config.completionReward, "minigame_complete", id());
            rewardGranted = true;
        }

        destroyWebView();
        Runnable callback = done;
        done = null;
        if (callback != null) callback.run();
    }

    private void cancelTimer() {
        if (timer != null) {
            timer.cancel();
            timer = null;
        }
    }

    private void destroyWebView() {
        if (webView == null) return;
        webView.stopLoading();
        webView.loadUrl("about:blank");
        webView.removeAllViews();
        webView.destroy();
        webView = null;
    }

    private static boolean isLocalAssetUri(Uri uri) {
        return uri != null
                && "https".equalsIgnoreCase(uri.getScheme())
                && APP_ASSET_HOST.equalsIgnoreCase(uri.getHost())
                && uri.getPath() != null
                && uri.getPath().startsWith("/assets/");
    }

    private static WebResourceResponse localOrBlocked(WebViewAssetLoader loader, Uri uri) {
        if (uri != null && isLocalAssetUri(uri)) {
            WebResourceResponse local = loader.shouldInterceptRequest(uri);
            if (local != null) return local;
        }
        return new WebResourceResponse(
                "text/plain",
                "UTF-8",
                new ByteArrayInputStream(new byte[0])
        );
    }

    private static TextView text(Activity activity, String value, float sp, int style) {
        TextView v = new TextView(activity);
        v.setText(value);
        v.setTextSize(sp);
        v.setTextColor(Color.rgb(24, 29, 38));
        v.setTypeface(Typeface.DEFAULT, style);
        v.setGravity(Gravity.CENTER);
        return v;
    }

    private static int dp(Activity activity, int value) {
        return Math.round(value * activity.getResources().getDisplayMetrics().density);
    }

    private static final String CANVAS_FIT =
            "(function(){var c=document.querySelector('canvas');if(!c)return;" +
            "document.documentElement.style.margin='0';document.body.style.margin='0';" +
            "function fit(){var sx=window.innerWidth/c.width,sy=window.innerHeight/c.height;" +
            "var s=Math.min(sx,sy);c.style.width=(c.width*s)+'px';c.style.height=(c.height*s)+'px';" +
            "c.style.display='block';c.style.margin='0 auto';}" +
            "fit();window.addEventListener('resize',fit);})();";

    private static final String SCALED_CANVAS_TOUCH_BRIDGE =
            "(function(){if(window.__esScaledTouchBridge)return;window.__esScaledTouchBridge=true;" +
            "var c=document.querySelector('canvas');if(!c)return;" +
            "function send(type,t){var r=c.getBoundingClientRect();var ix=(t.clientX-r.left)*(c.width/r.width);" +
            "var iy=(t.clientY-r.top)*(c.height/r.height);" +
            "c.dispatchEvent(new MouseEvent(type,{bubbles:true,cancelable:true,view:window," +
            "clientX:r.left+ix,clientY:r.top+iy,button:0}));}" +
            "c.addEventListener('touchstart',function(e){if(e.changedTouches.length){send('mousemove',e.changedTouches[0]);e.preventDefault();}},{passive:false});" +
            "c.addEventListener('touchmove',function(e){if(e.changedTouches.length){send('mousemove',e.changedTouches[0]);e.preventDefault();}},{passive:false});" +
            "c.addEventListener('touchend',function(e){if(e.changedTouches.length){var t=e.changedTouches[0];send('mousemove',t);send('click',t);e.preventDefault();}},{passive:false});" +
            "})();";

    private static final String AIM_RELEASE_TOUCH_BRIDGE =
            "(function(){if(window.__esAimReleaseTouchBridge)return;window.__esAimReleaseTouchBridge=true;" +
            "var c=document.querySelector('canvas');if(!c)return;" +
            "function send(type,t){c.dispatchEvent(new MouseEvent(type,{bubbles:true,cancelable:true,view:window," +
            "clientX:t.clientX,clientY:t.clientY,screenX:t.screenX,screenY:t.screenY,button:0}));}" +
            "c.addEventListener('touchstart',function(e){if(e.changedTouches.length){send('mousemove',e.changedTouches[0]);e.preventDefault();}},{passive:false});" +
            "c.addEventListener('touchmove',function(e){if(e.changedTouches.length){send('mousemove',e.changedTouches[0]);e.preventDefault();}},{passive:false});" +
            "c.addEventListener('touchend',function(e){if(e.changedTouches.length){var t=e.changedTouches[0];send('mousemove',t);send('mousedown',t);send('mouseup',t);e.preventDefault();}},{passive:false});" +
            "})();";

    private static final String TOUCH_MOUSE_BRIDGE =
            "(function(){if(window.__esTouchBridge)return;window.__esTouchBridge=true;" +
            "function target(t){return document.elementFromPoint(t.clientX,t.clientY);}" +
            "function send(type,t){var el=target(t);if(!el)return;el.dispatchEvent(new MouseEvent(type,{bubbles:true,cancelable:true,view:window," +
            "clientX:t.clientX,clientY:t.clientY,screenX:t.screenX,screenY:t.screenY,button:0}));}" +
            "document.addEventListener('touchstart',function(e){if(e.changedTouches.length){send('mousedown',e.changedTouches[0]);e.preventDefault();}},{passive:false});" +
            "document.addEventListener('touchmove',function(e){if(e.changedTouches.length){send('mousemove',e.changedTouches[0]);e.preventDefault();}},{passive:false});" +
            "document.addEventListener('touchend',function(e){if(e.changedTouches.length){send('mouseup',e.changedTouches[0]);e.preventDefault();}},{passive:false});" +
            "})();";
}
