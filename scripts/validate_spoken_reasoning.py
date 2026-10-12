#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter
base=Path("app/src/main/assets/content")
meta=json.loads((base/"spoken_reasoning_candidates.json").read_text())
banks=["math_g5_7_pilot.json","math_g5_new15_2026.json",
       "informatics_g5_7_pilot.json","informatics_g5_new15_2026.json"]
index={}
for bank_file in banks:
    bank=json.loads((base/bank_file).read_text())
    for q in bank["questions"]:
        assert q["id"] not in index
        index[q["id"]]=q
ids=[c["question_id"] for c in meta["candidates"]]
assert len(ids)==len(set(ids)) and len(ids)>=20
assert Counter(c["selection"] for c in meta["candidates"])["verified_arithmetic_pilot"]==1
for c in meta["candidates"]:
    q=index[c["question_id"]]
    assert q["subject"] in ("mathematics","informatics")
    assert q["interaction"]=="numeric" and q["answer"]
    assert q["source"].get("original") is True
    if c["selection"]=="collect_only":
        assert c.get("rubric_version") is None and c.get("reason")
    else:
        assert c["question_id"]=="math_ratio_001"
        assert c["rubric_version"]=="ratio-pilot-v1"
        assert len(c["accepted_paths"])>=2
assert index["math_ratio_001"]["answer"]==["10"]
print("Curated voice candidates:",len(ids))
