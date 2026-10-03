#!/usr/bin/env python3
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BANK = ROOT / "app/src/main/assets/content/english_g5_vso.json"
DICTIONARY = ROOT / "app/src/main/assets/content/dictionary_en.json"

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
seen_prompts = {}
seen_listening_scripts = {}
seen_audio_paths = {}
dialogues = 0
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
    normalized_prompt = " ".join(prompt.lower().split())
    knowledge_key = tuple(ref.get("id") for ref in q.get("knowledge", []))
    duplicate_key = (normalized_prompt, knowledge_key)
    if duplicate_key in seen_prompts:
        fail(f"{qid}: duplicate prompt for same knowledge as {seen_prompts[duplicate_key]}")
    seen_prompts[duplicate_key] = qid

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
        value = fb.get(field)
        if isinstance(value, str):
            valid = bool(value.strip())
        elif isinstance(value, dict):
            valid = any(isinstance(text, str) and text.strip() for text in value.values())
        else:
            valid = False
        if not valid:
            fail(f"{qid}: feedback.{field} is required")

    review = q.get("review") or {}
    if review.get("status") != "published":
        fail(f"{qid}: only published questions may ship")

    if q.get("subject") != pack.get("subject"):
        fail(f"{qid}: subject {q.get('subject')!r} does not match pack subject {pack.get('subject')!r}")
    if q.get("grade_min", 0) < pack.get("grade_min", 0) or q.get("grade_max", 999) > pack.get("grade_max", 999):
        fail(f"{qid}: grade range falls outside pack range")

    stimulus = q.get("stimulus") or {}
    if q.get("mode") == "reading":
        if not stimulus.get("text"):
            fail(f"{qid}: reading requires stimulus.text")
        ev = q.get("evidence")
        if ev and ev.lower() not in stimulus["text"].lower():
            fail(f"{qid}: evidence is not present in stimulus.text")

    if q.get("mode") == "listening":
        listening += 1
        audio_path = stimulus.get("audio")
        script = stimulus.get("script")
        if not audio_path:
            fail(f"{qid}: listening requires stimulus.audio")
        if not script:
            fail(f"{qid}: listening requires stimulus.script")
        if audio_path in seen_audio_paths:
            fail(f"{qid}: audio path reused by {seen_audio_paths[audio_path]}")
        seen_audio_paths[audio_path] = qid

        pace = stimulus.get("pace", "normal")
        if pace not in {"slow", "normal"}:
            fail(f"{qid}: invalid listening pace {pace!r}")

        segments = stimulus.get("segments")
        if segments is not None:
            dialogues += 1
            if not isinstance(segments, list) or len(segments) < 2:
                fail(f"{qid}: dialogue requires at least two segments")
            segment_texts = []
            voices = set()
            for segment in segments:
                if segment.get("voice") not in {"lessac", "ryan"}:
                    fail(f"{qid}: unsupported segment voice {segment.get('voice')!r}")
                if not isinstance(segment.get("text"), str) or not segment["text"].strip():
                    fail(f"{qid}: empty dialogue segment")
                voices.add(segment["voice"])
                segment_texts.append(segment["text"])
            if len(voices) < 2:
                fail(f"{qid}: dialogue must use at least two voices")
            if " ".join(segment_texts).strip() != script.strip():
                fail(f"{qid}: dialogue segments must exactly reconstruct stimulus.script")
        else:
            if stimulus.get("voice") not in {"lessac", "ryan"}:
                fail(f"{qid}: monologue voice must be lessac or ryan")

        normalized_script = " ".join(script.lower().split())
        if normalized_script in seen_listening_scripts:
            fail(f"{qid}: duplicate listening script also used by {seen_listening_scripts[normalized_script]}")
        seen_listening_scripts[normalized_script] = qid

with DICTIONARY.open(encoding="utf-8") as f:
    dictionary = json.load(f)

entries = dictionary.get("entries")
if not isinstance(entries, list) or not entries:
    fail("dictionary entries must be a non-empty array")

lemmas = set()
forms = {}
for entry in entries:
    lemma = entry.get("lemma")
    if not isinstance(lemma, str) or not lemma.strip():
        fail("dictionary entry has no lemma")
    if lemma in lemmas:
        fail(f"dictionary duplicate lemma: {lemma}")
    lemmas.add(lemma)

    translation = entry.get("translation")
    definition = entry.get("definition")
    if not isinstance(translation, dict) or not translation:
        fail(f"dictionary {lemma}: translation map required")
    if not isinstance(definition, dict) or not definition:
        fail(f"dictionary {lemma}: definition map required")
    if not entry.get("example"):
        fail(f"dictionary {lemma}: example required")

    for form in entry.get("forms", []):
        normalized = form.lower().strip()
        if normalized in forms and forms[normalized] != lemma:
            fail(f"dictionary form {form!r} belongs to both {forms[normalized]} and {lemma}")
        forms[normalized] = lemma

print(f"OK: pack={pack['id']}, {len(questions)} questions, {len(unit_ids)} knowledge units, {len(skills)} tags, {listening} listening items ({dialogues} dialogues), {len(entries)} dictionary entries")
