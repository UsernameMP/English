package com.usernamemp.englishsprint;

import android.content.Context;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;

/**
 * Public GitHub pilot transport only. No token or secret is stored in the APK.
 * Production must replace this with an authenticated backend ContentDeliverySource.
 */
public final class GitHubPilotContentSource implements ContentDeliverySource {
    public static final String MANIFEST_URL =
            "https://raw.githubusercontent.com/UsernameMP/English/content-pilot/manifest.json";

    @Override public Envelope fetch(Context context, Request request) throws Exception {
        JSONObject manifest=new JSONObject(get(MANIFEST_URL));
        JSONObject packs=manifest.getJSONObject("packs");
        JSONObject entry=packs.getJSONObject(request.packId);
        String payload=get(entry.getString("url"));
        String expected=entry.getString("sha256");
        if(!expected.equals(sha256(payload))) throw new SecurityException("Remote content digest mismatch");
        JSONObject bank=new JSONObject(payload);
        org.json.JSONArray q=bank.getJSONArray("questions");
        if(q.length()>request.limit) {
            org.json.JSONArray bounded=new org.json.JSONArray();
            for(int i=0;i<request.limit;i++) bounded.put(q.get(i));
            bank.put("questions",bounded);
            payload=bank.toString();
        }
        return new Envelope(payload,entry.optString("version",""),entry.optString("expires_at",""));
    }

    private static String get(String raw)throws Exception{
        HttpURLConnection c=(HttpURLConnection)new URL(raw).openConnection();
        c.setConnectTimeout(8000); c.setReadTimeout(12000); c.setRequestProperty("Accept","application/json");
        try(InputStream in=c.getInputStream();ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);
            return out.toString(StandardCharsets.UTF_8.name());
        } finally { c.disconnect(); }
    }
    private static String sha256(String raw)throws Exception{
        byte[] d=MessageDigest.getInstance("SHA-256").digest(raw.getBytes(StandardCharsets.UTF_8));
        StringBuilder s=new StringBuilder();for(byte b:d)s.append(String.format(Locale.ROOT,"%02x",b));return s.toString();
    }
}
