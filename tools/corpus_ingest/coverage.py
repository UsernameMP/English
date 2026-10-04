#!/usr/bin/env python3
"""Measure whether task corpora are structured, Atlas-mapped and runnable."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "app/src/main/assets"
DEFAULT_CATALOG = ASSETS / "content/catalog.json"
DEFAULT_TAXONOMY = ASSETS / "content/interaction_taxonomy.json"


def load_taxonomy(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"]: item["runtime_status"] for item in data["primitives"]}


def tasks_from_file(path: Path) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            tasks = data.get("questions", data.get("tasks", []))
            return [item for item in tasks if isinstance(item, dict)]
    except json.JSONDecodeError:
        pass
    tasks = []
    for line in raw.splitlines():
        if line.strip():
            item = json.loads(line)
            if isinstance(item, dict):
                tasks.append(item)
    return tasks


def catalog_tasks(catalog_path: Path) -> list[dict[str, Any]]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    tasks: list[dict[str, Any]] = []
    for pack in catalog.get("packs", []):
        if not pack.get("enabled", True):
            continue
        bank = json.loads((ASSETS / pack["asset"]).read_text(encoding="utf-8"))
        for task in bank.get("questions", []):
            task = dict(task)
            task.setdefault("pack_id", pack.get("id"))
            tasks.append(task)
    return tasks


def analyze(tasks: Iterable[dict[str, Any]], taxonomy: dict[str, str]) -> dict[str, Any]:
    rows = list(tasks)
    totals = Counter(total=len(rows))
    gaps: Counter[str] = Counter()
    for task in rows:
        structured = all(task.get(field) not in (None, "") for field in ("id", "subject", "interaction", "prompt"))
        atlas_mapped = isinstance(task.get("knowledge"), list) and bool(task["knowledge"]) \
            and isinstance(task.get("prerequisites"), list)
        interaction = task.get("interaction")
        interaction_covered = taxonomy.get(interaction) == "supported"
        runnable = structured and atlas_mapped and interaction_covered
        totals["structured"] += int(structured)
        totals["atlas_mapped"] += int(atlas_mapped)
        totals["interaction_covered"] += int(interaction_covered)
        totals["runnable"] += int(runnable)
        if not structured:
            for field in ("id", "subject", "interaction", "prompt"):
                if task.get(field) in (None, ""):
                    gaps[f"missing:{field}"] += 1
        if not atlas_mapped:
            gaps["missing:atlas_mapping"] += 1
        if not interaction_covered:
            gaps[f"interaction:{interaction or 'missing'}"] += 1
    total = totals["total"]
    ratios = {key: round(totals[key] / total, 6) if total else 0.0
              for key in ("structured", "atlas_mapped", "interaction_covered", "runnable")}
    return {
        "schema_version": "1.0",
        "counts": {key: totals[key] for key in ("total", "structured", "atlas_mapped", "interaction_covered", "runnable")},
        "ratios": ratios,
        "uncovered_clusters": dict(sorted(gaps.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--min-runnable", type=float, default=0.0)
    args = parser.parse_args()
    taxonomy = load_taxonomy(args.taxonomy)
    tasks = tasks_from_file(args.input) if args.input else catalog_tasks(args.catalog)
    report = analyze(tasks, taxonomy)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["ratios"]["runnable"] >= args.min_runnable else 2


if __name__ == "__main__":
    raise SystemExit(main())
