#!/usr/bin/env python3
"""Stable unique URL index from raw link occurrences. Original links are never deleted."""
import json
from pathlib import Path
from link_intelligence import canonical_resource_url, resource_id, hint

ROOT = Path(__file__).resolve().parent
RAW_SHARDS = ROOT / "links_shards"
RESOURCE_SHARDS = ROOT / "resources_shards"
OBSERVATIONS = ROOT / "resource_observations.jsonl"
PER_SHARD = 100


def iter_rows(path):
    if not path.exists():
        return
    with path.open(encoding="utf-8") as source:
        for line in source:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                yield obj


def build():
    # Resource and occurrence are distinct: one target may be linked from many
    # source pages. Unique resources have stable IDs; raw occurrences retain all
    # parent URL, anchor text, and provenance evidence.
    mime_by_id = {}
    for row in iter_rows(OBSERVATIONS):
        if row.get("resource_id") and row.get("mime"):
            mime_by_id[row["resource_id"]] = row["mime"]
    unique = {}
    for path in sorted(RAW_SHARDS.glob("batch_*.jsonl")):
        for row in iter_rows(path):
            url = canonical_resource_url(row.get("url", ""))
            rid = resource_id(url)
            if not rid or rid in unique:
                continue
            guess = hint(url, row.get("anchor_text", ""),
                         row.get("title", ""), row.get("heading", ""),
                         mime_by_id.get(rid, ""))
            unique[rid] = {
                "resource_id": rid, "url": url,
                "first_occurrence_id": row.get("id"),
                "first_parent_url": row.get("parent_url"),
                "first_source_url": row.get("source_url"),
                "anchor_text": row.get("anchor_text"),
                "heading": row.get("heading"),
                "type_hint": guess["type_hint"],
                "hint_evidence": guess["hint_evidence"],
                "file_candidate": guess["file_candidate"],
                "mime": mime_by_id.get(rid) or None,
                "review_status": "unreviewed",
            }
    RESOURCE_SHARDS.mkdir(exist_ok=True)
    rows = list(unique.values())
    changed = 0
    required = set()
    for i in range(0, len(rows), PER_SHARD):
        path = RESOURCE_SHARDS / f"resource_{i // PER_SHARD + 1:06d}.jsonl"
        required.add(path)
        content = "".join(json.dumps(r, ensure_ascii=False) + "\n"
                          for r in rows[i:i + PER_SHARD])
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
            changed += 1
    # No removal of historical raw evidence; derived stale shards are removed
    # only when input shrinks (which is not expected in normal operation).
    for path in RESOURCE_SHARDS.glob("resource_*.jsonl"):
        if path not in required:
            path.unlink()
    print(json.dumps({"unique_resource_urls": len(rows),
                      "resource_shards_changed": changed}))


if __name__ == "__main__":
    build()
