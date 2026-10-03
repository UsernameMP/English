#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

def stable_id(subject, grade, competition, knowledge, seed):
    raw = f"{subject}|{grade}|{competition}|{knowledge}|{seed}".encode("utf-8")
    return f"gen_{subject}_{hashlib.sha1(raw).hexdigest()[:12]}"

def main():
    p = argparse.ArgumentParser(description="Create a deterministic draft question template.")
    p.add_argument("--subject", required=True)
    p.add_argument("--grade", type=int, required=True)
    p.add_argument("--competition", default="")
    p.add_argument("--season", default="")
    p.add_argument("--knowledge", required=True, help="Primary assessed Knowledge Unit id")
    p.add_argument("--interaction", choices=["single_choice", "numeric"], default="single_choice")
    p.add_argument("--prerequisite", action="append", default=[])
    p.add_argument("--seed", default="0")
    p.add_argument("--output", required=True)
    args = p.parse_args()

    qid = stable_id(args.subject, args.grade, args.competition, args.knowledge, args.seed)
    question = {
        "id": qid,
        "subject": args.subject,
        "grade_min": args.grade,
        "grade_max": args.grade,
        "competition": args.competition,
        "season": args.season,
        "interaction": args.interaction,
        "mode": "problem",
        "difficulty": 1,
        "prompt": "TODO: write problem statement",
        "stimulus": {},
        "knowledge": [{"id": args.knowledge, "weight": 1.0}],
        "prerequisites": list(dict.fromkeys(args.prerequisite)),
        "answer": ["a"] if args.interaction == "single_choice" else ["0"],
        "feedback": {
            "short": {"en": "TODO", "ru": "TODO"},
            "full": {"en": "TODO", "ru": "TODO"},
            "rule": {"en": "TODO", "ru": "TODO"}
        },
        "source": {
            "competition": args.competition,
            "region": "",
            "year": ""
        },
        "review": {
            "status": "draft",
            "generator": "generator/generate_task.py",
            "seed": str(args.seed)
        }
    }
    if args.interaction == "single_choice":
        question["options"] = [
            {"id": "a", "text": "TODO option A"},
            {"id": "b", "text": "TODO option B"},
            {"id": "c", "text": "TODO option C"}
        ]

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(question, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out)

if __name__ == "__main__":
    main()
