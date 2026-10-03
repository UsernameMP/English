package com.usernamemp.englishsprint;

import android.app.Activity;
import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

public final class MiniGameHost {
    private final Context context;
    private final EconomyStore economy;
    private final Map<String, MiniGame> games = new LinkedHashMap<>();
    private final Map<String, MiniGameConfig> configs = new LinkedHashMap<>();

    private boolean enabled = false;
    private int breakIntervalQuestions = 10;
    private String defaultGame = "";

    public MiniGameHost(Context context, EconomyStore economy) {
        this.context = context.getApplicationContext();
        this.economy = economy;
        register(new TapSparkMiniGame());
        loadConfig();
    }

    public boolean shouldOfferBreak(int answeredInSession, boolean hasMoreQuestions) {
        return enabled
                && hasMoreQuestions
                && breakIntervalQuestions > 0
                && answeredInSession > 0
                && answeredInSession % breakIntervalQuestions == 0
                && games.containsKey(defaultGame)
                && configs.containsKey(defaultGame)
                && configs.get(defaultGame).enabled;
    }

    public void startBreak(Activity activity, Runnable onFinished) {
        MiniGame game = games.get(defaultGame);
        MiniGameConfig config = configs.get(defaultGame);
        if (game == null || config == null || !config.enabled) {
            onFinished.run();
            return;
        }
        game.start(activity, config, economy, onFinished);
    }

    public int breakIntervalQuestions() {
        return breakIntervalQuestions;
    }

    public String defaultTitle(Locale locale) {
        MiniGameConfig config = configs.get(defaultGame);
        return config == null ? "" : config.title(locale);
    }

    private void register(MiniGame game) {
        games.put(game.id(), game);
    }

    private void loadConfig() {
        try {
            JSONObject root = new JSONObject(readAsset("game/minigames.json"));
            enabled = root.optBoolean("enabled", false);
            breakIntervalQuestions = Math.max(1, root.optInt("break_interval_questions", 10));
            defaultGame = root.optString("default_game", "");

            JSONArray array = root.optJSONArray("games");
            if (array == null) return;
            for (int i = 0; i < array.length(); i++) {
                JSONObject o = array.getJSONObject(i);
                Map<String, String> titles = new LinkedHashMap<>();
                JSONObject titleObj = o.optJSONObject("title");
                if (titleObj != null) {
                    java.util.Iterator<String> keys = titleObj.keys();
                    while (keys.hasNext()) {
                        String key = keys.next();
                        titles.put(key, titleObj.optString(key, ""));
                    }
                }
                MiniGameConfig config = new MiniGameConfig(
                        o.optString("id", ""),
                        o.optBoolean("enabled", false),
                        Math.max(5, Math.min(60, o.optInt("duration_seconds", 45))),
                        Math.max(0, o.optInt("completion_reward", 0)),
                        Math.max(1, o.optInt("score_bonus_every", 10)),
                        Math.max(0, o.optInt("score_bonus_cap", 0)),
                        titles
                );
                configs.put(config.id, config);
            }
        } catch (Exception e) {
            throw new IllegalStateException("Mini-game config failed to load", e);
        }
    }

    private String readAsset(String path) throws Exception {
        try (InputStream in = context.getAssets().open(path);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) != -1) out.write(buffer, 0, read);
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }
}
