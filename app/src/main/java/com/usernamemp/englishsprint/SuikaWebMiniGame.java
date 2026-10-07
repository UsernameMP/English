package com.usernamemp.englishsprint;
public final class SuikaWebMiniGame extends WebAssetMiniGame {
    @Override public String id() { return "suika"; }
    @Override protected String assetEntry() { return "games/suika/index.html"; }
    @Override protected String adaptationScript() { return WebGamePatches.SUIKA; }
}
