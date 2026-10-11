#!/usr/bin/env python3
"""Merge small, human-reviewed discovery batches into the canonical source ledger."""
import json
from pathlib import Path
root = Path(__file__).resolve().parent
target = root / "sources.jsonl"
rows = []
seen = set()
paths = [target, *sorted((root / "runs").glob("discovery_*.jsonl")),
         root / "runs" / "new_kg_source.jsonl"]
for path in paths:
    if not path.exists():
        continue
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        url = row.get("url", "").strip()
        if not url or url.rstrip("/") in seen:
            continue
        seen.add(url.rstrip("/"))
        rows.append(row)
target.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
print(f"Source registry: {len(rows)} unique URLs")
