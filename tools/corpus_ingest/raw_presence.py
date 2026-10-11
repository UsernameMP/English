#!/usr/bin/env python3
"""Minimum RAW presence across (discovery segment, education level, subject, season, grade).

This is an *existence map*, not a claim that an olympiad set is complete.
Unknown cells mean NO EVIDENCE IN CURRENT CORPUS, never "no olympiad exists".
Only original task-role RAW with a real SHA-256 turns a cell green.

The approved competition season/grade ranges are weak CATALOG HINTS, not
evidence that an edition or a task really existed at that coordinate.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from discovery_network import OUTPUT as NETWORK_OUTPUT
from coverage_dashboard import REGISTRY

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "tools/document_triage/corpus/ru/presence.json"
STATES = ("unknown", "catalogued", "located", "raw")
STATE_RANK = {v: i for i, v in enumerate(STATES)}
GRADES = tuple(range(1, 12))


def expand_school_grades(band: str | int | None) -> tuple[int, ...]:
    """Expand *explicitly* stated bands only; refuse ungrounded inferred ages."""
    if band is None:
        return ()
    value = str(band).strip().replace("–", "-").replace("—", "-")
    match = re.fullmatch(r"(\d{1,2})(?:-(\d{1,2}))?", value)
    if not match:
        return ()
    low = int(match.group(1))
    high = int(match.group(2) or match.group(1))
    if low not in GRADES or high not in GRADES or low > high:
        return ()
    return tuple(range(low, high + 1))


def score_document(obs: dict, assets: dict[str, dict]) -> str:
    """Task links are yellow; downloaded task content is green."""
    if obs.get("classification", {}).get("document_role") != "tasks":
        return "unknown"
    sha_ref = obs.get("asset_id")
    asset = assets.get(sha_ref) if sha_ref else None
    if (obs.get("fetch_status") in {"DOWNLOADED", "DUPLICATE"}
            and asset and asset.get("has_raw_download") is True):
        return "raw"
    return "located"


def compute_presence(registry: dict, network: dict, timestamp: str | None = None) -> dict:
    if network.get("schema_version") != "discovery.network.v1":
        raise ValueError("Unexpected discovery network schema")
    segment = network["segment"]["id"]
    allowed = {c["id"]: c for c in registry["competitions"]
               if segment in c.get("discovery_segment_ids", [])}
    subjects = [dict(s) for s in registry["subjects"]]
    subject_ids = {s["id"] for s in subjects}
    asset_by_id = {a["id"]: a for a in network.get("raw_assets", [])}

    cells: dict[tuple, dict] = {}
    no_slot: list[dict] = []
    no_slot_causes: Counter[str] = Counter()

    # weak hints from approved catalog; do NOT assert task existence or editions.
    for comp in allowed.values():
        level = comp.get("education_level", "school")
        if level not in {"school", "university"}:
            continue
        for sub in comp["subject_ids"]:
            if sub not in subject_ids:
                continue
            for year in range(comp["from"], comp["to"] + 1):
                if level == "school":
                    if comp["grade_min"] is None or comp["grade_max"] is None:
                        continue
                    grades = [str(g) for g in GRADES
                              if comp["grade_min"] <= g <= comp["grade_max"]]
                else:
                    grades = ["university"]
                for grade in grades:
                    key = (level, sub, year, grade)
                    if key not in cells:
                        cells[key] = {
                            "education_level": level, "subject_id": sub,
                            "season": year, "grade": grade,
                            "state": "catalogued",
                            "catalog_competition_ids": [],
                            "observed_competition_ids": [],
                            "task_urls": 0,
                            "task_raw_hashes": [],
                            "raw_evidence": [],
                            "located_evidence": [],
                            "other_material_urls": 0,
                        }
                    if comp["id"] not in cells[key]["catalog_competition_ids"]:
                        cells[key]["catalog_competition_ids"].append(comp["id"])

    def get_cell(level: str, subject: str, season: int, grade: str) -> dict:
        key = (level, subject, season, grade)
        if key not in cells:
            cells[key] = {
                "education_level": level, "subject_id": subject,
                "season": season, "grade": grade,
                "state": "unknown",
                "catalog_competition_ids": [],
                "observed_competition_ids": [],
                "task_urls": 0, "task_raw_hashes": [],
                "raw_evidence": [], "located_evidence": [],
                "other_material_urls": 0,
            }
        return cells[key]

    for obs in network.get("observations", []):
        c = obs.get("classification") or {}
        subject = c.get("subject_id")
        year = c.get("season")
        # Only explicit education-level field can give university.
        level = c.get("education_level", "school")
        if level == "university":
            grades = ("university",)
        elif level == "school":
            grades = tuple(str(g) for g in expand_school_grades(c.get("grade_band")))
        else:
            grades = ()
        missing = []
        if subject not in subject_ids:
            missing.append("subject")
        if not isinstance(year, int) or year < 1850 or year > 2150:
            missing.append("season")
        if not grades:
            missing.append("grade_or_level")
        if missing:
            reason = "+".join(missing)
            no_slot_causes[reason] += 1
            if len(no_slot) < 40:
                no_slot.append({
                    "url": obs.get("url"), "document_role": c.get("document_role"),
                    "fetch_status": obs.get("fetch_status"), "missing": missing,
                    "subject_id": subject, "season": year,
                    "grade_band": c.get("grade_band"),
                })
            continue
        tier = score_document(obs, asset_by_id)
        cid = c.get("competition_id")
        for grade in grades:
            cell = get_cell(level, subject, year, grade)
            if cid in allowed and cid not in cell["observed_competition_ids"]:
                cell["observed_competition_ids"].append(cid)
            if tier == "unknown":
                cell["other_material_urls"] += 1
                continue
            cell["task_urls"] += 1
            if STATE_RANK[tier] > STATE_RANK[cell["state"]]:
                cell["state"] = tier
            ref = {"url": obs.get("url"), "status": obs.get("fetch_status"),
                   "competition_id": cid, "round_id": c.get("stage_id"),
                   "sha256": obs.get("asset_id"), "assertion": c.get("assertion")}
            if tier == "raw":
                if obs["asset_id"] not in cell["task_raw_hashes"]:
                    cell["task_raw_hashes"].append(obs["asset_id"])
                if len(cell["raw_evidence"]) < 12:
                    cell["raw_evidence"].append(ref)
            elif len(cell["located_evidence"]) < 12:
                cell["located_evidence"].append(ref)

    items = []
    for cell in cells.values():
        cell["catalog_competition_ids"].sort()
        cell["observed_competition_ids"].sort()
        cell["task_raw_hashes"].sort()
        for kind in ("raw_evidence", "located_evidence"):
            cell[kind].sort(key=lambda x: x.get("url") or "")
        cell["raw_task_count_unique"] = len(cell["task_raw_hashes"])
        items.append(cell)
    items.sort(key=lambda c: (
        c["education_level"], c["subject_id"], c["season"],
        -1 if c["grade"] == "university" else int(c["grade"])))

    return {
        "schema_version": "discovery.raw_presence.v1",
        "generated_at": timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "segment": network["segment"],
        "upstream": {"origin": network.get("origin"),
                     "observations": network.get("summary", {}).get("url_observations"),
                     "source_schema": network["schema_version"]},
        "subject_catalog": subjects,
        "competition_catalog": [{
            "id": c["id"], "name": c["name"],
            "subject_ids": c["subject_ids"],
            "education_level": c.get("education_level", "school"),
            "seasons_approx": [c["from"], c["to"]],
            "grades_approx": [c.get("grade_min"), c.get("grade_max")],
            "native_stages": c["stages"],
            "archive_links": c.get("archive_links", []),
        } for c in allowed.values()],
        "school_grade_domain": list(GRADES),
        "education_levels": ["school", "university"],
        "cells": items,
        "unplaced_observation_count": sum(no_slot_causes.values()),
        "unplaced_reasons": dict(sorted(no_slot_causes.items())),
        "unplaced_examples": no_slot,
        "semantics": {
            "unknown": "Нет свидетельств в текущем корпусе; существование олимпиад не отрицается.",
            "catalogued": "Известна олимпиада с приблизительным периодом/классами; конкретный выпуск ещё не подтверждён.",
            "located": "Обнаружена ссылка на файл заданий с годом, предметом и классом, но RAW не сохранён.",
            "raw": "Получен оригинальный файл заданий с SHA-256; метаданные уровня/класса/года могут быть выведены из имени файла и не проверены человеком.",
            "not_progress_percent": "Цвет обозначает минимально доказанное присутствие, не полноту олимпиад.",
            "school_years": "Период, выбранный в интерфейсе, — горизонт исследования, а не дата начала существования предмета.",
            "university": "Университетские материалы не являются 12-м классом. Нет данных — unknown, а не nonexistent.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", type=Path, default=NETWORK_OUTPUT)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    net = json.loads(args.network.read_text(encoding="utf-8"))
    reg = json.loads(args.registry.read_text(encoding="utf-8"))
    result = compute_presence(reg, net)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tally = Counter(c["state"] for c in result["cells"])
    print(f"RAW minimum presence: {len(result['cells'])} materialized cells; "
          f"{dict(tally)}; {result['unplaced_observation_count']} unplaced observations")


if __name__ == "__main__":
    main()
