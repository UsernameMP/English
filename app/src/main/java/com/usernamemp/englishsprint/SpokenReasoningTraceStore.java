package com.usernamemp.englishsprint;

import android.content.Context;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

/** Private, no-backup JSON records; never writes or uploads original voice/audio. */
public final class SpokenReasoningTraceStore {
    private final File directory;
    public SpokenReasoningTraceStore(Context context) {
        directory = new File(context.getNoBackupFilesDir(), "reasoning_attempts_v1");
        if (!directory.isDirectory() && !directory.mkdirs())
            throw new IllegalStateException("Reasoning storage unavailable");
    }
    public synchronized String save(JSONObject attempt) throws Exception {
        String id = UUID.randomUUID().toString();
        attempt.put("schema_version", 1);
        attempt.put("trace_id", id);
        attempt.put("recorded_at_ms", System.currentTimeMillis());
        File tmp = new File(directory, id + ".tmp");
        File dst = new File(directory, id + ".json");
        try (FileOutputStream out = new FileOutputStream(tmp)) {
            out.write(attempt.toString().getBytes(StandardCharsets.UTF_8));
            out.getFD().sync();
        }
        if (!tmp.renameTo(dst)) {
            tmp.delete();
            throw new IllegalStateException("Unable to commit reasoning trace");
        }
        return id;
    }
    public synchronized JSONArray exportAll() throws Exception {
        JSONArray rows = new JSONArray();
        File[] files = directory.listFiles((d, name) -> name.endsWith(".json"));
        if (files == null) return rows;
        for (File f : files) {
            try {
                byte[] bytes = new byte[(int) f.length()];
                try (java.io.FileInputStream in = new java.io.FileInputStream(f)) {
                    int off=0;
                    while(off<bytes.length) {
                        int count=in.read(bytes,off,bytes.length-off);
                        if(count<0) throw new java.io.EOFException();
                        off+=count;
                    }
                }
                rows.put(new JSONObject(new String(bytes, StandardCharsets.UTF_8)));
            } catch (Exception ignored) { /* Corrupt records excluded; never send fragments. */ }
        }
        return rows;
    }
    public synchronized int deleteAll() {
        int count = 0;
        File[] files = directory.listFiles((d, n) -> n.endsWith(".json") || n.endsWith(".tmp"));
        if (files != null) for (File f : files) if (f.delete()) count++;
        return count;
    }
}
