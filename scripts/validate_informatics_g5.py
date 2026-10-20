#!/usr/bin/env python3
"""Grade-5 school-stage informatics bank: balanced mechanics and schema regression checks."""
from collections import Counter
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT/"app/src/main/assets/content/informatics_g5_olympiad_extended.json"
bank=json.loads(ASSET.read_text(encoding="utf-8"))
qs=bank["questions"]
expected={k:60 for k in ("numeric","single_choice","multi_choice","matching","sequence")}
assert len(qs)==300
assert Counter(q["interaction"] for q in qs)==expected
assert len({q["id"] for q in qs})==len(qs)
assert bank["content_version"]=="2.2.0"
assert bank["editorial"]["official_task_copy"] is False
assert len(bank["editorial"]["references"])==5
catalog=json.loads((ROOT/"app/src/main/assets/content/catalog.json").read_text(encoding="utf-8"))
pack=next(p for p in catalog["packs"] if p["id"]==bank["pack"]["id"])
assert hashlib.sha256(ASSET.read_bytes()).hexdigest()==pack["sha256"]
for q in qs:
    id=q["id"]; typ=q["interaction"]; answers=q["answer"]
    assert q["subject"]=="informatics" and q["grade_min"]==q["grade_max"]==5,id
    assert q["source"]["original"] is True and q["review"]["status"]=="published",id
    assert q["review"].get("human_assessor") is False,id
    assert q["reasoning_annotation"]["observed_from_learner"] is False,id
    assert q["feedback"]["full"]["ru"] and q["feedback"]["rule"]["ru"],id
    assert answers and len(answers)==len(set(answers)),id
    assert q.get("stimulus",{}).get("text",{}),id
    if typ=="numeric":
        assert len(answers)==1 and answers[0].lstrip("-").isdigit(),id
    elif typ=="matching":
        left=q["matching_left"];right=q["matching_right"]
        pairs=[a.split(":") for a in answers]
        assert len(pairs)==len(left)==len(right)>=3,id
        assert {a for a,b in pairs}=={a["id"] for a in left},id
        assert {b for a,b in pairs}=={b["id"] for b in right},id
    else:
        opts=q["options"]; names=[o["id"] for o in opts]
        assert len(names)>=4 and len(names)==len(set(names)),id
        assert set(answers).issubset(names),id
        if typ=="single_choice": assert len(answers)==1,id
        if typ=="multi_choice": assert 2<=len(answers)<len(opts),id
        if typ=="sequence": assert len(answers)==len(opts),id
assert all(q["interaction"]!="spoken_reasoning" for q in qs)
pilot=json.loads((ROOT/"app/src/main/assets/content/informatics_g5_7_pilot.json").read_text(encoding="utf-8"))
assert all(q["interaction"]!="spoken_reasoning" for q in pilot["questions"])
# Independent answer-key fixtures for all 50 introductory AI tasks.
# The fixture uses displayed option *text*, not JSON answer IDs or source order.
ai_questions = [q for q in qs if q["id"].startswith("ai5_")]
assert len(ai_questions) == 50
assert all(q["id"].startswith("ai5_v2_") for q in ai_questions)
assert Counter(q["interaction"] for q in ai_questions) == {k: 10 for k in expected}
assert all(q["difficulty"] <= 2 for q in ai_questions)
assert all(q["knowledge"][0]["id"] == "CS.AI.OLYMPIAD.5" for q in ai_questions)
ai_fixtures = {
    "labels": (3, ["Кот","Кот и собака","Кот, собака и хомяк","Кот, собака, хомяк и мышь"], [1,2,3,4]),
    "rules": (3, ["Товар А: 2 звезды","Товар Б: 5 звёзд","Товар В: 3 звезды","Товар Г: 4 звезды"], [2,5,3,4]),
    "tables": (3, ["Модель А: 2 верных","Модель Б: 5 верных","Модель В: 3 верных","Модель Г: 4 верных"], [2,5,3,4]),
    "votes": (3, ["ДДН; ННН","ДДН; НДД; ДДД","ННН; ДДН; ДНД; НДН","ДДН; ДНД; ДДД; НДД"], [1,3,2,4]),
    "errors": (2, ["Модель А: 3 ошибки","Модель Б: 1 ошибка","Модель В: 4 ошибки","Модель Г: 2 ошибки"], [3,1,4,2]),
    "accuracy": (80, ["Модель А: 4 из 10","Модель Б: 6 из 10","Модель В: 8 из 10","Модель Г: 9 из 10"], [40,60,80,90]),
    "missing": (4, ["1, 1, 2, ?","2, 2, 3, ?","3, 3, 1, ?","4, 4, 2, ?"], [1,2,3,4]),
    "recommend": (3, ["Книга А: 2 балла","Книга Б: 4 балла","Книга В: 1 балл","Книга Г: 3 балла"], [2,4,1,3]),
    "reminders": (4, ["Понедельник","Понедельник, среда","Понедельник, среда, пятница","Понедельник, среда, пятница, воскресенье"], [1,2,3,4]),
    "budget": (3, ["Проверка А: 3 жетона","Проверка Б: 1 жетон","Проверка В: 4 жетона","Проверка Г: 2 жетона"], [3,1,4,2]),
}
assert Counter(q["ai_archetype"] for q in ai_questions) == {k: 5 for k in ai_fixtures}
import re
for q in ai_questions:
    num, labels, values = ai_fixtures[q["ai_archetype"]]
    score = dict(zip(labels, values))
    typ = q["interaction"]
    if typ == "numeric":
        assert q["answer"] == [str(num)], q["id"]
    elif typ == "matching":
        left = {x["id"]: x["text"] for x in q["matching_left"]}
        right = {x["id"]: int(x["text"]) for x in q["matching_right"]}
        assert set(left.values()) == set(labels), q["id"]
        assert len(q["answer"]) == 4, q["id"]
        for pair in q["answer"]:
            li, ri = pair.split(":")
            assert score[left[li]] == right[ri], q["id"]
    else:
        opts = q["options"]
        assert {x["text"] for x in opts} == set(labels), q["id"]
        actual = {o["id"]: score[o["text"]] for o in opts}
        if typ == "single_choice":
            expected_answer = {max(actual, key=actual.get)}
            assert set(q["answer"]) == expected_answer, q["id"]
        elif typ == "multi_choice":
            threshold = int(re.search(r"не меньше (\\d+)", q["prompt"]).group(1))
            expected_answer = {id for id, value in actual.items() if value >= threshold}
            assert set(q["answer"]) == expected_answer, q["id"]
        elif typ == "sequence":
            expected_answer = sorted(actual, key=actual.get)
            assert q["answer"] == expected_answer, q["id"]
        else:
            raise AssertionError((q["id"], typ))
    assert "факториал" not in (q["prompt"] + q["stimulus"]["text"]).lower()
