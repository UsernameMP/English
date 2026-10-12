package com.usernamemp.englishsprint;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Conservative deterministic pilot. Never infers a student's thoughts from the key. */
public final class SpokenReasoningRubric {
    public static final String VERSION = "ratio-pilot-v1";
    private static final Pattern EXPR = Pattern.compile(
        "(?<!\\d)(\\d+)\\s*([*/])\\s*(\\d+)(?:\\s*([*/])\\s*(\\d+))?\\s*=\\s*(\\d+)(?!\\d)");
    private static final String[][] NUMBERS = {
        {"пятнадцать","15"},{"десять","10"},{"пять","5"},{"три","3"},{"две","2"},
        {"два","2"},{"двух","2"},{"одна","1"},{"один","1"},{"one","1"},
        {"two","2"},{"three","3"},{"five","5"},{"ten","10"},{"fifteen","15"}
    };

    public static final class Result {
        public final String status;
        public final List<String> evidence;
        public final List<String> contradictions;
        public Result(String status, List<String> evidence, List<String> contradictions) {
            this.status = status;
            this.evidence = evidence;
            this.contradictions = contradictions;
        }
    }

    private SpokenReasoningRubric() { }

    public static Result assess(String questionId, boolean answerCorrect, String transcript) {
        List<String> evidence = new ArrayList<>();
        List<String> contradictions = new ArrayList<>();
        if (transcript == null || transcript.trim().isEmpty())
            return new Result(answerCorrect ? "correct_unsubstantiated" : "incomplete",
                    evidence, contradictions);
        if (!"math_ratio_001".equals(questionId))
            return new Result("uncertain_semantics", evidence, contradictions);
        String s = normalized(transcript).trim();
        if (s.matches("(?:10|ответ 10|answer 10|the answer is 10)[.!]?"))
            return new Result(answerCorrect ? "correct_unsubstantiated" : "incomplete",
                    evidence, contradictions);
        boolean share = false, doubleShare = false, direct = false;
        Matcher matcher = EXPR.matcher(s);
        while (matcher.find()) {
            double a = Double.parseDouble(matcher.group(1));
            double b = Double.parseDouble(matcher.group(3));
            String op = matcher.group(2);
            if (b == 0 && "/".equals(op)) { contradictions.add(matcher.group()); continue; }
            double value = "/".equals(op) ? a / b : a * b;
            String op2 = matcher.group(4);
            Double c = matcher.group(5) == null ? null : Double.parseDouble(matcher.group(5));
            if (c != null) {
                if (c == 0 && "/".equals(op2)) { contradictions.add(matcher.group()); continue; }
                value = "/".equals(op2) ? value / c : value * c;
            }
            double claimed = Double.parseDouble(matcher.group(6));
            if (Math.abs(value - claimed) > 1e-7) {
                contradictions.add(matcher.group());
                continue;
            }
            String proof = matcher.group().trim();
            if ((a == 15 && b == 3 && "/".equals(op) && c == null && claimed == 5))
                share = true;
            if (((a == 5 && b == 2) || (a == 2 && b == 5))
                    && "*".equals(op) && c == null && claimed == 10)
                doubleShare = true;
            if (a == 15 && c != null && claimed == 10
                    && (b == 2 && "*".equals(op) && c == 3 && "/".equals(op2)
                        || b == 3 && "/".equals(op) && c == 2 && "*".equals(op2)))
                direct = true;
            evidence.add(proof);
        }
        if (!contradictions.isEmpty())
            return new Result("incorrect_reasoning", evidence, contradictions);
        if ((share && doubleShare) || direct)
            return new Result("correct_supported", evidence, contradictions);
        if (!evidence.isEmpty())
            return new Result("incomplete", evidence, contradictions);
        return new Result("uncertain_semantics", evidence, contradictions);
    }

    static String normalized(String text) {
        String s = text.toLowerCase(Locale.ROOT).replace('×','*').replace('÷','/')
                .replace('х','x').replace('＝','=');
        for (String[] n : NUMBERS)
            s = s.replaceAll("(?<![\\p{L}])" + n[0] + "(?![\\p{L}])", n[1]);
        s = s.replaceAll("\\b(?:разделить на|делим на|поделить на|divided by)\\b", "/")
                .replaceAll("(?<![\\p{L}])(?:умножить на|умножаем на|times|multiplied by)(?![\\p{L}])", "*")
                .replaceAll("(?<![\\p{L}])(?:равно|равняется|получается|получим|equals|is equal to)(?![\\p{L}])", "=");
        return s.replaceAll("\\s+"," ");
    }
}
