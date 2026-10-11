#!/usr/bin/env python3
"""Idempotently merge reviewed discovery batches into canonical source registry."""
import json
from pathlib import Path

from crawl_links import normalize

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "sources.jsonl"
RUNS = ROOT / "runs"


def read_rows(path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def merge_sources():
    existing = read_rows(TARGET)
    seen = {normalize(row.get("url", "")) for row in existing}
    merged = list(existing)
    inputs = [*sorted(RUNS.glob("discovery_*.jsonl")), RUNS / "new_kg_source.jsonl"]
    for path in inputs:
        for row in read_rows(path):
            url = normalize(row.get("url", ""))
            if not url or url in seen:
                continue
            # Keep source provenance and all author classifications as supplied.
            candidate = dict(row)
            candidate["url"] = url
            candidate.setdefault("origin", path.as_posix())
            candidate.setdefault("status", "unverified")
            merged.append(candidate)
            seen.add(url)
    if merged != existing:
        TARGET.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in merged),
            encoding="utf-8",
        )
    return len(merged), len(merged) - len(existing)


if __name__ == "__main__":
    count, added = merge_sources()
    print(f"Source registry: {count} unique URLs (+{added})")