# The default 15-question training must retain enough accessible classics per type.
hard_classic = {"sorting","subsets","coloring","garden","digits","counting","constraints","invariants"}
easy_classic = [q for q in qs if not q["id"].startswith("ai5_")
                and q["difficulty"] <= 2 and q["skills"][0] not in hard_classic]
assert all(sum(q["interaction"] == typ for q in easy_classic) >= 12 for typ in expected)

# Full generated mechanics verification: independently recompute each new answer.
def value_for(q, item):
    text = item["text"]
    family = q["skills"][0]
    if family == "machines":
        import re
        start = int(re.search(r"число вычислителя (\d+)", q["stimulus"]["text"]).group(1))
        for action in text.split(" → "):
            start = start + int(action[1:]) if action.startswith("+") else start * int(action[1:])
        return start
    if family == "garden":
        import re
        cherries, sweet = map(int, re.search(r"(\d+) вишен, (\d+) черешен", text).groups())
        return sweet + min(cherries, sweet + 1)
    if family == "sorting":
        order = "ХВЧ"
        return sum(order.index(text[i]) > order.index(text[j])
                   for i in range(len(text)) for j in range(i + 1, len(text)))
    if family == "subsets":
        return sum(map(int, text.split("+")))
    if family == "digits":
        return sum(map(int, text))
    if family == "coloring":
        return (1 if "нет общих" in text else 2 if "цепочка" in text
                else 3 if "три попарно" in text else 4)
    if family == "clubs":
        return len(text.split(": ", 1)[1].split(", "))
    if family == "words":
        return len(text)
    raise AssertionError("Unhandled original exercise family: " + family)

checked = 0
for q in qs:
    if not q["id"].startswith("cs5_school_"):
        continue
    options = q.get("options") or q["matching_left"]
    vals = [value_for(q, row) for row in options]
    interaction = q["interaction"]
    if interaction == "single_choice":
        calculated = [options[vals.index(max(vals))]["id"]]
        assert q["answer"] == calculated, q["id"]
    elif interaction == "multi_choice":
        import re
        threshold = int(re.search(r"(?:не меньше|не менее) (\d+)", q["prompt"]).group(1))
        calculated = [options[i]["id"] for i, v in enumerate(vals) if v >= threshold]
        assert set(q["answer"]) == set(calculated), q["id"]
    elif interaction == "matching":
        left = dict(zip([row["id"] for row in options], vals))
        right = {row["id"]: int(row["text"]) for row in q["matching_right"]}
        assert all(left[a] == right[b] for a, b in (pair.split(":") for pair in q["answer"])), q["id"]
    elif interaction == "sequence":
        calculated = [row["id"] for score, row in sorted(zip(vals, options), key=lambda item: item[0])]
        assert q["answer"] == calculated, q["id"]
    checked += 1
assert checked == 155, checked
signatures = {
    (q["stimulus"].get("text"), q["prompt"],
     tuple((r["id"],r["text"]) for r in q.get("options",q.get("matching_left", []))))
    for q in qs
}
assert len(signatures) == len(qs), "Repeated task stem and options"
print("OK: 300 grade-5 informatics tasks, including 50 easy AI tasks with independent text-based answer checks.")
