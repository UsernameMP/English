#!/usr/bin/env python3
"""Independent regression checks for the two original grade-5 15-task APK packs.

No OCR or Dropbox dependencies. Verifies installed pack metadata and known
answer keys against separately calculated reference outcomes.
"""
from __future__ import annotations

from collections import Counter, deque
from itertools import permutations, product
from math import comb
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "app/src/main/assets"
CONTENT = ASSETS / "content"
FILENAMES = {
    "mathematics": "math_g5_new15_2026.json",
    "informatics": "informatics_g5_new15_2026.json",
}
PACK_IDS = {
    "mathematics": "mathematics.olympiad.5.new15.ru.2026",
    "informatics": "informatics.olympiad.5.new15.ru.2026",
}
CYRILLIC = re.compile(r"[А-Яа-яЁё]")


def independent_keys() -> dict[str, list[str]]:
    math = [
        next(str(d) for d in range(10) if (3 + d + 7 + 2) % 9 == 0),
        str(sum(n % 6 == 0 and n % 9 != 0 for n in range(1, 201))),
        str(next(n for n in range(100) if n * 4 == 84 * 3)),
        str(next(2 * x for x in range(71) if x + x + 6 + 2 * x == 70)),
        str(sum(p[0] != "0" and int(p[-1]) % 2 == 0
                for p in permutations("0123"))),
        str(sum(p[1] == "П" and {p[0], p[2]} == {"Д", "М"}
                or p[2] == "П" and {p[1], p[3]} == {"Д", "М"}
                or p[3] == "П" and {p[2], p[4]} == {"Д", "М"}
                for p in permutations("ДМПАБ"))),
        str(next(a*b for a in range(1,24) for b in range(1,24)
                 if (a+b)*2==46 and abs(a-b)==7)),
        str(12**2 - 5**2),
        str(sum(range(1, 12))),
        "opt1",  # eight odd integers sum to even; cannot be 21
        str(sum(n % 10 == 7 and n % 3 == 0 for n in range(1, 101))),
        "opt1",  # odd count of chips invariant under even delta; cannot be 0
        str(sum(comb(5-b, b) for b in range(3))),  # b two-step moves
        str(comb(5,2)),
        str(sum((4-k)*(5-k) for k in range(1,4))),
    ]
    s = 1
    for _ in range(4): s = s*2+1
    codes = {"0": "А", "10": "Б", "11": "В"}
    # Validate codeword concatenation using independently named symbols.
    encoded = "".join(k for k,v in [("0","А"),("11","В"),("0","А"),("10","Б")])
    assert encoded == "011010"
    moves = {"А": ["Б","Г"], "Б": ["А","В"], "В": ["Б","Г"], "Г": ["А","В"]}
    todo = deque([("А",0)]); seen = set()
    route = None
    while todo:
        node,d = todo.popleft()
        if node == "В": route=d;break
        if node in seen:continue
        seen.add(node);todo.extend((n,d+1) for n in moves[node])
    colorings=sum(all(c[i]!=c[(i+1)%4] for i in range(4))
                  for c in product(range(2),repeat=4))
    cs=[
        str(((4*3)-5)*2),
        str(abs(3-1)+abs(2-4)),
        str(s),
        str(sum(i for i in range(1,6) if i%2==0)),
        str(int("1101",2)),
        "opt1", # АВАБ
        str(sum(n>=9 for n in (6,9,6,12))),
        str(len(list(product("01",repeat=2)))),
        str(route),
        str(colorings),
        "opt1", # Vera pear
        str(sum((3,1,2)[i] > (3,1,2)[j] for i in range(3) for j in range(i+1,3))),
        "opt0",
        str(next(n for n in range(1,10) if 2**n >= 8)),
        str(comb(4,2)),
    ]
    return {"mathematics":math, "informatics":cs}


def main() -> None:
    catalog=json.loads((CONTENT/"catalog.json").read_text(encoding="utf-8"))
    grants=json.loads((ASSETS/"commerce/entitlements.json").read_text(encoding="utf-8"))["grants"]
    blueprints=json.loads((CONTENT/"competition_blueprints.json").read_text(encoding="utf-8"))["blueprints"]
    units={x["id"] for x in json.loads((CONTENT/"knowledge_units.json").read_text(encoding="utf-8"))["knowledge_units"]}
    expected=independent_keys()
    all_ids=set()
    for subject,filename in FILENAMES.items():
        raw=(CONTENT/filename).read_bytes()
        data=json.loads(raw)
        pid=PACK_IDS[subject]
        entry=next(x for x in catalog["packs"] if x["id"]==pid)
        assert entry["sha256"]==hashlib.sha256(raw).hexdigest(), f"{subject}: stale APK hash"
        assert entry["asset"]=="content/"+filename
        assert entry["content_version"]==data["content_version"]
        assert entry["enabled"] and data["pack"]["id"]==pid
        assert data["pack"]["grade_min"]==data["pack"]["grade_max"]==5
        assert data["pack"]["subject"]==subject and data["locale"]=="ru"
        assert any(g.get("active") and pid in g.get("pack_ids",[]) for g in grants)
        bp=next(b for b in blueprints if b["pack_id"]==pid)
        assert abs(sum(row["weight"] for row in bp["coverage"])-1)<1e-6
        qs=data["questions"]
        assert len(qs)==15 and len(expected[subject])==15
        seen=set()
        for idx,(q,want) in enumerate(zip(qs,expected[subject]),start=1):
            msg=f"{subject} #{idx} {q['id']}"
            assert q["id"] not in seen and q["id"] not in all_ids,msg+": duplicate ID"
            seen.add(q["id"]);all_ids.add(q["id"])
            assert q["grade_min"]==q["grade_max"]==5 and q["subject"]==subject,msg
            assert CYRILLIC.search(q["prompt"]),msg+": Russian prompt"
            assert q["mode"]=="practice" and q["source"]["original"] is True,msg
            assert q["review"]["status"]=="published" and not q["review"]["human_assessor"],msg
            assert q["reasoning_annotation"]["source"]=="author_reference_solution",msg
            assert q["reasoning_annotation"]["observed_from_learner"] is False,msg
            assert len(q["reasoning_annotation"]["steps"])>=2,msg
            assert all(x["id"] in units for x in q["knowledge"]),msg
            assert len(q["answer"])==1 and q["answer"][0]==want,msg+": unexpected answer "+str(q["answer"])
            for section in ("short","full","rule"):
                assert q["feedback"][section]["en"]==q["feedback"][section]["ru"],msg
                assert CYRILLIC.search(q["feedback"][section]["ru"]),msg
            if q["interaction"]=="numeric":
                assert re.fullmatch(r"\d+",q["answer"][0]),msg
                assert q["answer_policy"]["tolerance"]==0,msg
            else:
                opts=q["options"]
                assert q["interaction"]=="single_choice" and len(opts)>=2,msg
                assert want in {x["id"] for x in opts},msg
            assert not (set(q["prerequisites"])-units),msg
        assessing={q["knowledge"][0]["id"] for q in qs}
        assert assessing=={r["knowledge_id"] for r in bp["coverage"]}
        print(f"PASS {subject}: {len(qs)} new fifth-grade tasks and independently checked keys")
    print("PASS 30 new APK tasks, pack hashes, access grants, Atlas and Russian explanations")


if __name__=="__main__":
    main()
