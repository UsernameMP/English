package com.usernamemp.englishsprint;
public final class Game2048WebMiniGame extends WebAssetMiniGame {
    @Override public String id() { return "game_2048"; }
    @Override protected String assetEntry() { return "games/2048/index.html"; }
    @Override protected String adaptationScript() { return WebGamePatches.GAME_2048; }
}
