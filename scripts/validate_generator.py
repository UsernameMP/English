#!/usr/bin/env python3
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "generator/question_schema.json"
EXAMPLE = ROOT / "generator/example_generated_question.json"
GENERATOR = ROOT / "generator/generate_task.py"

def fail(message):
    print(f"GENERATOR ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)

schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
example = json.loads(EXAMPLE.read_text(encoding="utf-8"))

required = schema.get("required", [])
for field in required:
    if field not in example:
        fail(f"example missing required field: {field}")

if not isinstance(example.get("knowledge"), list) or not example["knowledge"]:
    fail("knowledge must contain assessed Knowledge Unit refs")
if not isinstance(example.get("prerequisites"), list):
    fail("prerequisites must be an array")
if example.get("grade_min", 0) > example.get("grade_max", 0):
    fail("grade_min must be <= grade_max")
if example.get("interaction") == "single_choice":
    option_ids = [o.get("id") for o in example.get("options", [])]
    answers = example.get("answer", [])
    if len(answers) != 1 or answers[0] not in option_ids:
        fail("single_choice answer must reference an option")

with tempfile.TemporaryDirectory() as tmp:
    out = pathlib.Path(tmp) / "generated.json"
    subprocess.run([
        sys.executable, str(GENERATOR),
        "--subject", "english",
        "--grade", "5",
        "--competition", "VSOSh",
        "--season", "2026-2027",
        "--knowledge", "ENG.GRAMMAR.BE",
        "--seed", "ci",
        "--output", str(out),
    ], check=True)
    generated = json.loads(out.read_text(encoding="utf-8"))
    for field in required:
        if field not in generated:
            fail(f"generator output missing: {field}")
    if generated["review"]["status"] != "draft":
        fail("generator must never emit published content directly")

print("OK: generator schema/example/CLI")
