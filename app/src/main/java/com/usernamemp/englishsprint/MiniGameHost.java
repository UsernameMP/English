package com.usernamemp.englishsprint;

import android.app.Activity;
import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;
import android.content.SharedPreferences;

public final class MiniGameHost {
    private final Context context;
    private final EconomyStore economy;
    private final Map<String, MiniGame> games = new LinkedHashMap<>();
    private final Map<String, MiniGameConfig> configs = new LinkedHashMap<>();

    private boolean enabled = false;
    private int breakIntervalQuestions = 10;
    private String defaultGame = "";
    private String selectionStrategy = "round_robin";
    private final SharedPreferences prefs;
    private final Random random = new Random();

    public MiniGameHost(Context context, EconomyStore economy) {
        this.context = context.getApplicationContext();
        this.economy = economy;
        this.prefs = this.context.getSharedPreferences("english_sprint_minigames", Context.MODE_PRIVATE);
        loadConfig();
    }

    public boolean shouldOfferBreak(int answeredInSession, boolean hasMoreQuestions) {
        return enabled
                && hasMoreQuestions
                && breakIntervalQuestions > 0
                && answeredInSession > 0
                && answeredInSession % breakIntervalQuestions == 0
                && !enabledGameIds().isEmpty();
    }

    public void startBreak(Activity activity, Runnable onFinished) {
        String selected = selectNextGameId();
        MiniGame game = games.get(selected);
        MiniGameConfig config = configs.get(selected);
        if (!compatible(game, config)) {
            onFinished.run();
            return;
        }
        prefs.edit().putString("last_game_id", selected).apply();
        game.start(activity, config, economy, onFinished);
    }

    public void startRandomPreview(Activity activity, Runnable onFinished) {
        List<String> ids = enabledGameIds();
        String selected = selectRandomGameId(
                ids,
                prefs.getString("last_preview_game_id", ""),
                random
        );
        MiniGame game = games.get(selected);
        MiniGameConfig config = configs.get(selected);
        if (!compatible(game, config)) {
            onFinished.run();
            return;
        }
        prefs.edit().putString("last_preview_game_id", selected).apply();
        game.start(activity, config, economy, onFinished);
    }

    static String selectRandomGameId(List<String> ids, String last, Random random) {
        if (ids == null || ids.isEmpty()) return "";
        if (ids.size() == 1) return ids.get(0);
        List<String> candidates = new ArrayList<>(ids);
        candidates.remove(last);
        if (candidates.isEmpty()) candidates.addAll(ids);
        return candidates.get(random.nextInt(candidates.size()));
    }

    public int breakIntervalQuestions() {
        return breakIntervalQuestions;
    }

    public String defaultTitle(Locale locale) {
        String selected = selectNextGameId();
        MiniGameConfig config = configs.get(selected);
        return config == null ? "" : config.title(locale);
    }

    private List<String> enabledGameIds() {
        List<String> ids = new ArrayList<>();
        for (Map.Entry<String, MiniGameConfig> entry : configs.entrySet()) {
            MiniGame game = games.get(entry.getKey());
            if (compatible(game, entry.getValue())) ids.add(entry.getKey());
        }
        return ids;
    }

    private String selectNextGameId() {
        List<String> ids = enabledGameIds();
        if (ids.isEmpty()) return defaultGame;
        if (ids.size() == 1) return ids.get(0);

        String last = prefs.getString("last_game_id", "");
        int lastIndex = ids.indexOf(last);

        if ("round_robin".equals(selectionStrategy)) {
            return ids.get((lastIndex + 1 + ids.size()) % ids.size());
        }

        // Fallback strategy: deterministic no-repeat rotation.
        return ids.get((lastIndex + 1 + ids.size()) % ids.size());
    }

    private void register(MiniGame game) {
        games.put(game.id(), game);
    }

    private void registerConfigured(String className) {
        if (className == null || !className.startsWith("com.usernamemp.englishsprint.")) return;
        try {
            Object candidate = Class.forName(className).getDeclaredConstructor().newInstance();
            if (candidate instanceof MiniGame) register((MiniGame) candidate);
        } catch (ReflectiveOperationException ignored) {
            // Catalog mistakes and removed modules fail closed; CI validates bundled entries.
        }
    }

    private boolean compatible(MiniGame game, MiniGameConfig config) {
        if (game == null || config == null || !config.isProduction()) return false;
        GameModuleDescriptor descriptor = game.descriptor();
        return descriptor != null && descriptor.id.equals(config.id)
                && descriptor.apiVersion == config.moduleApiVersion && descriptor.isCompatible();
    }

    private void loadConfig() {
        try {
            JSONObject root = new JSONObject(readAsset("game/minigames.json"));
            enabled = root.optBoolean("enabled", false);
            breakIntervalQuestions = Math.max(1, root.optInt("break_interval_questions", 10));
            defaultGame = root.optString("default_game", "");
            selectionStrategy = root.optString("selection_strategy", "round_robin");

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
                        o.optString("status", "prototype"),
                        o.optInt("module_api_version", 0),
                        Math.max(5, Math.min(60, o.optInt("duration_seconds", 45))),
                        Math.max(0, o.optInt("completion_reward", 0)),
                        Math.max(1, o.optInt("score_bonus_every", 10)),
                        Math.max(0, o.optInt("score_bonus_cap", 0)),
                        titles
                );
                configs.put(config.id, config);
                registerConfigured(o.optString("engine_class", ""));
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
