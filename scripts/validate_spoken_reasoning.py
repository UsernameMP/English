#!/usr/bin/env python3
"""Proof of scope: explicit eligible task IDs, arithmetic paths, no observed reasoning impersonation."""
import json
from pathlib import Path
from collections import Counter

base = Path("app/src/main/assets/content")
data = json.loads((base / "spoken_reasoning_candidates.json").read_text(encoding="utf-8"))
assert data["schema_version"] == 1
q = json.loads((base / "math_g5_7_pilot.json").read_text(encoding="utf-8"))
index = {item["id"]: item for item in q["questions"]}
ids = [x["question_id"] for x in data["candidates"]]
assert len(ids) == len(set(ids))
assert "math_ratio_001" in ids and len(ids) >= 3
assert Counter(x["selection"] for x in data["candidates"])["verified_arithmetic_pilot"] == 1
for item in data["candidates"]:
    task = index[item["question_id"]]
    assert task["subject"] == "mathematics"
    assert task["interaction"] == "numeric"
    assert task["source"]["original"] is True
    assert int(task["grade_min"]) <= item["grade_min"]
    assert int(task["grade_max"]) >= item["grade_max"]
    assert task["answer"]
    if item["selection"] == "collect_only":
        assert item.get("rubric_version") is None
    else:
        assert item["rubric_version"] == "ratio-pilot-v1"
        assert len(item["accepted_paths"]) >= 2
assert index["math_ratio_001"]["answer"] == ["10"]
print("Voice reasoning pilot content contract OK")
