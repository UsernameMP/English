#!/usr/bin/env python3
"""Structural and independently computed checks for the Rift grade-5 informatics bank.

These checks do not constitute a human assessor review. They verify content
integrity, client-supported interactions and several algorithmic answer families.
"""
from collections import Counter
import itertools
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "app/src/main/assets/content/informatics_g5_olympiad_extended.json"
bank = json.loads(FILE.read_text(encoding="utf-8"))
qs = bank["questions"]
assert len(qs) == 170, f"expected 170 tasks, got {len(qs)}"
assert bank["locale"] == "ru"
assert bank["pack"]["grade_min"] == bank["pack"]["grade_max"] == 5
assert len({q["id"] for q in qs}) == len(qs)
assert Counter(q["interaction"] for q in qs) == {
    "numeric": 125, "matching": 10, "single_choice": 15,
    "multi_choice": 10, "sequence": 10
}
assert len({q["knowledge"][0]["id"] for q in qs}) == 15


def check(condition, msg):
    if not condition:
        raise AssertionError(msg)


def chromatic(edges, n):
    for k in range(1, 5):
        for colors in itertools.product(range(k), repeat=n):
            if all(colors[a] != colors[b] for a,b in edges):
                return k
    raise AssertionError("more than 4 colors required")


def minimum_swaps(items):
    from collections import deque
    start = tuple(items)
    target = tuple(sorted(items))
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        seq, steps = queue.popleft()
        if seq == target:
            return steps
        for j in range(len(seq)-1):
            candidate = list(seq)
            candidate[j], candidate[j+1] = candidate[j+1], candidate[j]
            candidate = tuple(candidate)
            if candidate not in seen:
                seen.add(candidate)
                queue.append((candidate, steps+1))
    raise AssertionError("cannot sort")


