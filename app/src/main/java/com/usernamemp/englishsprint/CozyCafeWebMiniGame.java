package com.usernamemp.englishsprint;
public final class CozyCafeWebMiniGame extends WebAssetMiniGame {
    @Override public String id() { return "cozy_cafe"; }
    @Override protected String assetEntry() { return "games/cozy/index.html"; }
    @Override protected boolean needsScaledCanvasTouchBridge() { return true; }
    @Override protected String adaptationScript() { return WebGamePatches.COZY_CAFE; }
}
