#!/usr/bin/env python3
"""Build a static Corpus Coverage snapshot from the canonical registry and RAW crawl state.

The registry is hand-edited; coverage.json is generated. Unknown data never
becomes a fake completeness percentage. Uses standard library only.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import urllib.request
import urllib.parse
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "tools/corpus_ingest/registry/competitions.json"
STATE = ROOT / "tools/corpus_ingest/state/crawl_state.jsonl"
OUTPUT = ROOT / "tools/document_triage/corpus/coverage.json"
PARSE = ROOT / "tools/corpus_ingest/state/parse_state.jsonl"

STATUS_KEYS = ("PENDING", "DOWNLOADED", "DUPLICATE", "FAILED_RETRYABLE",
               "FAILED_TERMINAL", "CLAIMED", "DOWNLOADING")
ROLE_KEYS = ("tasks", "answers", "criteria", "script", "audio", "other")


def read_jsonl_bytes(data: bytes) -> list[dict]:
    return [json.loads(s) for s in data.decode("utf-8-sig").splitlines() if s.strip()]


def read_jsonl(path: Path) -> list[dict]:
    return read_jsonl_bytes(path.read_bytes()) if path.exists() else []


def merge_checkpoint_rows(github_rows: list[dict], dropbox_rows: list[dict]) -> list[dict]:
    """Keep the freshest record of each document from GitHub or Dropbox.

    GitHub can continue to record discoveries when Dropbox reaches capacity,
    so a successful Dropbox fetch does NOT imply its state is complete.
    """
    merged: dict[str, dict] = {}
    for row in [*dropbox_rows, *github_rows]:
        identity = row.get("document_id") or row.get("url")
        if not identity:
            continue
        old = merged.get(identity)
        if old is None or (row.get("updated_at") or "") >= (old.get("updated_at") or ""):
            merged[identity] = row
    return sorted(merged.values(), key=lambda row: (row.get("source_id", ""), row.get("url", "")))


def dropbox_checkpoint(filename: str = "checkpoint.jsonl") -> bytes | None:
    key, secret, refresh = (os.getenv(k, "") for k in
                            ("DROPBOX_APP_KEY", "DROPBOX_APP_SECRET", "DROPBOX_REFRESH_TOKEN"))
    if not all((key, secret, refresh)):
        return None
    auth = base64.b64encode(f"{key}:{secret}".encode()).decode()
    request = urllib.request.Request(
        "https://api.dropboxapi.com/oauth2/token",
        data=urllib.parse.urlencode({"grant_type": "refresh_token",
                                      "refresh_token": refresh}).encode(),
        headers={"Authorization": f"Basic {auth}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        token = json.load(response)["access_token"]
    path = os.getenv("DROPBOX_ROOT", "/OlympiadCorpus").rstrip("/") + "/state/" + filename
    download = urllib.request.Request(
        "https://content.dropboxapi.com/2/files/download",
        data=b"",
        headers={"Authorization": f"Bearer {token}",
                 "Dropbox-API-Arg": json.dumps({"path": path})},
    )
    with urllib.request.urlopen(download, timeout=60) as response:
        return response.read()


def validate_registry(registry: dict) -> None:
    subjects = [s["id"] for s in registry["subjects"]]
    assert len(subjects) == len(set(subjects)), "duplicate subject IDs"
    competitions = [c["id"] for c in registry["competitions"]]
    assert len(competitions) == len(set(competitions)), "duplicate competition IDs"
    assert subjects and competitions
    for competition in registry["competitions"]:
        assert set(competition["subject_ids"]) <= set(subjects)
        assert competition["from"] <= competition["to"]
        stages = [s["id"] for s in competition["stages"]]
        assert stages and len(stages) == len(set(stages))
        for link in competition.get("archive_links", []):
            assert urlparse(link["url"]).scheme == "https"
    for source in registry["competitions"]:
        for linked in source.get("source_ids", []):
            assert isinstance(linked, str) and linked


def identify(record: dict, registry: dict) -> dict:
    url = record.get("url", "")
    name = urlparse(url).path.rsplit("/", 1)[-1].lower()
    sid = record.get("source_id", "")
    competition = next((c for c in registry["competitions"]
                        if sid in c.get("source_ids", [])), None)
    if not competition and (sid.startswith("vosh_") or "olimpiada_ru_engl_archive" == sid):
        competition = next(c for c in registry["competitions"] if c["id"] == "vsosh")

    subjects = {"engl": "english", "math": "mathematics",
                "inf": "informatics", "iikt": "informatics",
                "prog": "informatics", "robot": "informatics",
                "fiz": "physics", "bio": "biology",
                "chem": "chemistry", "rus": "russian"}
    short = re.search(r"(?:^|-)(engl|math|inf|iikt|prog|robot|fiz|bio|chem|rus)(?:-|\.)", name)
    subject = subjects[short.group(1)] if short else None
    if not subject and sid.startswith("vosh_engl"):
        subject = "english"
    if not subject and (sid.startswith("olimpiada_ru_math_school")
                        or sid.startswith("vosh_2024_math_school")):
        subject = "mathematics"
    if not subject and (sid.startswith("olimpiada_ru_inf_school")
                        or sid.startswith("vosh_2024_inf_school")):
        subject = "informatics"

    yr = re.search(r"(?<!\d)(20\d{2})[-/](20\d{2})(?!\d)", url)
    season = int(yr.group(1)) if yr else None
    if season is None:
        # Paths like /tasks/73/2024/ are unambiguous. Prefer them over
        # grade bands like iikt-10-11 which otherwise look like year 2010/11.
        yr = re.search(r"/(20\d{2})/", url)
        season = int(yr.group(1)) if yr else None
    if season is None:
        # When the URL has no explicit four-digit year, a trailing two-digit
        # season may be inferred only after all grade-band tokens.
        years = [
            2000 + int(m.group(1))
            for m in re.finditer(r"(?<!\d)(\d{2})-(\d{2})(?!\d)", name)
            if int(m.group(2)) == (int(m.group(1)) + 1) % 100
        ]
        if years:
            season = years[-1]

    stage = None
    for pattern, value in ((r"(?:-|/)sch(?:-|/|\.|$)|school", "school"),
                           (r"(?:-|/)mun(?:-|/|\.|$)|municipal", "municipal"),
                           (r"(?:-|/)reg(?:-|/|\.|$)|regional", "regional"),
                           (r"(?:-|/)(?:fin|final)(?:-|/|\.|$)", "final")):
        if re.search(pattern, name + " " + urlparse(url).path.lower()):
            stage = value
            break
    # This fallback is allowed only for source IDs whose crawler adapter
    # explicitly restricts discovery to the school-stage HTML section.
    if stage is None and sid in {
        "olimpiada_ru_math_school_archive", "olimpiada_ru_inf_school_archive",
        "vosh_2024_math_school_sirius_11", "vosh_2024_inf_school_sirius_10_11",
    }:
        stage = "school"

    grades = None
    if short:
        tail = name[short.end():]
        m = re.match(r"(\d{1,2})(?:-(\d{1,2}))?(?:-|\.)", tail)
        if m:
            grades = m.group(1) + (("–" + m.group(2)) if m.group(2) else "")

    if re.search(r"(?:^|[-/])(tasks?|zadan)", name): role = "tasks"
    elif re.search(r"(?:^|[-/])(ans|otv)", name): role = "answers"
    elif re.search(r"(?:^|[-/])(krit|crit|criteria)", name): role = "criteria"
    elif re.search(r"(?:^|[-/])script", name): role = "script"
    elif name.endswith((".mp3", ".wav", ".m4a")): role = "audio"
    else: role = "other"
    return {"competition_id": competition["id"] if competition else None,
            "subject_id": subject, "season": season, "stage_id": stage,
            "grade_band": grades or "не указан", "role": role}


def generate(registry: dict, records: list[dict], parsed: list[dict] | None = None,
             origin: str = "Dropbox RAW checkpoint") -> dict:
    validate_registry(registry)
    by_hash = {rec.get("document_sha256"): rec.get("status")
               for rec in (parsed or []) if rec.get("document_sha256")}
    statuses = Counter(rec.get("status", "UNKNOWN") for rec in records)
    cells: dict[tuple, dict] = {}
    unclassified = Counter()
    latest = None
    for rec in records:
        meta = identify(rec, registry)
        stamp = rec.get("updated_at") or rec.get("first_seen")
        if stamp and (latest is None or stamp > latest):
            latest = stamp
        if not meta["competition_id"] or not meta["subject_id"] or not meta["season"] or not meta["stage_id"]:
            missing = ",".join(k for k in ("competition_id", "subject_id", "season", "stage_id") if not meta[k])
            unclassified[missing] += 1
            continue
        key = tuple(meta[k] for k in ("competition_id", "subject_id", "season", "stage_id", "grade_band"))
        if key not in cells:
            cells[key] = {k: meta[k] for k in ("competition_id", "subject_id", "season", "stage_id", "grade_band")}
            cells[key].update({"statuses": {}, "roles": {}, "parse_statuses": {}, "examples": [], "urls": 0})
        cell = cells[key]
        status = rec.get("status", "UNKNOWN")
        cell["urls"] += 1
        cell["statuses"][status] = cell["statuses"].get(status, 0) + 1
        cell["roles"][meta["role"]] = cell["roles"].get(meta["role"], 0) + 1
        sha = rec.get("sha256")
        if sha in by_hash and status in ("DOWNLOADED", "DUPLICATE"):
            ps = by_hash[sha]
            cell["parse_statuses"][ps] = cell["parse_statuses"].get(ps, 0) + 1
        if len(cell["examples"]) < 4:
            cell["examples"].append({"url": rec.get("url"), "status": status, "role": meta["role"]})

    return {"schema_version": "corpus_coverage.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "state_latest_update": latest,
            "origin": origin,
            "summary": {"urls": len(records), "statuses": dict(sorted(statuses.items())),
                        "identified_urls": sum(x["urls"] for x in cells.values()),
                        "unclassified_urls": sum(unclassified.values()),
                        "parsed_document_hashes": len(by_hash)},
            "unclassified_reasons": dict(sorted(unclassified.items())),
            "cells": sorted(cells.values(), key=lambda x: (
                x["competition_id"], x["subject_id"], -x["season"], x["stage_id"], x["grade_band"]))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--checkpoint", type=Path, default=STATE)
    parser.add_argument("--parse-state", type=Path, default=PARSE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--refresh-dropbox", action="store_true")
    args = parser.parse_args()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    validate_registry(registry)
    checkpoint = None
    origin = str(args.checkpoint)
    if args.refresh_dropbox:
        try:
            checkpoint = dropbox_checkpoint()
            if checkpoint:
                origin = "Dropbox /OlympiadCorpus/state/checkpoint.jsonl"
        except Exception as exc:
            print(f"WARNING: could not refresh Dropbox: {exc}")
    if checkpoint is None:
        if args.checkpoint.exists() and args.checkpoint.stat().st_size > 0:
            checkpoint = args.checkpoint.read_bytes()
        elif args.output.exists():
            print("WARNING: no live checkpoint. Keeping previous labeled snapshot.")
            return
        else:
            raise SystemExit("Cannot build: no checkpoint and no existing coverage snapshot")
    # Include GitHub-side discoveries not yet written back to a full Dropbox.
    records = merge_checkpoint_rows(read_jsonl(args.checkpoint), read_jsonl_bytes(checkpoint))
    if not records:
        raise SystemExit("Refusing to replace coverage with an empty checkpoint")
    if args.checkpoint.exists() and args.checkpoint.stat().st_size:
        origin += " + GitHub local crawler state (latest wins)"
    parsed = read_jsonl(args.parse_state)
    if args.refresh_dropbox:
        try:
            parsed_bytes = dropbox_checkpoint("parse_state.jsonl")
            if parsed_bytes:
                parsed = read_jsonl_bytes(parsed_bytes)
        except Exception as exc:
            print(f"WARNING: parse-state unavailable: {exc}")
    result = generate(registry, records, parsed, origin)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Coverage built: {result['summary']['urls']} URLs / {len(result['cells'])} cells / {result['summary']['unclassified_urls']} unclassified")


if __name__ == "__main__":
    main()
