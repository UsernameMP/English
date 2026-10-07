package com.usernamemp.englishsprint;
public final class Match3WebMiniGame extends WebAssetMiniGame {
    @Override public String id() { return "match3"; }
    @Override protected String assetEntry() { return "games/match3/match3.html"; }
    @Override protected boolean needsTouchMouseBridge() { return true; }
}
