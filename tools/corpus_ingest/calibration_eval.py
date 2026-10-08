from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "calibration-report.v2"


def _norm(value: object) -> str:
    return re.sub(r"[^a-z0-9а-яё]+", " ", str(value or "").lower(), flags=re.I).strip()


def _section_key(section: dict[str, Any]) -> str:
    semantic = _norm(section.get("semantic_type"))
    label = _norm(section.get("label"))
    # Semantic type helps cross-template matching, but repeated sets retain their label.
    if semantic == "speaking_set":
        return label
    return semantic if semantic and semantic != "unknown" else label


def _task_key(task: dict[str, Any]) -> str:
    number = str(task.get("number") or "").strip()
    if number:
        return "n:" + number.lower()
    label = _norm(task.get("label"))
    m = re.search(r"\b(?:task|problem|question|задание|задача)\s*([0-9a-zа-я]+)\b", label, re.I)
    if m:
        return "n:" + m.group(1).lower()
    return "l:" + label


def _pair_by_key(gold: list[dict[str, Any]], machine: list[dict[str, Any]], key_fn):
    buckets: dict[str, list[int]] = {}
    for idx, item in enumerate(machine):
        buckets.setdefault(key_fn(item), []).append(idx)
    used: set[int] = set()
    pairs: list[tuple[dict[str, Any], dict[str, Any] | None]] = []
    for g in gold:
        key = key_fn(g)
        candidates = [i for i in buckets.get(key, []) if i not in used]
        if candidates:
            idx = candidates[0]
            used.add(idx)
            pairs.append((g, machine[idx]))
        else:
            pairs.append((g, None))
    extras = [m for i, m in enumerate(machine) if i not in used]
    return pairs, extras


def _span_ok(gold: dict[str, Any], machine: dict[str, Any] | None) -> bool | None:
    if machine is None:
        return False
    if str(gold.get("quality") or "") == "NEEDS_BOUNDARY_RECHECK":
        return None
    gs = int(gold.get("page_start") or 1)
    ge = int(gold.get("page_end") or gs)
    ms = int(machine.get("page_start") or machine.get("start") or 1)
    me = int(machine.get("page_end") or machine.get("end") or ms)
    return gs == ms and ge == me


