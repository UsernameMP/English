#!/usr/bin/env python3
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BANK = ROOT / "app/src/main/assets/content/english_g5_vso.json"

def fail(msg):
    print(f"CONTENT ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)

with BANK.open(encoding="utf-8") as f:
    bank = json.load(f)

pack = bank.get("pack")
if not isinstance(pack, dict):
    fail("pack metadata is required")
for field in ("id", "subject", "grade_min", "grade_max", "season", "title", "subtitle"):
    if field not in pack:
        fail(f"pack.{field} is required")

units = bank.get("knowledge_units")
if not isinstance(units, list) or not units:
    fail("knowledge_units must be a non-empty array")

unit_ids = set()
for unit in units:
    uid = unit.get("id")
    if not isinstance(uid, str) or not uid:
        fail("knowledge unit id is required")
    if uid in unit_ids:
        fail(f"duplicate knowledge unit: {uid}")
    unit_ids.add(uid)
    if not isinstance(unit.get("labels"), dict) or not unit["labels"]:
        fail(f"{uid}: labels are required")

questions = bank.get("questions")
if not isinstance(questions, list) or not questions:
    fail("questions must be a non-empty array")

seen = set()
supported = {"single_choice"}
modes = {"grammar", "reading", "listening", "story"}
skills = set()
listening = 0

for i, q in enumerate(questions):
    where = f"question[{i}]"
    qid = q.get("id")
    if not isinstance(qid, str) or not qid.strip():
        fail(f"{where}: missing id")
    if qid in seen:
        fail(f"{qid}: duplicate id")
    seen.add(qid)

    if q.get("interaction") not in supported:
        fail(f"{qid}: runtime currently supports {sorted(supported)}, got {q.get('interaction')!r}")
    if q.get("mode") not in modes:
        fail(f"{qid}: invalid mode")

    qskills = q.get("skills")
    if not isinstance(qskills, list) or not qskills:
        fail(f"{qid}: at least one skill is required")
    skills.update(qskills)

    knowledge = q.get("knowledge")
    if not isinstance(knowledge, list) or not knowledge:
        fail(f"{qid}: at least one knowledge reference is required")
    total_weight = 0.0
    for ref in knowledge:
        kid = ref.get("id")
        weight = ref.get("weight")
        if kid not in unit_ids:
            fail(f"{qid}: unknown knowledge unit {kid!r}")
        if not isinstance(weight, (int, float)) or weight <= 0 or weight > 1:
            fail(f"{qid}: invalid knowledge weight for {kid}")
        total_weight += float(weight)
    if total_weight > 1.000001:
        fail(f"{qid}: knowledge weights exceed 1.0")

    prompt = q.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        fail(f"{qid}: prompt is empty")

    options = q.get("options")
    if not isinstance(options, list) or len(options) < 2:
        fail(f"{qid}: at least two options are required")
    option_ids = [o.get("id") for o in options]
    if len(option_ids) != len(set(option_ids)):
        fail(f"{qid}: option ids must be unique")
    if any(not isinstance(o.get("text"), str) or not o["text"].strip() for o in options):
        fail(f"{qid}: option text is empty")

    answers = q.get("answer")
    if not isinstance(answers, list) or len(answers) != 1:
        fail(f"{qid}: single_choice needs exactly one answer")
    if answers[0] not in option_ids:
        fail(f"{qid}: answer {answers[0]!r} is not an option id")

    fb = q.get("feedback") or {}
    for field in ("short", "full", "rule"):
        if not isinstance(fb.get(field), str) or not fb[field].strip():
            fail(f"{qid}: feedback.{field} is required")

    review = q.get("review") or {}
    if review.get("status") != "verified":
        fail(f"{qid}: only verified questions may ship")

    stimulus = q.get("stimulus") or {}
    if q.get("mode") == "reading":
        if not stimulus.get("text"):
            fail(f"{qid}: reading requires stimulus.text")
        ev = q.get("evidence")
        if ev and ev.lower() not in stimulus["text"].lower():
            fail(f"{qid}: evidence is not present in stimulus.text")

    if q.get("mode") == "listening":
        listening += 1
        if not stimulus.get("audio"):
            fail(f"{qid}: listening requires stimulus.audio")
        if not stimulus.get("script"):
            fail(f"{qid}: listening requires stimulus.script")

print(f"OK: pack={pack['id']}, {len(questions)} questions, {len(unit_ids)} knowledge units, {len(skills)} tags, {listening} listening items")
