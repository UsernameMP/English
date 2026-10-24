#!/usr/bin/env python3
"""Idempotently merge explicitly audited RIFT Review checkpoints, without downloading documents.

Only the explicitly audited reviewed resource shards listed here are eligible. Older historical
checkpoints require separate reconciliation and are intentionally not merged.
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "link_labels.jsonl"
CHECKPOINTS = {
    "r294_review_r299.jsonl": "bc2fb77519dbc39631edc2166315fc72703cae3a",
    "r295_review_r300.jsonl": "c578f9c6b466ce51704d0ec31c49c5c61d20ed1f",
    "r296_review_r301.jsonl": "1f3ad337080850ecd2c54105d33f8bab4231d0ab",
    "r297_review_r302.jsonl": "65d4536e4828574921456ce649dafb94a3b4995e",
    "r298_review_r303.jsonl": "08ad3a871798448ffc2bacdb591d0ae2ac4fd37a",
    "r299_review_r304.jsonl": "293a93e58479ccc7806638c5fcfa916273e9959e",
    "r300_review_r305.jsonl": "f7639b0785919311d3df88405cb6b8462c3b89fb",
    "r301_review_r306.jsonl": "9f574a33f87a1f2c06fef96442a62b738f982a4e",
}
ALLOWED_TYPES = {"task", "solution", "criteria", "participant_work", "archive", "source", "unrelated", "review"}


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def parse_jsonl(data, label):
    rows = []
    for line_no, line in enumerate(data.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{label}:{line_no}: malformed JSON") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"{label}:{line_no}: expected object")
        rows.append(obj)
    return rows


def merge():
    old_data = TARGET.read_bytes()
    canonical = parse_jsonl(old_data, TARGET.name)
    by_occurrence = {}
    by_resource = {}
    for row in canonical:
        occurrence = row.get("raw_occurrence_id") or row.get("id")
        resource = row.get("resource_id")
        if occurrence:
            if occurrence in by_occurrence:
                raise ValueError(f"Duplicate canonical raw occurrence: {occurrence}")
            by_occurrence[occurrence] = row
        if resource:
            by_resource.setdefault(resource, row)

    new = []
    skipped = 0
    for filename, expected_sha in CHECKPOINTS.items():
        path = ROOT / "runs" / filename
        data = path.read_bytes()
        actual_sha = git_blob_sha(data)
        if actual_sha != expected_sha:
            raise ValueError(f"{filename}: unexpected Git blob SHA {actual_sha}")
        rows = parse_jsonl(data, filename)
        if len(rows) != 100:
            raise ValueError(f"{filename}: expected 100 records, got {len(rows)}")
        for row in rows:
            occ = row.get("raw_occurrence_id")
            rid = row.get("resource_id")
            url = row.get("url")
            kind = row.get("type")
            if not occ or not rid or not url or kind not in ALLOWED_TYPES:
                raise ValueError(f"{filename}: incomplete review row {occ!r}")
            prior = by_occurrence.get(occ)
            if prior:
                if prior.get("resource_id") != rid or prior.get("url") != url or prior.get("type") != kind:
                    raise ValueError(f"Conflicting occurrence: {occ}")
                skipped += 1
                continue
            prior_resource = by_resource.get(rid)
            if prior_resource:
                if prior_resource.get("url") != url or prior_resource.get("type") != kind:
                    raise ValueError(f"Conflicting resource: {rid}")
                skipped += 1
                continue
            by_occurrence[occ] = row
            by_resource[rid] = row
            new.append(row)

    if new:
        addition = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in new)
        prefix = old_data + (b"\n" if old_data and not old_data.endswith(b"\n") else b"")
        content = prefix + addition.encode("utf-8")
        fd, temp_name = tempfile.mkstemp(prefix=".rift-labels-", dir=str(ROOT))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, TARGET)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
    print(f"RIFT reviewed checkpoint merge: existing={len(canonical)} added={len(new)} skipped={skipped} total={len(canonical)+len(new)}")
    return len(new)


if __name__ == "__main__":
    merge()
