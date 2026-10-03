package com.usernamemp.englishsprint;

import android.app.Activity;

public interface MiniGame {
    String id();
    void start(Activity activity, MiniGameConfig config, EconomyStore economy, Runnable onFinished);
}
