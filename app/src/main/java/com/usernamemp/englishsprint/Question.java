package com.usernamemp.englishsprint;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public final class Question {
    public enum Type { GRAMMAR, READING, LISTENING, STORY }

    public final String id;
    public final String subject;
    public final int gradeMin;
    public final int gradeMax;
    public final String interaction;
    public final String skill;
    public final List<String> skills;
    public final List<KnowledgeRef> knowledge;
    public final Type type;
    public final int difficulty;
    public final String prompt;
    public final String context;
    public final List<String> options;
    public final int correctIndex;
    public final String explanation;
    public final String explanationFull;
    public final String rule;
    public final String evidence;
    public final String audioAsset;
    public final String speechText;
    public final String sourceCompetition;
    public final String sourceRegion;
    public final String sourceYear;
    public final boolean verified;

    public Question(
            String id,
            String subject,
            int gradeMin,
            int gradeMax,
            String interaction,
            List<String> skills,
            List<KnowledgeRef> knowledge,
            Type type,
            int difficulty,
            String prompt,
            String context,
            List<String> options,
            int correctIndex,
            String explanation,
            String explanationFull,
            String rule,
            String evidence,
            String audioAsset,
            String speechText,
            String sourceCompetition,
            String sourceRegion,
            String sourceYear,
            boolean verified
    ) {
        this.id = id;
        this.subject = subject;
        this.gradeMin = gradeMin;
        this.gradeMax = gradeMax;
        this.interaction = interaction;
        this.skills = Collections.unmodifiableList(new ArrayList<>(skills));
        this.skill = skills.isEmpty() ? "general" : skills.get(0);
        this.knowledge = Collections.unmodifiableList(new ArrayList<>(knowledge));
        this.type = type;
        this.difficulty = difficulty;
        this.prompt = prompt;
        this.context = context == null ? "" : context;
        this.options = Collections.unmodifiableList(new ArrayList<>(options));
        this.correctIndex = correctIndex;
        this.explanation = explanation == null ? "" : explanation;
        this.explanationFull = explanationFull == null ? "" : explanationFull;
        this.rule = rule == null ? "" : rule;
        this.evidence = evidence == null ? "" : evidence;
        this.audioAsset = audioAsset == null ? "" : audioAsset;
        this.speechText = speechText == null ? "" : speechText;
        this.sourceCompetition = sourceCompetition == null ? "" : sourceCompetition;
        this.sourceRegion = sourceRegion == null ? "" : sourceRegion;
        this.sourceYear = sourceYear == null ? "" : sourceYear;
        this.verified = verified;
    }

    public String primaryKnowledgeId() {
        return knowledge.isEmpty() ? skill : knowledge.get(0).id;
    }

    public boolean isCorrect(int index) {
        return index == correctIndex;
    }
}
