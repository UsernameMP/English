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

    numeric_out = pathlib.Path(tmp) / "generated_numeric.json"
    subprocess.run([
        sys.executable, str(GENERATOR),
        "--subject", "informatics",
        "--grade", "6",
        "--competition", "Olympiad pilot",
        "--season", "2026-2027",
        "--knowledge", "CS.ALGORITHMS.TRACING",
        "--interaction", "numeric",
        "--seed", "ci-numeric",
        "--output", str(numeric_out),
    ], check=True)
    numeric = json.loads(numeric_out.read_text(encoding="utf-8"))
    if numeric.get("interaction") != "numeric" or "options" in numeric:
        fail("numeric generator output must not contain answer options")
    if not numeric.get("answer"):
        fail("numeric generator output needs accepted answers")
    if (numeric.get("answer_policy") or {}).get("tolerance") != 0:
        fail("numeric drafts must declare an exact default tolerance")

    multi_out = pathlib.Path(tmp) / "generated_multi.json"
    subprocess.run([
        sys.executable, str(GENERATOR),
        "--subject", "informatics",
        "--grade", "6",
        "--knowledge", "CS.LOGIC.BOOLEAN",
        "--interaction", "multi_choice",
        "--seed", "ci-multi",
        "--output", str(multi_out),
    ], check=True)
    multi = json.loads(multi_out.read_text(encoding="utf-8"))
    option_ids = {option.get("id") for option in multi.get("options", [])}
    if multi.get("interaction") != "multi_choice" or len(multi.get("answer", [])) < 2:
        fail("multi_choice generator output needs multiple answers")
    if any(answer not in option_ids for answer in multi["answer"]):
        fail("multi_choice answers must reference option IDs")

    sequence_out = pathlib.Path(tmp) / "generated_sequence.json"
    subprocess.run([
        sys.executable, str(GENERATOR), "--subject", "informatics", "--grade", "6",
        "--knowledge", "CS.ALGORITHMS.TRACING", "--interaction", "sequence",
        "--seed", "ci-sequence", "--output", str(sequence_out),
    ], check=True)
    sequence = json.loads(sequence_out.read_text(encoding="utf-8"))
    option_ids = [option.get("id") for option in sequence.get("options", [])]
    if sequence.get("interaction") != "sequence" or set(sequence.get("answer", [])) != set(option_ids):
        fail("sequence output must order every option ID exactly once")

print("OK: generator schema/example/CLI")
