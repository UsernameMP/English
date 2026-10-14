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
print("OK: 250 5th-grade informatics problems, 50 per supported mechanic; no microphone.")
