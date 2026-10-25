#!/usr/bin/env python3
"""Apply explicitly SHA-pinned, evidence-backed RIFT label corrections atomically.

This edits metadata only, never downloads linked documents. A mismatched raw ID,
resource ID, URL, old field value or checkpoint SHA aborts without changing labels.
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "link_labels.jsonl"
CORRECTIONS = (
    ("r303_r302_grade_corrections.jsonl", "8c71b29217f77ba43fba68fda2f1ab0a2e458d25", "grade"),
    ("r307_r306_corrections_fixed.jsonl", "61254ca48e8195307d65609906992aad77815041", "type"),
    ("r310_r309_posn_provenance_corrections.jsonl", "76b6b3247555152976cf8f9c526585e860df93fc", "metadata"),
)

def blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def load_jsonl(data, label):
    rows = []
    for i, line in enumerate(data.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{label}:{i}: expected JSON object")
        rows.append(value)
    return rows

def apply():
    original = TARGET.read_bytes()
    rows = load_jsonl(original, str(TARGET))
    by_id = {}
    for row in rows:
        rid = row.get("raw_occurrence_id")
        if not rid or rid in by_id:
            raise ValueError(f"Missing or duplicate canonical raw ID: {rid!r}")
        by_id[rid] = row

    changed = 0
    already = 0
    for filename, expected_sha, kind in CORRECTIONS:
        data = (ROOT / "runs" / filename).read_bytes()
        if blob_sha(data) != expected_sha:
            raise ValueError(f"{filename}: checkpoint SHA mismatch")
        for patch in load_jsonl(data, filename):
            raw_id = patch["raw_occurrence_id"]
            row = by_id.get(raw_id)
            if row is None:
                raise ValueError(f"{filename}: unknown raw occurrence {raw_id}")
            if row.get("resource_id") != patch["resource_id"] or row.get("url") != patch["url"]:
                raise ValueError(f"{filename}: provenance conflict for {raw_id}")
            if kind == "metadata":
                # All four provenance fields must match either the original or the
                # corrected tuple. Partial edits and unrelated canonical rows abort.
                if row.get("type") != patch.get("type"):
                    raise ValueError(f"{filename}: type mismatch for {raw_id}")
                keys = ("country", "competition", "subject", "level")
                old_match = all(row.get(k) == patch["previous_" + k] for k in keys)
                new_match = all(row.get(k) == patch["corrected_" + k] for k in keys)
                if new_match:
                    already += 1
                    continue
                if not old_match:
                    raise ValueError(f"{filename}: provenance metadata conflict for {raw_id}")
                for key in keys:
                    row[key] = patch["corrected_" + key]
                row["correction_checkpoint"] = filename
                row["correction_evidence"] = patch.get("evidence_source_url")
                row["corrected_at"] = patch.get("detected_at")
                changed += 1
                continue
            if kind == "grade":
                if patch.get("field") != "grade" or row.get("year") != patch["year"]:
                    raise ValueError(f"{filename}: grade/year mismatch for {raw_id}")
                key, old, new = "grade", patch["original_value"], patch["corrected_value"]
            else:
                key, old, new = "type", patch["previous_type"], patch["corrected_type"]
            current = row.get(key)
            if current == new:
                already += 1
                continue
            if current != old:
                raise ValueError(f"{filename}: {raw_id} {key} conflict: {current!r} != {old!r}")
            row[key] = new
            if kind == "type":
                row["competition"] = None
                row["reason"] = patch["reason"]
                row["confidence"] = patch["confidence"]
            row["correction_checkpoint"] = filename
            row["correction_evidence"] = patch.get("evidence_url") or patch.get("evidence_source")
            row["corrected_at"] = patch.get("reviewed_at") or patch.get("detected_at")
            changed += 1

    if changed:
        content = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows).encode("utf-8")
        fd, name = tempfile.mkstemp(prefix=".rift-corrections-", dir=str(ROOT))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, TARGET)
        finally:
            if os.path.exists(name):
                os.unlink(name)
    print(f"RIFT audited corrections: changed={changed} already={already} total={len(rows)}")
    return changed

if __name__ == "__main__":
    apply()
