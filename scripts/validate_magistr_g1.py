#!/usr/bin/env python3
"""Independent deterministic checks for the two grade-1 Magistr Scheta practice packs.

These are independently authored training exercises, not copied official papers.
"""
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "app/src/main/assets/content"
SOURCES = [
    ("speed", 384, 48, FOLDER / "math_g1_magistr_2026_speed.json"),
    ("olymp", 288, 18, FOLDER / "math_g1_magistr_2026_olymp.json"),
]
seen_ids = set()
seen_prompts = set()
total = 0
all_counts = {}

def expected_answer(q):
    category = q["skills"][0]
    p = q["prompt"]
    v = list(map(int, re.findall(r"\d+", p)))
    if category in {"add10", "add20"}:
        if category == "add20":
            assert v[0] % 10 + v[1] % 10 >= 10
        return v[0] + v[1]
    if category in {"sub10", "sub20"}:
        if category == "sub20":
            assert v[0] % 10 < v[1] % 10
        return v[0] - v[1]
    if category == "missing":
        return v[1] - v[0]
    if category in {"chain", "story_two"}:
        return v[0] + v[1] - v[2]
    if category in {"compare", "story_diff", "story_sub"}:
        return v[0] - v[1]
    if category == "place":
        return v[0] % 10
    if category == "neighbours":
        return v[0] - 1 if "перед" in p else v[0] + 1
    if category == "tens":
        return v[0] // 10 if "десятков" in p else v[0] % 10
    if category == "order":
        return sorted(v)[1]
    if category == "story_add":
        return v[0] + v[1]
    if category == "story_unknown":
        return v[1] - v[0]
    if category == "series":
        assert len(v) == 4
        assert len(set(v[i + 1] - v[i] for i in range(3))) == 1
        return v[3] + v[3] - v[2]
    if category == "interleave":
        assert len(v) == 6
        assert v[2] - v[0] == v[4] - v[2]
        assert v[3] - v[1] == v[5] - v[3]
        return v[4] + v[4] - v[2]
    if category == "units":
        return v[0] * 10 + v[1]
    if category == "broken_line":
        return sum(v)
    if category == "choices":
        return v[0] * v[1]
    if category == "shapes":
        return v[0] * (3 if "треугольник" in p else 4)
    if category == "position":
        assert len(q["options"]) == 3
        match = re.search(r"Дети (\w+), (\w+) и (\w+) стоят", p)
        assert match
        return match.group(2)
    if category == "deduction":
        match = re.search(r"Монета не в (\w+) и не в (\w+) коробке", p)
        assert match
        excluded = set(match.groups())
        return next(o["text"] for o in q["options"] if o["text"] not in excluded)
    raise AssertionError(f"unknown exercise category: {category}")

def decoded_answer(q):
    if q["interaction"] == "numeric":
        assert len(q["answer"]) == 1
        return int(q["answer"][0])
    assert q["interaction"] == "single_choice"
    assert len(q["answer"]) == 1
    options = {o["id"]: o["text"] for o in q["options"]}
    assert len(options) == len(q["options"])
    return options[q["answer"][0]]

for stage, count, per_type, path in SOURCES:
    bank = json.loads(path.read_text(encoding="utf-8"))
    assert bank["pack"]["grade_min"] == bank["pack"]["grade_max"] == 1
    assert bank["editorial"]["official_task_copy"] is False
    assert bank["editorial"]["organizer_affiliation"] is False
    questions = bank["questions"]
    assert len(questions) == count, (stage, len(questions))
    types = collections.Counter(q["skills"][0] for q in questions)
    assert len(types) == (8 if stage == "speed" else 16)
    assert set(types.values()) == {per_type}, types
    for q in questions:
        assert q["grade_min"] == q["grade_max"] == 1
        assert q["source"]["original"] is True
        assert q["review"]["status"] == "published"
        assert q["id"] not in seen_ids
        seen_ids.add(q["id"])
        normalized = " ".join(q["prompt"].lower().split())
        assert normalized not in seen_prompts, q["id"]
        seen_prompts.add(normalized)
        computed = expected_answer(q)
        actual = decoded_answer(q)
        assert str(actual) == str(computed), (q["id"], actual, computed)
        if isinstance(computed, int):
            assert 0 <= computed <= 100, (q["id"], computed)
        assert q["feedback"]["full"]["ru"]
        assert q["reasoning_annotation"]["steps"]
    all_counts[stage] = dict(sorted(types.items()))
    total += len(questions)

assert total == 672
print(f"OK: {total} independent grade-1 tasks, 24 categories; answer keys, prompts, limits and source rights checked")
print(json.dumps(all_counts, ensure_ascii=False, sort_keys=True))
