package com.usernamemp.englishsprint;

import android.app.Activity;

public final class DictionaryRepository {
    public interface Callback {
        void onResult(DictionaryEntry entry, boolean fromNetwork, String error);
    }

    private final Activity activity;
    private final DictionaryStore local;
    private final DictionaryProvider remote;

    public DictionaryRepository(Activity activity, DictionaryStore local) {
        this.activity = activity;
        this.local = local;
        this.remote = new RemoteDictionaryProvider();
    }

    public void lookup(String word, Callback callback) {
        DictionaryEntry cached = local.lookup(word);
        if (cached != null) {
            callback.onResult(cached, false, null);
            return;
        }

        remote.lookup(word, (entry, error) -> activity.runOnUiThread(() -> {
            if (entry != null) {
                local.cache(entry);
                callback.onResult(entry, true, null);
            } else {
                callback.onResult(null, false, error == null ? "unavailable" : error);
            }
        }));
    }
}
