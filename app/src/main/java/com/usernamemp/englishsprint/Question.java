package com.usernamemp.englishsprint;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class Question {
    public enum Type { PRACTICE, GRAMMAR, READING, LISTENING, STORY }

    public final String id;
    public final String subject;
    public final int gradeMin;
    public final int gradeMax;
    public final String interaction;
    public final String skill;
    public final List<String> skills;
    public final List<KnowledgeRef> knowledge;
    public final List<String> prerequisites;
    public final Type type;
    public final int difficulty;
    public final String prompt;
    public final String context;
    public final List<String> options;
    public final List<String> matchingLeft;
    public final List<String> matchingRight;
    public final List<Integer> matchingAnswer;
    public final int correctIndex;
    public final List<Integer> correctIndices;
    public final List<String> acceptedAnswers;
    public final double numericTolerance;
    public final Double numericMin;
    public final Double numericMax;
    public final String numericUnit;
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
        this.prerequisites = Collections.emptyList();
        this.type = type;
        this.difficulty = difficulty;
        this.prompt = prompt;
        this.context = context == null ? "" : context;
        this.options = Collections.unmodifiableList(new ArrayList<>(options));
        this.matchingLeft = Collections.emptyList();
        this.matchingRight = Collections.emptyList();
        this.matchingAnswer = Collections.emptyList();
        this.correctIndex = correctIndex;
        this.correctIndices = correctIndex < 0
                ? Collections.emptyList() : Collections.singletonList(correctIndex);
        this.acceptedAnswers = Collections.emptyList();
        this.numericTolerance = 0.0;
        this.numericMin = null;
        this.numericMax = null;
        this.numericUnit = "";
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

    public Question(
            String id,
            String subject,
            int gradeMin,
            int gradeMax,
            String interaction,
            List<String> skills,
            List<KnowledgeRef> knowledge,
            List<String> prerequisites,
            Type type,
            int difficulty,
            String prompt,
            String context,
            List<String> options,
            List<String> matchingLeft,
            List<String> matchingRight,
            List<Integer> matchingAnswer,
            int correctIndex,
            List<Integer> correctIndices,
            List<String> acceptedAnswers,
            double numericTolerance,
            Double numericMin,
            Double numericMax,
            String numericUnit,
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
        this.prerequisites = Collections.unmodifiableList(new ArrayList<>(prerequisites));
        this.type = type;
        this.difficulty = difficulty;
        this.prompt = prompt;
        this.context = context == null ? "" : context;
        this.options = Collections.unmodifiableList(new ArrayList<>(options));
        this.matchingLeft = Collections.unmodifiableList(new ArrayList<>(matchingLeft));
        this.matchingRight = Collections.unmodifiableList(new ArrayList<>(matchingRight));
        this.matchingAnswer = Collections.unmodifiableList(new ArrayList<>(matchingAnswer));
        this.correctIndex = correctIndex;
        this.correctIndices = Collections.unmodifiableList(new ArrayList<>(correctIndices));
        this.acceptedAnswers = Collections.unmodifiableList(new ArrayList<>(acceptedAnswers));
        this.numericTolerance = Math.max(0.0, numericTolerance);
        this.numericMin = numericMin;
        this.numericMax = numericMax;
        this.numericUnit = numericUnit == null ? "" : numericUnit.trim();
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

    public boolean acceptsIndices(Set<Integer> indices) {
        return new LinkedHashSet<>(correctIndices).equals(new LinkedHashSet<>(indices));
    }

    public boolean acceptsSequence(List<Integer> indices) {
        return correctIndices.equals(indices);
    }

    public boolean acceptsMatching(List<Integer> rightIndexByLeft) {
        return matchingAnswer.equals(rightIndexByLeft);
    }

    public boolean acceptsText(String raw) {
        if (raw == null) return false;
        if ("numeric".equals(interaction)) {
            Double value = parseNumeric(raw);
            if (value == null) return false;
            if (numericMin != null && value < numericMin) return false;
            if (numericMax != null && value > numericMax) return false;
            if (numericMin != null || numericMax != null) return true;
            for (String accepted : acceptedAnswers) {
                Double expected = parseNumeric(accepted);
                if (expected != null && Math.abs(value - expected) <= numericTolerance + 1e-9) return true;
            }
            return false;
        }
        String normalized = normalizeAnswer(raw);
        if (normalized.isEmpty()) return false;
        for (String accepted : acceptedAnswers) {
            if (normalized.equals(normalizeAnswer(accepted))) return true;
        }
        return false;
    }

    private Double parseNumeric(String raw) {
        String value = raw.trim().replace(',', '.');
        if (!numericUnit.isEmpty()) {
            String suffix = numericUnit.toLowerCase(Locale.ROOT).replaceAll("\\s+", "");
            String compact = value.toLowerCase(Locale.ROOT).replaceAll("\\s+", "");
            if (!compact.endsWith(suffix)) return null;
            value = compact.substring(0, compact.length() - suffix.length());
        }
        Matcher matcher = Pattern.compile("^[-+]?(?:\\d+(?:\\.\\d+)?|\\.\\d+)$").matcher(value.trim());
        if (!matcher.matches()) return null;
        try {
            return Double.parseDouble(value.trim());
        } catch (NumberFormatException ignored) {
            return null;
        }
    }

    private static String normalizeAnswer(String value) {
        String normalized = value.trim().replace(',', '.').replaceAll("\\s+", "");
        if (normalized.matches("[-+]?\\d+(\\.\\d+)?")) {
            try {
                return new java.math.BigDecimal(normalized).stripTrailingZeros().toPlainString();
            } catch (NumberFormatException ignored) {
            }
        }
        return normalized.toLowerCase(java.util.Locale.ROOT);
    }
}
