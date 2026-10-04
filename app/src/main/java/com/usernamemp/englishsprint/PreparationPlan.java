package com.usernamemp.englishsprint;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

/** A deterministic, non-punitive daily workload derived from target and evidence gaps. */
public final class PreparationPlan {
    public final int questionsToday;
    public final int daysRemaining;
    public final int dueReviews;
    public final List<String> focusKnowledge;

    private PreparationPlan(int questionsToday, int daysRemaining, int dueReviews, List<String> focusKnowledge) {
        this.questionsToday = questionsToday;
        this.daysRemaining = daysRemaining;
        this.dueReviews = dueReviews;
        this.focusKnowledge = Collections.unmodifiableList(focusKnowledge);
    }

    public static PreparationPlan create(ProgressStore progress, TrainingTargetStore target) {
        Map<String, Double> weights = QuestionBank.blueprintWeights();
        List<Gap> gaps = new ArrayList<>();
        int totalRemaining = 0;
        int due = 0;
        for (String id : QuestionBank.knowledgeIds()) {
            double weight = weights.getOrDefault(id, 0.0);
            int evidenceGoal = Math.max(3, (int) Math.ceil(weight * 40.0));
            int remaining = Math.max(0, evidenceGoal - progress.attemptsKnowledge(id));
            boolean isDue = progress.isDue(id);
            if (isDue) due++;
            totalRemaining += remaining;
            double priority = remaining + weight * 10.0 + (isDue ? 8.0 : 0.0)
                    + Math.max(0.0, 0.75 - progress.masteryKnowledge(id)) * 10.0;
            gaps.add(new Gap(id, priority));
        }
        gaps.sort(Comparator.comparingDouble((Gap gap) -> gap.priority).reversed());
        List<String> focus = new ArrayList<>();
        for (Gap gap : gaps) {
            if (focus.size() >= 3) break;
            focus.add(gap.id);
        }

        int rawDays = target.daysRemaining();
        int days = rawDays < 0 ? 14 : Math.max(1, rawDays);
        int daily = (int) Math.ceil(totalRemaining / (double) days) + Math.min(due, 3);
        daily = Math.max(5, Math.min(20, daily));
        return new PreparationPlan(daily, rawDays, due, focus);
    }

    private static final class Gap {
        final String id;
        final double priority;
        Gap(String id, double priority) { this.id = id; this.priority = priority; }
    }
}