checked = Counter()
for q in qs:
    ident = q["id"]
    check(q["subject"] == "informatics" and q["grade_min"] == q["grade_max"] == 5, f"{ident}: grade/subject")
    check(q["source"]["original"] is True, f"{ident}: source must be original")
    check(q["review"]["human_assessor"] is False, f"{ident}: no invented assessor review")
    check(q["reasoning_annotation"]["observed_from_learner"] is False, f"{ident}: unobserved reasoning")
    check(len(q["reasoning_annotation"]["steps"]) >= 2, f"{ident}: missing solution steps")
    check(bool(re.search(r"[А-Яа-яЁё]", q["prompt"])), f"{ident}: non-Russian prompt")
    for field in ("short", "full", "rule"):
        fb = q["feedback"][field]
        check(bool(fb["ru"]) and fb["ru"] == fb["en"], f"{ident}: untranslated feedback {field}")
    ans = q["answer"]
    check(ans and len(ans) == len(set(ans)), f"{ident}: missing/duplicated answer")
    interaction = q["interaction"]
    if interaction == "numeric":
        check(len(ans) == 1 and re.fullmatch(r"-?\d+", ans[0]) is not None, f"{ident}: invalid numeric")
    elif interaction == "matching":
        left, right = q["matching_left"], q["matching_right"]
        lookup_left = {r["id"] for r in left}
        lookup_right = {r["id"] for r in right}
        left_seen, right_seen = set(), set()
        for pair in ans:
            x,y = pair.split(":")
            check(x in lookup_left and y in lookup_right, f"{ident}: invalid matching pair")
            left_seen.add(x)
            right_seen.add(y)
        check(left_seen == lookup_left and len(right_seen) == len(right), f"{ident}: not bijective")
    else:
        option_ids = [x["id"] for x in q["options"]]
        check(set(ans) <= set(option_ids), f"{ident}: option mismatch")
        if interaction == "sequence":
            check(len(ans) == len(option_ids), f"{ident}: sequence missing item")
        if interaction == "multi_choice":
            check(len(ans) >= 2, f"{ident}: must select two or more")
    family = q["skills"][0]
    stimulus = q["stimulus"].get("text", "")
    expected = int(ans[0]) if interaction == "numeric" else None

    if family == "coloring":
        edges_raw = stimulus.split("Пары соседей: ",1)[1].split(". Соседи",1)[0]
        vertices = "АБВГДЕЖЗ"
        edges = [(vertices.index(a),vertices.index(b)) for a,b in
                 (e.split("—") for e in edges_raw.split(", "))]
        check(expected == chromatic(edges, max(max(e) for e in edges)+1), f"{ident}: wrong chromatic number")
        checked[family] += 1

    elif family == "sorting" and interaction == "numeric":
        seq = [int(x) for x in stimulus.split("Номера слева направо: ",1)[1].split(".",1)[0].split(", ")]
        check(expected == minimum_swaps(seq), f"{ident}: wrong adjacent-swap answer")
        checked[family] += 1

    elif family == "digits":
        m = re.search(r"набора ([\d, ]+)\. Сумма трёх цифр (\d+)", stimulus)
        check(m is not None, f"{ident}: format")
        digits = [int(z) for z in m.group(1).split(", ")]
        target = int(m.group(2))
        actual = sum(a != b and b != c and a+b+c == target
                     for a,b,c in itertools.product(digits, repeat=3) if a != 0)
        check(expected == actual, f"{ident}: digit count wrong")
        checked[family] += 1

    elif family == "coding":
        count = int(re.search(r"для кодирования (\d+)",q["prompt"]).group(1))
        length = 0
        while 2**length < count: length += 1
        check(expected == length, f"{ident}: code bits wrong")
        checked[family] += 1

    elif family == "routes":
        raw = stimulus.split("переходы: ",1)[1].rstrip(".")
        verts = "АБВГДЕ"
        edges = [(verts.index(a),verts.index(b)) for a,b in
                 (e.split("→") for e in raw.split(", "))]
        paths = [[] for _ in range(6)]
        paths[0] = [("А",)]
        for v in range(6):
            for a,b in edges:
                if a == v:
                    paths[b].extend(path+(verts[b],) for path in paths[a])
        lengths = [len(path)-1 for path in paths[5]]
        actual = len(lengths) if "Сколько маршрутов" in q["prompt"] else min(lengths)
        check(expected == actual, f"{ident}: route answer wrong {expected} != {actual}")
        checked[family] += 1

    elif family == "invariants":
        m = re.search(r"Старт: (\d+)\. Каждая команда либо прибавляет (\d+)",stimulus)
        start, step = map(int,m.groups())
        selections = [int(x["text"]) for x in q["options"]]
        bad = [i for i,v in enumerate(selections) if (v-start)%step != 0]
        chosen = next(i for i,opt in enumerate(q["options"]) if opt["id"] == ans[0])
        check(bad == [chosen], f"{ident}: invariance has invalid distractors")
        checked[family] += 1

    elif family == "binary":
        if interaction == "numeric":
            binary = stimulus.split("запись ",1)[1].split("₂",1)[0]
            check(expected == int(binary,2), f"{ident}: binary conversion")
        else:
            decimal = int(re.search(r"числу (\d+)",q["prompt"]).group(1))
            chosen = next(x["text"] for x in q["options"] if x["id"] == ans[0])
            check(chosen == format(decimal,"b"), f"{ident}: inverse binary")
        checked[family] += 1

    elif family == "order":
        expected_names = ["Б", "Г", "А", "В"]
        selected = [next(x["text"][0] for x in q["options"] if x["id"] == key) for key in ans]
        check(selected == expected_names, f"{ident}: invalid sorting sequence")
        checked[family] += 1

    elif family == "multi":
        m = re.search(r"делятся на (\d+) и больше (\d+)",q["prompt"])
        divisor, threshold = map(int,m.groups())
        actual = {x["id"] for x in q["options"]
                  if int(x["text"])%divisor==0 and int(x["text"])>threshold}
        check(actual == set(ans), f"{ident}: multi-choice false answer")
        checked[family] += 1

print(f"OK: grade-5 informatics: {len(qs)} tasks, 15 topics, 5 interactions; "
      f"{sum(checked.values())} independently recalculated answers")
