package com.usernamemp.englishsprint;
public final class BubbleShooterWebMiniGame extends WebAssetMiniGame {
    @Override public String id() { return "bubble_shooter"; }
    @Override protected String assetEntry() { return "games/bubble/bubble-shooter.html"; }
    @Override protected boolean needsCanvasFit() { return true; }
    @Override protected boolean needsAimReleaseTouchBridge() { return true; }
    @Override protected String adaptationScript() { return WebGamePatches.BUBBLE_SHOOTER; }
}
