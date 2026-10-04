from corpus import candidate_confidence


def test_clean_text_is_accepted():
    score, status, _ = candidate_confidence(
        "1. Найдите все целые числа, удовлетворяющие условию задачи и докажите ответ.",
        False,
        False,
        True,
    )
    assert score >= 0.9
    assert status == "accepted"


def test_graphic_task_is_not_silently_accepted():
    _, status, reason = candidate_confidence("3. Разрежьте фигуру на четыре равные части.", True, True, True)
    assert status in {"needs_llm", "needs_human"}
    assert "embedded_image" in reason


def test_broken_short_formula_goes_to_human():
    score, status, _ = candidate_confidence("7. □□□ = ?", False, False, True)
    assert score < 0.65
    assert status == "needs_human"
