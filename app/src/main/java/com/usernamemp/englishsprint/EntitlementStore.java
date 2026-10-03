package com.usernamemp.englishsprint;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public final class EntitlementStore {
    public static final class Grant {
        public final String id;
        public final String source;
        public final boolean active;
        public final String subject;
        public final int gradeMin;
        public final int gradeMax;
        public final String competition;
        public final String season;
        public final List<String> packIds;
        public final String devicePolicy;

        Grant(JSONObject o) {
            id = o.optString("id", "");
            source = o.optString("source", "");
            active = o.optBoolean("active", false);
            subject = o.optString("subject", "");
            gradeMin = o.optInt("grade_min", 1);
            gradeMax = o.optInt("grade_max", 12);
            competition = o.optString("competition", "");
            season = o.optString("season", "");
            devicePolicy = o.optString("device_policy", "");

            List<String> ids = new ArrayList<>();
            JSONArray packs = o.optJSONArray("pack_ids");
            if (packs != null) {
                for (int i = 0; i < packs.length(); i++) ids.add(packs.optString(i, ""));
            }
            packIds = Collections.unmodifiableList(ids);
        }

        boolean matches(String packId, String packSubject, int packGradeMin, int packGradeMax,
                        String packCompetition, String packSeason) {
            if (!active) return false;
            if (packIds.contains(packId)) return true;
            if (!subject.isEmpty() && !subject.equals(packSubject)) return false;
            if (packGradeMin < gradeMin || packGradeMax > gradeMax) return false;
            if (!competition.isEmpty() && !competition.equals(packCompetition)) return false;
            if (!season.isEmpty() && !season.equals(packSeason)) return false;
            return true;
        }
    }

    private final List<Grant> grants = new ArrayList<>();

    public EntitlementStore(Context context) {
        try {
            JSONObject root = new JSONObject(readAsset(context, "commerce/entitlements.json"));
            JSONArray array = root.getJSONArray("grants");
            for (int i = 0; i < array.length(); i++) grants.add(new Grant(array.getJSONObject(i)));
        } catch (Exception e) {
            throw new IllegalStateException("Entitlement catalog failed to load", e);
        }
    }

    public List<Grant> grants() {
        return Collections.unmodifiableList(grants);
    }

    public boolean canAccessPack(String packId) {
        for (Grant grant : grants) if (grant.active && grant.packIds.contains(packId)) return true;
        return false;
    }

    public boolean canAccessPack(String packId, String subject, int gradeMin, int gradeMax,
                                 String competition, String season) {
        for (Grant grant : grants) {
            if (grant.matches(packId, subject, gradeMin, gradeMax, competition, season)) return true;
        }
        return false;
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
