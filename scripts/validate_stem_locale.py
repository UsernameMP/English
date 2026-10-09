#!/usr/bin/env python3
"""Ensure Russian STEM pilots cannot ship with English question text.

The English-language subject is intentionally excluded from this check.
"""
import json
import pathlib
import re

CONTENT = pathlib.Path(__file__).resolve().parents[1] / "app/src/main/assets/content"
PACKS = ("math_g5_7_pilot.json", "informatics_g5_7_pilot.json")
CYRILLIC = re.compile(r"[А-Яа-яЁё]")
ENGLISH_WORD = re.compile(r"[A-Za-z]{3,}")


def verify_text(value, label, require_cyrillic=False):
    if not isinstance(value, str) or not value.strip():
        raise AssertionError(f"{label}: missing text")
    if require_cyrillic and not CYRILLIC.search(value):
        raise AssertionError(f"{label}: text is not Russian: {value!r}")
    if ENGLISH_WORD.search(value):
        raise AssertionError(f"{label}: English text remains: {value!r}")


def main():
    total = 0
    for filename in PACKS:
        pack = json.loads((CONTENT / filename).read_text(encoding="utf-8"))
        if pack.get("locale") != "ru":
            raise AssertionError(f"{filename}: locale must be ru")
        for field in ("title", "subtitle"):
            labels = pack["pack"][field]
            verify_text(labels["ru"], f"{filename}: pack.{field}", True)
            if labels.get("en") != labels["ru"]:
                raise AssertionError(f"{filename}: pack.{field} must remain Russian in all device locales")

        if len(pack["questions"]) != 12:
            raise AssertionError(f"{filename}: unexpected number of questions")

        for q in pack["questions"]:
            qid = q["id"]
            verify_text(q["prompt"], f"{qid}: prompt", True)
            stimulus = q.get("stimulus", {})
            for key in ("text", "script"):
                if stimulus.get(key):
                    verify_text(stimulus[key], f"{qid}: stimulus.{key}")
            for index, option in enumerate(q.get("options", [])):
                verify_text(option["text"], f"{qid}: option {index}")
            for key in ("short", "full", "rule"):
                fb = q["feedback"][key]
                verify_text(fb["ru"], f"{qid}: feedback.{key}", True)
                if fb.get("en") != fb["ru"]:
                    raise AssertionError(f"{qid}: feedback.{key} must remain Russian on English device locale")
            if q.get("interaction") == "numeric" and "unit" in q.get("answer_policy", {}):
                unit = q["answer_policy"]["unit"]
                verify_text(unit, f"{qid}: answer_policy.unit", True)
                for accepted in q["answer"]:
                    if not accepted.endswith(unit):
                        raise AssertionError(f"{qid}: answer uses wrong unit: {accepted}")
            total += 1
    print(f"OK: {total} Russian STEM questions; prompts, options, contexts and feedback localized")


if __name__ == "__main__":
    main()