def evaluate_document(
    document_id: str,
    gold_doc: dict[str, Any],
    machine: dict[str, Any],
) -> dict[str, Any]:
    gold_sections = list(gold_doc.get("sections") or [])
    machine_sections = list(machine.get("sections") or [])
    section_pairs, section_extras = _pair_by_key(gold_sections, machine_sections, _section_key)

    section_hits = sum(1 for _, m in section_pairs if m is not None)
    section_span_results = [_span_ok(g, m) for g, m in section_pairs if m is not None]
    section_span_scored = [x for x in section_span_results if x is not None]

    gold_task_total = 0
    task_hits = 0
    known_kind_total = 0
    known_kind_hits = 0
    gold_artifact_total = 0
    artifact_kind_hits = 0
    task_span_results: list[bool] = []
    body_reconstructed_tasks = 0
    review_required_tasks = 0
    asset_binding_confidences: list[float] = []
    gold_body_span_total = 0
    gold_body_span_hits = 0
    misses: list[dict[str, Any]] = []

    for gold_section, machine_section in section_pairs:
        gold_tasks = list(gold_section.get("tasks") or [])
        gold_task_total += len(gold_tasks)
        if machine_section is None:
            for task in gold_tasks:
                misses.append({
                    "kind": "task",
                    "section": gold_section.get("label"),
                    "label": task.get("label"),
                    "reason": "parent_section_missing",
                })
            continue

        machine_tasks = list(machine_section.get("tasks") or [])
        task_pairs, _ = _pair_by_key(gold_tasks, machine_tasks, _task_key)
        for gt, mt in task_pairs:
            if mt is None:
                misses.append({
                    "kind": "task",
                    "section": gold_section.get("label"),
                    "label": gt.get("label"),
                    "reason": "task_missing",
                })
                continue
            task_hits += 1

            if mt.get("body_blocks") and mt.get("body_spans"):
                body_reconstructed_tasks += 1
            if bool(mt.get("review_required")):
                review_required_tasks += 1
            for artifact in mt.get("artifacts") or []:
                if artifact.get("asset_binding_confidence") is not None:
                    asset_binding_confidences.append(float(artifact["asset_binding_confidence"]))

            gold_body_spans = list(gt.get("body_spans") or [])
            if gold_body_spans:
                gold_body_span_total += 1
                machine_body_spans = list(mt.get("body_spans") or [])
                gp = {(int(x.get("page") or 0), tuple(round(float(v), 1) for v in (x.get("bbox") or []))) for x in gold_body_spans}
                mp = {(int(x.get("page") or 0), tuple(round(float(v), 1) for v in (x.get("bbox") or []))) for x in machine_body_spans}
                if gp == mp:
                    gold_body_span_hits += 1

            gkind = str(gt.get("kind") or "UNKNOWN")
            if gkind != "UNKNOWN":
                known_kind_total += 1
                if str(mt.get("kind") or "UNKNOWN") == gkind:
                    known_kind_hits += 1

            if str(gt.get("quality") or "") != "NEEDS_BOUNDARY_RECHECK":
                gs = int(gt.get("page_start") or gt.get("anchor_page") or gold_section.get("page_start") or 1)
                ge = int(gt.get("page_end") or gt.get("anchor_page") or gold_section.get("page_end") or gs)
                ms = int(mt.get("page_start") or mt.get("anchor", {}).get("page") or machine_section.get("page_start") or 1)
                me = int(mt.get("page_end") or machine_section.get("page_end") or ms)
                task_span_results.append(gs == ms and ge == me)

            gold_artifacts = list(gt.get("artifacts") or [])
            machine_artifacts = list(mt.get("artifacts") or [])
            gold_artifact_total += len(gold_artifacts)
            machine_kinds = [str(x.get("kind") or "") for x in machine_artifacts]
            consumed: set[int] = set()
            for ga in gold_artifacts:
                target = str(ga.get("kind") or "")
                # A generic detected TABLE/GRID/DIAGRAM is useful evidence even before
                # a later vision classifier refines FORM/CROSSWORD/OPTIONS_TABLE.
                compatible = {
                    "FORM": {"FORM", "TABLE", "GRID", "DIAGRAM"},
                    "CROSSWORD": {"CROSSWORD", "GRID", "TABLE", "DIAGRAM"},
                    "OPTIONS_TABLE": {"OPTIONS_TABLE", "TABLE", "GRID"},
                    "RESPONSE_TABLE": {"RESPONSE_TABLE", "TABLE", "GRID"},
                    "WORD_BANK": {"WORD_BANK", "TABLE", "DIAGRAM"},
                }.get(target, {target})
                found = next((i for i, mk in enumerate(machine_kinds) if i not in consumed and mk in compatible), None)
                if found is not None:
                    consumed.add(found)
                    artifact_kind_hits += 1

    for g, m in section_pairs:
        if m is None:
            misses.append({"kind": "section", "label": g.get("label"), "reason": "section_missing"})

    def ratio(n: int, d: int) -> float | None:
        return round(n / d, 4) if d else None

    section_recall = ratio(section_hits, len(gold_sections))
    task_recall = ratio(task_hits, gold_task_total)
    known_kind_accuracy = ratio(known_kind_hits, known_kind_total)
    artifact_recall = ratio(artifact_kind_hits, gold_artifact_total)
    section_span_accuracy = ratio(sum(bool(x) for x in section_span_scored), len(section_span_scored))
    task_span_accuracy = ratio(sum(bool(x) for x in task_span_results), len(task_span_results))
    body_reconstruction_coverage = ratio(body_reconstructed_tasks, task_hits)
    body_span_accuracy = ratio(gold_body_span_hits, gold_body_span_total)
    review_required_rate = ratio(review_required_tasks, task_hits)
    asset_binding_confidence_avg = (
        round(sum(asset_binding_confidences) / len(asset_binding_confidences), 4)
        if asset_binding_confidences else None
    )

    reviewable = (
        (section_recall is None or section_recall >= 0.90)
        and (task_recall is None or task_recall >= 0.85)
        and (known_kind_accuracy is None or known_kind_accuracy >= 0.70)
    )

    return {
        "document_id": document_id,
        "filename": gold_doc.get("filename"),
        "gold": {
            "sections": len(gold_sections),
            "tasks": gold_task_total,
            "known_kinds": known_kind_total,
            "artifacts": gold_artifact_total,
        },
        "machine": {
            "sections": len(machine_sections),
            "extra_sections": [x.get("label") for x in section_extras],
            "matched_tasks": task_hits,
            "body_reconstructed_tasks": body_reconstructed_tasks,
            "review_required_tasks": review_required_tasks,
            "asset_binding_samples": len(asset_binding_confidences),
            "asset_binding_confidence_sum": round(sum(asset_binding_confidences), 6),
        },
        "metrics": {
            "section_recall": section_recall,
            "section_span_accuracy": section_span_accuracy,
            "task_recall": task_recall,
            "task_span_accuracy": task_span_accuracy,
            "known_kind_accuracy": known_kind_accuracy,
            "artifact_recall": artifact_recall,
            "body_reconstruction_coverage": body_reconstruction_coverage,
            "body_span_accuracy": body_span_accuracy,
            "asset_binding_confidence_avg": asset_binding_confidence_avg,
            "review_required_rate": review_required_rate,
        },
        "reviewable": reviewable,
        "misses": misses,
        "warnings": list(machine.get("warnings") or []),
    }


