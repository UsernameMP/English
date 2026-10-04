package com.usernamemp.englishsprint;

import android.app.Activity;

public interface MiniGame {
    String id();
    default GameModuleDescriptor descriptor() {
        return new GameModuleDescriptor(id(), GameModuleDescriptor.HOST_API_VERSION, true, true, false);
    }
    void start(Activity activity, MiniGameConfig config, EconomyStore economy, Runnable onFinished);
}
