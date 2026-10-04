package com.usernamemp.englishsprint;

/** Stable, subject-neutral contract advertised by a playable game engine. */
public final class GameModuleDescriptor {
    public static final int HOST_API_VERSION = 1;
    public final String id;
    public final int apiVersion;
    public final boolean skillBased;
    public final boolean hasWinLoss;
    public final boolean supportsPause;

    public GameModuleDescriptor(String id, int apiVersion, boolean skillBased,
                                boolean hasWinLoss, boolean supportsPause) {
        this.id = id;
        this.apiVersion = apiVersion;
        this.skillBased = skillBased;
        this.hasWinLoss = hasWinLoss;
        this.supportsPause = supportsPause;
    }

    public boolean isCompatible() {
        return apiVersion == HOST_API_VERSION && skillBased && hasWinLoss;
    }
}
