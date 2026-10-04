package com.usernamemp.englishsprint;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

/** Blueprint-weighted readiness. Confidence is kept separate from estimated mastery. */
public final class ReadinessForecast {
    public final int readinessPercent;
    public final int confidencePercent;
    public final List<String> weakestKnowledge;

    private ReadinessForecast(int readinessPercent, int confidencePercent, List<String> weakestKnowledge) {
        this.readinessPercent = readinessPercent;
        this.confidencePercent = confidencePercent;
        this.weakestKnowledge = Collections.unmodifiableList(weakestKnowledge);
    }

    public static ReadinessForecast create(ProgressStore progress) {
        Map<String, Double> weights = QuestionBank.blueprintWeights();
        List<Row> rows = new ArrayList<>();
        double weightedScore = 0.0;
        double weightedConfidence = 0.0;
        double totalWeight = 0.0;
        for (String id : QuestionBank.knowledgeIds()) {
            double weight = weights.getOrDefault(id, 0.0);
            if (weight <= 0.0) continue;
            double confidence = Math.min(1.0, progress.attemptsKnowledge(id) / 5.0);
            double estimate = progress.masteryKnowledge(id) * confidence + 0.35 * (1.0 - confidence);
            if (progress.isDue(id)) estimate = Math.max(0.0, estimate - 0.05);
            weightedScore += weight * estimate;
            weightedConfidence += weight * confidence;
            totalWeight += weight;
            rows.add(new Row(id, estimate));
        }
        rows.sort(Comparator.comparingDouble(row -> row.score));
        List<String> weakest = new ArrayList<>();
        for (Row row : rows) {
            if (weakest.size() >= 3) break;
            weakest.add(row.id);
        }
        if (totalWeight <= 0.0) return new ReadinessForecast(0, 0, weakest);
        return new ReadinessForecast(
                boundedPercent(weightedScore / totalWeight),
                boundedPercent(weightedConfidence / totalWeight), weakest);
    }

    private static int boundedPercent(double value) {
        return (int) Math.round(Math.max(0.0, Math.min(1.0, value)) * 100.0);
    }

    private static final class Row {
        final String id;
        final double score;
        Row(String id, double score) { this.id = id; this.score = score; }
    }
}
