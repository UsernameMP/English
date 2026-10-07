from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Any

SCHEMA_VERSION = "structure-proposal.v2"

TASK_RE = re.compile(
    r"^\s*(?:task|problem|question|exercise|задача|задание|вопрос)\s*"
    r"(?:№\s*)?([0-9]{1,3}|[A-ZА-Я])\b[\s.):-]*(.*)$",
    re.I,
)
PART_RE = re.compile(
    r"^\s*(?:part|часть)\s*(?:№\s*)?([0-9]{1,3}|[A-ZА-Я])\b[\s.):-]*(.*)$",
    re.I,
)
ITEM_RE = re.compile(r"^\s*([0-9]{1,3})[.)]\s+\S")
SET_RE = re.compile(r"^\s*(?:speaking\s+)?set\s*([0-9]{1,3}|[A-Z])\b", re.I)

SECTION_PATTERNS = [
    ("LISTENING", re.compile(r"^\s*listening\b", re.I)),
    ("READING", re.compile(r"^\s*reading\b", re.I)),
    ("USE_OF_ENGLISH", re.compile(r"^\s*use\s+of\s+english\b", re.I)),
    ("WRITING", re.compile(r"^\s*writing\b", re.I)),
    ("SPEAKING_SET", re.compile(r"^\s*(?:speaking\s+)?set\s*[0-9A-Z]+\b", re.I)),
    ("SPEAKING", re.compile(r"^\s*speaking\b", re.I)),
    ("TRANSCRIPTION", re.compile(r"^\s*(?:transcription|transcript)\b", re.I)),
    ("ANSWERS", re.compile(r"^\s*(?:listening|reading|use\s+of\s+english)?\s*answers?\b", re.I)),
    ("CRITERIA", re.compile(r"^\s*(?:criteria|критерии\b|критерии\s+оценивания)", re.I)),
    ("METHODOLOGY", re.compile(r"^\s*методическ(?:ие|ая)\s+(?:рекомендации|рекомендация)\b", re.I)),
]

KIND_RULES = [
    ("TRUE_FALSE_NOT_STATED", re.compile(r"true\s*\([^)]*\).*false\s*\([^)]*\).*not\s+stated|true.*false.*not\s+stated", re.I | re.S)),
    ("TRUE_FALSE", re.compile(r"\btrue\b.*\bfalse\b", re.I | re.S)),
    ("FORM_FILL", re.compile(r"complete\s+the\s+form|fill\s+in\s+the\s+form", re.I)),
    ("TABLE_GAP_FILL", re.compile(r"complete\s+the\s+table|fill\s+in\s+the\s+table", re.I)),
    ("KEY_WORD_TRANSFORMATION", re.compile(r"key\s+word|complete.*second\s+sentence.*meaning", re.I | re.S)),
    ("WORD_FORMATION", re.compile(r"word\s+formation|form\s+(?:a|the)\s+word|use\s+the\s+word\s+given", re.I)),
    ("MATCHING", re.compile(r"match\b|choose\s+the\s+correct\s+paragraph|which\s+paragraph", re.I)),
    ("ORDERING", re.compile(r"put.*(?:correct|right)\s+order|arrange.*order", re.I | re.S)),
    ("MULTIPLE_CHOICE_CLOZE", re.compile(r"which\s+answer\s*\(a,?\s*b,?\s*c(?:\s+or\s+d)?\).*fits?\s+each\s+gap", re.I | re.S)),
    ("OPEN_CLOZE", re.compile(r"(?:one|two)\s+word(?:s)?\s+for\s+each\s+(?:answer|gap)|one\s+word\s+per\s+gap", re.I)),
    ("SELECT_ONE", re.compile(r"choose\s+the\s+correct\s+answer|choose\s+(?:a|one)\s+(?:correct\s+)?(?:option|answer)|\bA,?\s*B,?\s*C(?:\s*or\s*D)?\b", re.I)),
    ("GAP_FILL", re.compile(r"complete\s+(?:the\s+)?(?:sentences?|text)|fill\s+(?:in\s+)?(?:the\s+)?gaps?", re.I)),
    ("EXTENDED_RESPONSE", re.compile(r"write\s+(?:your\s+)?(?:essay|article|letter|report|story)|write\s+[0-9]+\s*[-–]\s*[0-9]+\s+words", re.I)),
    ("PROOF", re.compile(r"\bprove\b|\bdokazh|докаж", re.I)),
    ("PROGRAMMING", re.compile(r"write\s+(?:a\s+)?program|algorithm|программ|алгоритм", re.I)),
    ("ORAL_RESPONSE", re.compile(r"monologue|dialogue|speak\b|talk\s+about|устн|монолог|диалог", re.I)),
    ("NUMERIC_RESPONSE", re.compile(r"\bcalculate\b|\bcompute\b|\bfind\s+(?:the\s+)?(?:value|number)|вычисл|найдите\s+(?:значение|число)", re.I)),
]