def evaluate(gold: dict[str, Any], structures: dict[str, dict[str, Any]]) -> dict[str, Any]:
    docs: list[dict[str, Any]] = []
    for document_id, gold_doc in (gold.get("documents") or {}).items():
        docs.append(evaluate_document(document_id, gold_doc, structures.get(document_id, {"sections": [], "warnings": ["structure_missing"]})))

    def micro(metric: str, numerator: str, denominator: str) -> float | None:
        num = den = 0
        for d in docs:
            g = d["gold"]
            if denominator == "sections":
                den += g["sections"]
                num += round((d["metrics"][metric] or 0) * g["sections"])
            elif denominator == "tasks":
                den += g["tasks"]
                num += round((d["metrics"][metric] or 0) * g["tasks"])
            elif denominator == "known_kinds":
                den += g["known_kinds"]
                num += round((d["metrics"][metric] or 0) * g["known_kinds"])
            elif denominator == "artifacts":
                den += g["artifacts"]
                num += round((d["metrics"][metric] or 0) * g["artifacts"])
        return round(num / den, 4) if den else None

    matched = sum(int(d["machine"].get("matched_tasks") or 0) for d in docs)
    body_done = sum(int(d["machine"].get("body_reconstructed_tasks") or 0) for d in docs)
    review_required = sum(int(d["machine"].get("review_required_tasks") or 0) for d in docs)
    binding_samples = sum(int(d["machine"].get("asset_binding_samples") or 0) for d in docs)
    binding_sum = sum(float(d["machine"].get("asset_binding_confidence_sum") or 0) for d in docs)

    return {
        "schema_version": SCHEMA_VERSION,
        "document_count": len(docs),
        "reviewable_documents": sum(1 for d in docs if d["reviewable"]),
        "metrics": {
            "section_recall_micro": micro("section_recall", "section_hits", "sections"),
            "task_recall_micro": micro("task_recall", "task_hits", "tasks"),
            "known_kind_accuracy_micro": micro("known_kind_accuracy", "known_kind_hits", "known_kinds"),
            "artifact_recall_micro": micro("artifact_recall", "artifact_hits", "artifacts"),
            "body_reconstruction_coverage_micro": round(body_done / matched, 4) if matched else None,
            "asset_binding_confidence_micro": round(binding_sum / binding_samples, 4) if binding_samples else None,
            "review_required_rate_micro": round(review_required / matched, 4) if matched else None,
        },
        "documents": docs,
    }


def load_structures(directory: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path in directory.glob("*.structure.json"):
        doc_id = path.name.removesuffix(".structure.json")
        out[doc_id] = json.loads(path.read_text(encoding="utf-8"))
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--gold", required=True)
    p.add_argument("--structures", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    gold = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    report = evaluate(gold, load_structures(Path(args.structures)))
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["metrics"], ensure_ascii=False))
    print(f"reviewable={report['reviewable_documents']}/{report['document_count']}")


if __name__ == "__main__":
    main()
