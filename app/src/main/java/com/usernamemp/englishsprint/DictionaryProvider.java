package com.usernamemp.englishsprint;

public interface DictionaryProvider {
    interface Callback {
        void onResult(DictionaryEntry entry, String error);
    }

    void lookup(String word, Callback callback);
}
