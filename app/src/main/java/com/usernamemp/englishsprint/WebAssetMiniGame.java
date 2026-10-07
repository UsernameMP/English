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
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public abstract class WebAssetMiniGame implements MiniGame {
    private CountDownTimer timer;
    private WebView webView;
    private Runnable done;
    private EconomyStore economy;
    private MiniGameConfig config;
    private boolean completed;
    private boolean closed;
    private TextView timeView;
    private TextView rewardView;

    protected abstract String assetEntry();
    protected boolean needsTouchMouseBridge() { return false; }

    @Override
    public final void start(Activity activity, MiniGameConfig config, EconomyStore economy, Runnable onFinished) {
        stop();
        this.config = config;
        this.economy = economy;
        this.done = onFinished;
        this.completed = false;
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
        close.setOnClickListener(v -> finishFromUser());
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
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(false);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setBlockNetworkLoads(true);
        webView.setBackgroundColor(Color.BLACK);
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);
        webView.setVerticalScrollBarEnabled(false);
        webView.setHorizontalScrollBarEnabled(false);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                return uri == null || !"file".equalsIgnoreCase(uri.getScheme());
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                if (needsTouchMouseBridge()) {
                    view.evaluateJavascript(TOUCH_MOUSE_BRIDGE, null);
                }
            }
        });
        root.addView(webView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        activity.setContentView(root);
        webView.loadUrl("file:///android_asset/" + assetEntry());

        timer = new CountDownTimer(config.durationSeconds * 1000L, 1000L) {
            @Override public void onTick(long millisUntilFinished) {
                timeView.setText((millisUntilFinished / 1000L + 1L) + "s");
            }

            @Override public void onFinish() {
                completed = true;
                timeView.setText("✓");
                if (config.completionReward > 0) {
                    rewardView.setText("+" + config.completionReward + " 💎");
                }
            }
        };
        timer.start();
    }

    @Override
    public final void stop() {
        if (timer != null) {
            timer.cancel();
            timer = null;
        }
        destroyWebView();
        closed = true;
    }

    private void finishFromUser() {
        if (closed) return;
        closed = true;
        if (timer != null) {
            timer.cancel();
            timer = null;
        }
        if (completed && config != null && config.completionReward > 0 && economy != null) {
            economy.credit(config.completionReward, "minigame_complete", id());
        }
        destroyWebView();
        Runnable callback = done;
        done = null;
        if (callback != null) callback.run();
    }

    private void destroyWebView() {
        if (webView == null) return;
        webView.stopLoading();
        webView.loadUrl("about:blank");
        webView.removeAllViews();
        webView.destroy();
        webView = null;
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

    private static final String TOUCH_MOUSE_BRIDGE =
            "(function(){if(window.__esTouchBridge)return;window.__esTouchBridge=true;" +
            "function send(type,t){var e=new MouseEvent(type,{bubbles:true,cancelable:true,view:window," +
            "clientX:t.clientX,clientY:t.clientY,screenX:t.screenX,screenY:t.screenY,button:0});" +
            "document.elementFromPoint(t.clientX,t.clientY).dispatchEvent(e);}" +
            "document.addEventListener('touchstart',function(e){if(e.changedTouches.length){send('mousedown',e.changedTouches[0]);e.preventDefault();}},{passive:false});" +
            "document.addEventListener('touchmove',function(e){if(e.changedTouches.length){send('mousemove',e.changedTouches[0]);e.preventDefault();}},{passive:false});" +
            "document.addEventListener('touchend',function(e){if(e.changedTouches.length){send('mouseup',e.changedTouches[0]);e.preventDefault();}},{passive:false});" +
            "})();";
}
