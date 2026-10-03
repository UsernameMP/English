package com.usernamemp.englishsprint;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

public final class RemoteDictionaryProvider implements DictionaryProvider {
    private static final String BASE =
            "https://api.dictionaryapi.dev/api/v2/entries/en/";

    @Override
    public void lookup(String word, Callback callback) {
        String normalized = normalize(word);
        if (normalized.isEmpty()) {
            callback.onResult(null, "empty");
            return;
        }

        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                String encoded = URLEncoder.encode(normalized, StandardCharsets.UTF_8.name());
                connection = (HttpURLConnection) new URL(BASE + encoded).openConnection();
                connection.setConnectTimeout(7000);
                connection.setReadTimeout(7000);
                connection.setRequestProperty("Accept", "application/json");
                connection.setRequestProperty("User-Agent", "English-Sprint-Dictionary/0.6");

                int code = connection.getResponseCode();
                if (code != 200) {
                    callback.onResult(null, "http_" + code);
                    return;
                }

                String json;
                try (InputStream in = new BufferedInputStream(connection.getInputStream());
                     ByteArrayOutputStream out = new ByteArrayOutputStream()) {
                    byte[] buffer = new byte[8192];
                    int read;
                    while ((read = in.read(buffer)) != -1) out.write(buffer, 0, read);
                    json = out.toString(StandardCharsets.UTF_8.name());
                }

                JSONArray root = new JSONArray(json);
                if (root.length() == 0) {
                    callback.onResult(null, "not_found");
                    return;
                }

                JSONObject first = root.getJSONObject(0);
                String lemma = first.optString("word", normalized);
                String phonetic = first.optString("phonetic", "");
                if (phonetic.isEmpty()) {
                    JSONArray phonetics = first.optJSONArray("phonetics");
                    if (phonetics != null) {
                        for (int i = 0; i < phonetics.length(); i++) {
                            String p = phonetics.getJSONObject(i).optString("text", "");
                            if (!p.isEmpty()) { phonetic = p; break; }
                        }
                    }
                }

                String definition = "";
                String example = "";
                JSONArray meanings = first.optJSONArray("meanings");
                if (meanings != null) {
                    outer:
                    for (int i = 0; i < meanings.length(); i++) {
                        JSONArray defs = meanings.getJSONObject(i).optJSONArray("definitions");
                        if (defs == null) continue;
                        for (int j = 0; j < defs.length(); j++) {
                            JSONObject d = defs.getJSONObject(j);
                            String candidate = d.optString("definition", "");
                            if (!candidate.isEmpty()) {
                                definition = candidate;
                                example = d.optString("example", "");
                                break outer;
                            }
                        }
                    }
                }

                if (definition.isEmpty()) {
                    callback.onResult(null, "not_found");
                    return;
                }

                Map<String, String> translations = new LinkedHashMap<>();
                translations.put("en", lemma);
                Map<String, String> definitions = new LinkedHashMap<>();
                definitions.put("en", definition);

                DictionaryEntry entry = new DictionaryEntry(
                        lemma,
                        Collections.singletonList(normalized),
                        phonetic,
                        example,
                        translations,
                        definitions
                );
                callback.onResult(entry, null);
            } catch (Exception e) {
                callback.onResult(null, e.getClass().getSimpleName());
            } finally {
                if (connection != null) connection.disconnect();
            }
        }, "dictionary-lookup").start();
    }

    private static String normalize(String raw) {
        if (raw == null) return "";
        String s = raw.toLowerCase(Locale.US).trim();
        s = s.replaceAll("^[^a-z']+|[^a-z']+$", "");
        if (s.endsWith("'s") && s.length() > 2) s = s.substring(0, s.length() - 2);
        return s;
    }
}
