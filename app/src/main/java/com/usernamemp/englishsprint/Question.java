package com.usernamemp.englishsprint;

import java.util.Arrays;
import java.util.List;

public final class Question {
    public enum Type { GRAMMAR, READING, LISTENING, STORY }

    public final String id;
    public final String skill;
    public final Type type;
    public final String prompt;
    public final String context;
    public final List<String> options;
    public final int correctIndex;
    public final String explanation;
    public final String evidence;
    public final String audioAsset;
    public final String speechText;

    public Question(
            String id,
            String skill,
            Type type,
            String prompt,
            String context,
            int correctIndex,
            String explanation,
            String evidence,
            String audioAsset,
            String speechText,
            String... options
    ) {
        this.id = id;
        this.skill = skill;
        this.type = type;
        this.prompt = prompt;
        this.context = context == null ? "" : context;
        this.options = Arrays.asList(options);
        this.correctIndex = correctIndex;
        this.explanation = explanation == null ? "" : explanation;
        this.evidence = evidence == null ? "" : evidence;
        this.audioAsset = audioAsset == null ? "" : audioAsset;
        this.speechText = speechText == null ? "" : speechText;
    }

    public boolean isCorrect(int index) {
        return index == correctIndex;
    }
}
