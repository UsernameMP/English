#!/usr/bin/env python3
import collections
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG = ROOT / "app/src/main/assets/content/catalog.json"
DICTIONARY = ROOT / "app/src/main/assets/content/dictionary_en.json"

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
dictionary = json.loads(DICTIONARY.read_text(encoding="utf-8"))

print("CONTENT REPORT")
print(f"dictionary entries: {len(dictionary.get('entries', []))}")
for pack_row in catalog.get("packs", []):
    path = ROOT / "app/src/main/assets" / pack_row["asset"]
    bank = json.loads(path.read_text(encoding="utf-8"))
    questions = bank["questions"]
    by_mode = collections.Counter(q["mode"] for q in questions)
    by_status = collections.Counter(q.get("review", {}).get("status", "missing") for q in questions)
    by_interaction = collections.Counter(q.get("interaction") for q in questions)
    by_knowledge = collections.Counter(
        ref["id"] for q in questions for ref in q.get("knowledge", [])
    )
    answer_positions = collections.Counter()
    for q in questions:
        if q.get("interaction") != "single_choice":
            continue
        ids = [o["id"] for o in q.get("options", [])]
        answer_positions[ids.index(q["answer"][0])] += 1
    print(f"pack: {bank['pack']['id']}")
    print(f"questions: {len(questions)}")
    print("interactions:", dict(sorted(by_interaction.items())))
    print("modes:", dict(sorted(by_mode.items())))
    print("review:", dict(sorted(by_status.items())))
    print("answer positions:", dict(sorted(answer_positions.items())))
    print("knowledge units:")
    for key, value in sorted(by_knowledge.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {key}: {value}")
