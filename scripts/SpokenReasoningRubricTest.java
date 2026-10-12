package com.usernamemp.englishsprint;

public final class SpokenReasoningRubricTest {
    private static void check(String name,String id,boolean answer,String txt,String expected) {
        String got=SpokenReasoningRubric.assess(id,answer,txt).status;
        if (!expected.equals(got))
            throw new AssertionError(name+": expected "+expected+" but got "+got);
    }
    public static void main(String[] args) {
        check("RU steps","math_ratio_001",true,
                "пятнадцать разделить на три равно пять, пять умножить на два равно десять",
                "correct_supported");
        check("EN direct","math_ratio_001",true,
                "fifteen times two divided by three equals ten","correct_supported");
        check("alternative","math_ratio_001",true,
                "15 / 3 * 2 = 10","correct_supported");
        check("bare answer","math_ratio_001",true,"10","correct_unsubstantiated" /* corrected below */);
        check("bad math","math_ratio_001",true,
                "15 / 3 = 4, 5 * 2 = 10","incorrect_reasoning");
        check("partial","math_ratio_001",true,"15 / 3 = 5","incomplete");
        check("unknown words","math_ratio_001",true,"какая-то хитрая формула",
                "uncertain_semantics");
        check("unknown task","math_mix_001",true,"6 + 4 - 1 = 9","uncertain_semantics");
        System.out.println("Conservative reasoning checks OK");
    }
}
