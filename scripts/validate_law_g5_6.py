#!/usr/bin/env python3
"""Check 30 original grade-5/6 law tasks against independent authored answer key."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "app/src/main/assets/content/law_g5_6_vsosh.json"
bank = json.loads(ASSET.read_text(encoding="utf-8"))
qs = bank["questions"]
EXPECTED = [["b"],["a","c","d"],["l0:r1","l1:r3","l2:r2","l3:r0"],["конституция","конституция рф","конституция российской федерации"],["14"],["10"],["c"],["a","c","d"],["l0:r2","l1:r3","l2:r0","l3:r1"],["d","b","a","c"],["a"],["a","c"],["l0:r2","l1:r3","l2:r1","l3:r0"],["дарение"],["c","a","d","b"],["b"],["b","d"],["l0:r2","l1:r3","l2:r1","l3:r0"],["штраф"],["b","d","a","c"],["c"],["a","b","d"],["l0:r1","l1:r3","l2:r0","l3:r2"],["нотариус"],["c","a","d","b"],["d"],["a","c","d"],["l0:r1","l1:r3","l2:r2","l3:r0"],["18"],["гражданство"]]
COUNTS = {"single_choice": 6, "multi_choice": 6, "matching": 6,
          "free_response": 5, "sequence": 4, "numeric": 3}
TOPICS = {"constitution", "family", "civil", "responsibility", "professions", "terms"}

assert bank["pack"]["subject"] == "law"
assert (bank["pack"]["grade_min"], bank["pack"]["grade_max"]) == (5, 6)
assert len(qs) == 30 and len({q["id"] for q in qs}) == 30
assert Counter(q["interaction"] for q in qs) == COUNTS
assert Counter(q["topic"] for q in qs) == {t: 5 for t in TOPICS}
assert bank["editorial"]["official_task_copy"] is False
assert all(q["interaction"] != "spoken_reasoning" for q in qs)
catalog = json.loads((ROOT/"app/src/main/assets/content/catalog.json").read_text(encoding="utf-8"))
row = next(x for x in catalog["packs"] if x["id"] == bank["pack"]["id"])
assert row["sha256"] == hashlib.sha256(ASSET.read_bytes()).hexdigest()
assert row["content_version"] == bank["content_version"]
knowledge = json.loads((ROOT/"app/src/main/assets/content/knowledge_units.json").read_text(encoding="utf-8"))
known = {unit["id"] for unit in knowledge["knowledge_units"]}

for i, (question, expected) in enumerate(zip(qs, EXPECTED), 1):
    qid = f"law56_{i:03}"
    assert question["id"] == qid, qid
    interaction = question["interaction"]
    answers = question["answer"]
    assert question["source"]["original"] is True, qid
    assert question["review"]["status"] == "published", qid
    assert question["review"]["human_assessor"] is False, qid
    assert question["reasoning_annotation"]["observed_from_learner"] is False, qid
    assert question["knowledge"] and all(x["id"] in known for x in question["knowledge"]), qid
    assert question["feedback"]["full"]["ru"] and question["feedback"]["rule"]["ru"], qid
    assert question["prompt"].strip(), qid
    if interaction in ("single_choice", "multi_choice", "sequence"):
        opts = question["options"]
        option_ids = [x["id"] for x in opts]
        assert len(option_ids) == len(set(option_ids)) >= 4, qid
        assert set(answers) <= set(option_ids), qid
        if interaction == "single_choice":
            assert len(answers) == 1, qid
        elif interaction == "multi_choice":
            assert len(answers) >= 2 and len(answers) < len(opts), qid
        else:
            assert len(answers) == len(opts) and set(answers) == set(option_ids), qid
    elif interaction == "matching":
        left, right = question["matching_left"], question["matching_right"]
        assert len(left) == len(right) == len(answers) == 4, qid
        linked = [x.split(":") for x in answers]
        assert {a for a, b in linked} == {x["id"] for x in left}, qid
        assert {b for a, b in linked} == {x["id"] for x in right}, qid
    elif interaction == "numeric":
        assert len(answers) == 1 and answers[0].isdigit(), qid
    elif interaction == "free_response":
        assert all(x.strip() for x in answers), qid
    else:
        raise AssertionError((qid, interaction))
    assert answers == expected, (qid, "incorrect reference key", answers, expected)

print("Law 5-6: 30 independently fixed answer keys, six topics and all interactions validated")