def _stable(prefix: str, *parts: object) -> str:
    raw = "|".join(str(x).strip().lower() for x in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:20]}"


def _bbox_area(box: list[float] | tuple[float, ...] | None) -> float:
    if not box or len(box) != 4:
        return 0.0
    return max(0.0, float(box[2]) - float(box[0])) * max(0.0, float(box[3]) - float(box[1]))


def flatten_lines(layout: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for page in layout.get("pages", []):
        page_no = int(page.get("page_number") or 1)
        page_h = float(page.get("height") or 0)
        for block in page.get("blocks", []):
            for line in block.get("lines", []):
                text = str(line.get("text") or "").strip()
                if not text:
                    continue
                spans = line.get("spans") or []
                sizes = [float(s.get("size") or 0) for s in spans if float(s.get("size") or 0) > 0]
                flags = [int(s.get("flags") or 0) for s in spans]
                lines.append({
                    "id": line.get("id") or _stable("line", page_no, line.get("bbox"), text),
                    "text": text,
                    "page": page_no,
                    "bbox": line.get("bbox") or [0, 0, 0, 0],
                    "font_size": max(sizes) if sizes else 0.0,
                    "boldish": any(f & 16 for f in flags),
                    "page_height": page_h,
                })
    lines.sort(key=lambda x: (x["page"], round(float(x["bbox"][1]), 2), float(x["bbox"][0])))
    return lines


def infer_task_kind(text: str, *, has_parts: bool = False) -> str:
    if has_parts:
        return "COMPOSITE"
    for kind, pattern in KIND_RULES:
        if pattern.search(text or ""):
            return kind
    return "UNKNOWN"


def _explicit_section_type(text: str) -> str | None:
    for kind, pattern in SECTION_PATTERNS:
        if pattern.search(text):
            return kind
    return None


def _heading_score(line: dict[str, Any], median_size: float) -> float:
    text = line["text"].strip()
    if not text or len(text) > 90:
        return 0.0
    explicit = _explicit_section_type(text)
    if explicit:
        return 1.0
    score = 0.0
    alpha = [c for c in text if c.isalpha()]
    if alpha and sum(c.isupper() for c in alpha) / len(alpha) >= 0.8:
        score += 0.35
    if median_size and line["font_size"] >= median_size * 1.18:
        score += 0.25
    if line["boldish"]:
        score += 0.15
    if len(text) <= 40:
        score += 0.10
    return score


def detect_section_starts(lines: list[dict[str, Any]]) -> list[int]:
    if not lines:
        return []
    sizes = sorted(x["font_size"] for x in lines if x["font_size"] > 0)
    median = sizes[len(sizes) // 2] if sizes else 0.0
    explicit = [i for i, line in enumerate(lines) if _explicit_section_type(line["text"])]
    if explicit:
        return explicit
    return [i for i, line in enumerate(lines) if _heading_score(line, median) >= 0.65]


def detect_task_starts(lines: list[dict[str, Any]], start: int, end: int) -> list[int]:
    return [i for i in range(start, end) if TASK_RE.match(lines[i]["text"])]


def _task_number(text: str) -> str:
    m = TASK_RE.match(text)
    return m.group(1) if m else ""


def _task_label(text: str) -> str:
    m = TASK_RE.match(text)
    if not m:
        return text[:80]
    return f"Task {m.group(1)}"


def _part_nodes(lines: list[dict[str, Any]], start: int, end: int, task_id: str) -> list[dict[str, Any]]:
    starts = [i for i in range(start + 1, end) if PART_RE.match(lines[i]["text"])]
    parts: list[dict[str, Any]] = []
    for pos, idx in enumerate(starts):
        stop = starts[pos + 1] if pos + 1 < len(starts) else end
        m = PART_RE.match(lines[idx]["text"])
        text = "\n".join(x["text"] for x in lines[idx:stop])
        parts.append({
            "id": _stable("part", task_id, lines[idx]["id"]),
            "label": f"Part {m.group(1)}",
            "page_start": lines[idx]["page"],
            "page_end": lines[stop - 1]["page"],
            "anchor": {"page": lines[idx]["page"], "line_id": lines[idx]["id"], "text": lines[idx]["text"]},
            "kind": infer_task_kind(text),
            "confidence": 0.94,
        })
    return parts


def _item_range(lines: list[dict[str, Any]], start: int, end: int) -> dict[str, int] | None:
    nums: list[int] = []
    for line in lines[start + 1:end]:
        m = ITEM_RE.match(line["text"])
        if m:
            nums.append(int(m.group(1)))
    if not nums:
        return None
    # Keep the observed bounds but avoid treating obvious page numbers / years as items.
    counts = Counter(nums)
    usable = [n for n in nums if 0 <= n <= 300 and counts[n] <= 3]
    if not usable:
        return None
    return {"start": min(usable), "end": max(usable), "count_observed": len(set(usable))}


def _task_region(lines: list[dict[str, Any]], start: int, end: int) -> dict[int, tuple[float, float]]:
    first = lines[start]
    last = lines[end - 1]
    pages = range(first["page"], last["page"] + 1)
    out: dict[int, tuple[float, float]] = {}
    for page in pages:
        same = [x for x in lines[start:end] if x["page"] == page]
        if not same:
            continue
        y0 = min(float(x["bbox"][1]) for x in same)
        y1 = max(float(x["bbox"][3]) for x in same)
        out[page] = (y0, y1)
    return out


def _overlaps_vertical(box: list[float], band: tuple[float, float]) -> bool:
    if not box or len(box) != 4:
        return False
    return min(float(box[3]), band[1]) - max(float(box[1]), band[0]) > 1


def _artifact_nodes(layout: dict[str, Any], lines: list[dict[str, Any]], start: int, end: int, task_id: str) -> list[dict[str, Any]]:
    regions = _task_region(lines, start, end)
    artifacts: list[dict[str, Any]] = []
    for page in layout.get("pages", []):
        page_no = int(page.get("page_number") or 1)
        band = regions.get(page_no)
        if not band:
            continue
        for table in page.get("tables", []):
            box = table.get("bbox") or [0, 0, 0, 0]
            if not _overlaps_vertical(box, band):
                continue
            cells = table.get("cells") or []
            w = max(1.0, float(box[2]) - float(box[0]))
            h = max(1.0, float(box[3]) - float(box[1]))
            ratio = w / h
            kind = "GRID" if len(cells) >= 16 and 0.55 <= ratio <= 1.8 else "TABLE"
            artifacts.append({
                "id": _stable("artifact", task_id, table.get("id") or box),
                "kind": kind,
                "page": page_no,
                "bbox": box,
                "source_id": table.get("id"),
                "confidence": 0.90 if kind == "TABLE" else 0.78,
            })
        for image in page.get("images", []):
            box = image.get("bbox") or [0, 0, 0, 0]
            if _overlaps_vertical(box, band):
                artifacts.append({
                    "id": _stable("artifact", task_id, image.get("id") or box),
                    "kind": "IMAGE",
                    "page": page_no,
                    "bbox": box,
                    "source_id": image.get("id"),
                    "confidence": 0.92,
                })
        drawings = [d for d in page.get("drawings", []) if _overlaps_vertical(d.get("bbox") or [0, 0, 0, 0], band)]
        if len(drawings) >= 4:
            box = [
                min(float(d["bbox"][0]) for d in drawings),
                min(float(d["bbox"][1]) for d in drawings),
                max(float(d["bbox"][2]) for d in drawings),
                max(float(d["bbox"][3]) for d in drawings),
            ]
            if _bbox_area(box) > 100:
                artifacts.append({
                    "id": _stable("artifact", task_id, page_no, "drawings", len(drawings)),
                    "kind": "DIAGRAM",
                    "page": page_no,
                    "bbox": [round(x, 3) for x in box],
                    "source_ids": [d.get("id") for d in drawings],
                    "confidence": 0.62,
                })
    return artifacts


def _section_label(line: dict[str, Any], semantic_type: str | None) -> str:
    text = line["text"].strip()
    if semantic_type == "SPEAKING_SET":
        m = SET_RE.match(text)
        if m:
            return f"Speaking Set {m.group(1)}"
    return text[:100]


def propose_structure(layout: dict[str, Any], *, filename: str = "", document_role: str = "") -> dict[str, Any]:
    lines = flatten_lines(layout)
    digest = str(layout.get("document_sha256") or "")
    if not lines:
        return {
            "schema_version": SCHEMA_VERSION,
            "document_sha256": digest,
            "filename": filename,
            "sections": [],
            "warnings": ["no_text_lines"],
        }

    starts = detect_section_starts(lines)
    if not starts:
        starts = [0]

    sections: list[dict[str, Any]] = []
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        line = lines[start]
        semantic_type = _explicit_section_type(line["text"]) or "UNKNOWN"
        sid = _stable("section", digest, line["id"], semantic_type)
        task_starts = detect_task_starts(lines, start, end)
        tasks: list[dict[str, Any]] = []

        for tpos, tstart in enumerate(task_starts):
            tend = task_starts[tpos + 1] if tpos + 1 < len(task_starts) else end
            heading = lines[tstart]
            tid = _stable("task", sid, heading["id"], _task_number(heading["text"]))
            parts = _part_nodes(lines, tstart, tend, tid)
            text = "\n".join(x["text"] for x in lines[tstart:tend])
            artifacts = _artifact_nodes(layout, lines, tstart, tend, tid)
            kind = infer_task_kind(text, has_parts=bool(parts))
            item_range = _item_range(lines, tstart, tend)
            task = {
                "id": tid,
                "label": _task_label(heading["text"]),
                "number": _task_number(heading["text"]),
                "kind": kind,
                "page_start": heading["page"],
                "page_end": lines[tend - 1]["page"],
                "anchor": {"page": heading["page"], "line_id": heading["id"], "text": heading["text"]},
                "parts": parts,
                "artifacts": artifacts,
                "confidence": 0.97,
                "proposal_source": "LAYOUT_RULES",
            }
            if item_range:
                task["item_range"] = item_range
            tasks.append(task)

        # Listening scripts and answer/criteria assets often contain no explicit "Task N" headings.
        # Preserve a low-confidence semantic node rather than fabricating numbered tasks.
        if not tasks and semantic_type in {"TRANSCRIPTION", "ANSWERS", "CRITERIA", "METHODOLOGY"}:
            label = {
                "TRANSCRIPTION": "Transcript segment",
                "ANSWERS": "Answer group",
                "CRITERIA": "Criterion group",
                "METHODOLOGY": "Methodology block",
            }[semantic_type]
            kind = {
                "TRANSCRIPTION": "TRANSCRIPT_SEGMENT",
                "ANSWERS": "ANSWER_GROUP",
                "CRITERIA": "CRITERION_GROUP",
                "METHODOLOGY": "OTHER",
            }[semantic_type]
            tasks.append({
                "id": _stable("task", sid, label),
                "label": label,
                "number": "",
                "kind": kind,
                "page_start": line["page"],
                "page_end": lines[end - 1]["page"],
                "anchor": {"page": line["page"], "line_id": line["id"], "text": line["text"]},
                "parts": [],
                "artifacts": _artifact_nodes(layout, lines, start, end, sid),
                "confidence": 0.68,
                "proposal_source": "LAYOUT_RULES",
            })

        sections.append({
            "id": sid,
            "label": _section_label(line, semantic_type),
            "semantic_type": semantic_type,
            "page_start": line["page"],
            "page_end": lines[end - 1]["page"],
            "anchor": {"page": line["page"], "line_id": line["id"], "text": line["text"]},
            "tasks": tasks,
            "confidence": 0.98 if semantic_type != "UNKNOWN" else 0.58,
            "proposal_source": "LAYOUT_RULES",
        })

    warnings: list[str] = []
    if all(not s["tasks"] for s in sections):
        warnings.append("no_explicit_tasks")
    return {
        "schema_version": SCHEMA_VERSION,
        "document_sha256": digest,
        "filename": filename,
        "document_role": document_role,
        "sections": sections,
        "warnings": warnings,
    }


def flatten_tasks(proposal: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for section in proposal.get("sections", []):
        for task in section.get("tasks", []):
            out.append({
                **task,
                "section_id": section.get("id"),
                "section_label": section.get("label"),
            })
    return out
