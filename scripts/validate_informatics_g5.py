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
expected={k:50 for k in ("numeric","single_choice","multi_choice","matching","sequence")}
assert len(qs)==250
assert Counter(q["interaction"] for q in qs)==expected
assert len({q["id"] for q in qs})==len(qs)
assert bank["content_version"]=="2.0.0"
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
print("OK: 250 5th-grade informatics problems, 50 per supported mechanic; no microphone.")
