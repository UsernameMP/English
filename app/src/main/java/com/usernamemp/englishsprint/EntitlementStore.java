package com.usernamemp.englishsprint;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;

public final class EntitlementStore {
    private final Set<String> accessiblePacks = new HashSet<>();

    public EntitlementStore(Context context) {
        try {
            JSONObject root = new JSONObject(readAsset(context, "commerce/entitlements.json"));
            JSONArray grants = root.getJSONArray("grants");
            for (int i = 0; i < grants.length(); i++) {
                JSONObject grant = grants.getJSONObject(i);
                if (!grant.optBoolean("active", false)) continue;
                JSONArray packs = grant.optJSONArray("pack_ids");
                if (packs == null) continue;
                for (int j = 0; j < packs.length(); j++) accessiblePacks.add(packs.getString(j));
            }
        } catch (Exception e) {
            throw new IllegalStateException("Entitlement catalog failed to load", e);
        }
    }

    public boolean canAccessPack(String packId) {
        return accessiblePacks.contains(packId);
    }

    private static String readAsset(Context context, String path) throws Exception {
        try (InputStream in = context.getAssets().open(path);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) != -1) out.write(buffer, 0, read);
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }
}
