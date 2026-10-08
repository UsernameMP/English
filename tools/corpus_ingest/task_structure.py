from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Any

SCHEMA_VERSION = "structure-proposal.v3"

TASK_RE = re.compile(
    r"^\s*(?:task|problem|question|exercise|задача|задание|вопрос)\b\s*"
    r"(?:№\s*)?([0-9]{1,3}|[A-ZА-Я])\b[\s.):-]*(.*)$",
    re.I,
)
TASK_OCCURRENCE_RE = re.compile(
    r"(?:^|\s)(?:task|problem|question|exercise|задача|задание|вопрос)\b\s*"
    r"(?:№\s*)?([0-9]{1,3}|[A-ZА-Я])\b",
    re.I,
)
PART_RE = re.compile(
    r"^\s*(?:part|часть)\b\s*(?:№\s*)?([0-9]{1,3}|[A-ZА-Я])\b[\s.):-]*(.*)$",
    re.I,
)
SUBPART_RE = re.compile(
    r"^\s*(?:\(([a-zа-я])\)|([a-zа-я])[.)]|\((i{1,3}|iv|v|vi{0,3}|ix|x)\))\s+\S",
    re.I,
)
DECIMAL_TASK_RE = re.compile(r"^\s*([0-9]{1,3}\.[0-9]{1,3})\.?(?:\s+|$)")
GROUP_SECTION_RE = re.compile(r"^\s*(?:часть|раздел|part|section)\s+([0-9IVX]+)\s*[.:]?\s*$", re.I)
ANSWER_QUESTION_RE = re.compile(r"(?:ответ\s+на\s+вопрос|answer\s+to\s+question)\s*(?:№\s*)?([0-9]{1,3}(?:\.[0-9]{1,3})?)", re.I)
ITEM_RE = re.compile(r"^\s*([0-9]{1,3})(?:[.)])?\s+\S")
RANGE_RE = re.compile(
    r"\b(?:questions?|items?|gaps?|sentences?)\s*(?:№\s*)?"
    r"([0-9]{1,3})\s*[-–—]\s*([0-9]{1,3})\b",
    re.I,
)
SET_RE = re.compile(r"^\s*(?:speaking\s+)?set\s*([0-9]{1,3}|[A-Z])\b", re.I)

SECTION_PATTERNS = [
    ("LISTENING", re.compile(r"^\s*listening\b", re.I)),
    ("READING", re.compile(r"^\s*reading\b", re.I)),
    ("USE_OF_ENGLISH", re.compile(r"^\s*use\s+of\s+english\b", re.I)),
    ("SPEAKING_SET", re.compile(r"^\s*(?:speaking\s+)?set\s*[0-9A-Z]+\b", re.I)),
    ("SPEAKING", re.compile(r"^\s*speaking\b", re.I)),
    ("TRANSCRIPTION", re.compile(r"^\s*(?:transcription|transcript|tapescript)\b", re.I)),
    ("CRITERIA", re.compile(r"^\s*(?:criteria\b|критерии\b)", re.I)),
    ("METHODOLOGY", re.compile(r"^\s*методическ(?:ие|ая)\s+(?:рекомендации|рекомендация)\b", re.I)),
    ("WRITING", re.compile(r"^\s*writing\b", re.I)),
    ("ANSWERS", re.compile(r"^\s*(?:(?:listening|reading|use\s+of\s+english)\s+)?answers?\s*$", re.I)),
]

KIND_RULES = [
    ("SELECT_MULTIPLE", re.compile(r"choose\s+(?:all|two|three|several|multiple).*?(?:correct|true)|select\s+(?:all|two|three|several|multiple).*?(?:correct|true)|выберите\s+(?:все|несколько).*?(?:правильн|верн)|укажите\s+все\s+верн", re.I | re.S)),
    ("TRUE_FALSE_NOT_STATED", re.compile(r"true\s*\([^)]*\).*false\s*\([^)]*\).*not\s+stated|true.*false.*not\s+stated", re.I | re.S)),
    ("TRUE_FALSE", re.compile(r"\btrue\b.*\bfalse\b", re.I | re.S)),
    ("FORM_FILL", re.compile(r"complete\s+the\s+form|fill\s+in\s+the\s+form", re.I)),
    ("TABLE_GAP_FILL", re.compile(r"complete\s+the\s+table|fill\s+in\s+the\s+table|заполните\s+таблиц", re.I)),
    ("KEY_WORD_TRANSFORMATION", re.compile(r"key\s+word|complete.*second\s+sentence.*meaning|second\s+sentence.*similar\s+meaning", re.I | re.S)),
    ("WORD_FORMATION", re.compile(r"word\s+formation|form\s+(?:a|the)\s+word|use\s+the\s+word\s+given|word\s+given\s+in\s+capitals", re.I)),
    ("IDIOM", re.compile(r"\bidioms?\b", re.I)),
    ("MATCHING", re.compile(r"\bmatch\b|choose\s+the\s+correct\s+paragraph|which\s+paragraph|choose\s+from\s+the\s+paragraphs|установите\s+соответств|соотнесите", re.I)),
    ("ORDERING", re.compile(r"put.*(?:correct|right)\s+order|arrange.*order|расположите.*порядк|установите\s+последовательност", re.I | re.S)),
    ("MULTIPLE_CHOICE_CLOZE", re.compile(
        r"(?:which|decide\s+which)\s+answer.*(?:fits?|best\s+fits?)\s+each\s+gap|"
        r"decide\s+which\s+answer.*best\s+fits.*gap",
        re.I | re.S,
    )),
    ("OPEN_CLOZE", re.compile(
        r"think\s+of\s+the\s+word\s+which\s+best\s+fits\s+each\s+gap|"
        r"(?:one|two)\s+word(?:s)?\s+for\s+each\s+(?:answer|gap)|one\s+word\s+per\s+gap",
        re.I,
    )),
    ("SELECT_ONE", re.compile(
        r"choose\s+the\s+correct\s+answer|choose\s+(?:a|one)\s+(?:correct\s+)?(?:option|answer)|"
        r"choose\s+[A-DА-Д](?:\s*,\s*[A-DА-Д]){1,3}.*(?:answer|question)|"
        r"choose\s+the\s+answer\s*\([A-DА-Д]|выберите\s+(?:один\s+)?правильн(?:ый|ого)\s+(?:вариант|ответ)|укажите\s+один\s+верн",
        re.I | re.S,
    )),
    ("OPEN_SHORT", re.compile(r"answer\s+the\s+following\s+questions|give\s+(?:a\s+)?short\s+answer|ответьте\s+на\s+вопрос|дайте\s+кратк", re.I)),
    ("GAP_FILL", re.compile(
        r"complete\s+(?:the\s+)?(?:sentences?|text)|fill\s+(?:in\s+)?(?:the\s+)?gaps?|"
        r"missing\s+information",
        re.I,
    )),
    ("EXTENDED_RESPONSE", re.compile(
        r"write\s+(?:your\s+)?(?:essay|article|letter|report|story|review)|"
        r"write\s+[0-9]+\s*[-–]\s*[0-9]+\s+words|"
        r"\([0-9]+\s*[-–]\s*[0-9]+\s+words\)",
        re.I,
    )),
    ("PROOF", re.compile(r"\bprove\b|докаж", re.I)),
    ("PROGRAMMING", re.compile(r"write\s+(?:a\s+)?program|\balgorithm\b|напишите\s+программ|программ|алгоритм", re.I)),
    ("ORAL_RESPONSE", re.compile(r"\bmonologue\b|\bdialogue\b|\bspeak\b|talk\s+about|устн|монолог|диалог", re.I)),
    ("NUMERIC_RESPONSE", re.compile(r"\bcalculate\b|\bcompute\b|\bfind\s+(?:the\s+)?(?:value|number)|вычисл|найдите\s+(?:значение|число)", re.I)),
]


def _stable(prefix: str, *parts: object) -> str:
    raw = "|".join(str(x).strip().lower() for x in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:20]}"


def _bbox_area(box: list[float] | tuple[float, ...] | None) -> float:
    if not box or len(box) != 4:
        return 0.0
    return max(0.0, float(box[2]) - float(box[0])) * max(0.0, float(box[3]) - float(box[1]))


def _bbox_iou(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b or len(a) != 4 or len(b) != 4:
        return 0.0
    x0, y0 = max(float(a[0]), float(b[0])), max(float(a[1]), float(b[1]))
    x1, y1 = min(float(a[2]), float(b[2])), min(float(a[3]), float(b[3]))
    inter = max(0.0, x1 - x0) * max(0.0, y1 - y0)
    union = _bbox_area(a) + _bbox_area(b) - inter
    return inter / union if union else 0.0


def infer_document_role(filename: str, explicit: str = "") -> str:
    if explicit:
        return explicit
    name = (filename or "").rsplit("/", 1)[-1].lower()
    if name.startswith(("script-", "transcript-", "tapescript-")):
        return "LISTENING_SCRIPT"
    if name.startswith(("ans-", "answer-", "answers-", "solutions-")):
        return "ANSWER_KEY"
    if name.startswith("criteria-"):
        return "CRITERIA"
    if name.startswith(("tasks-", "task-")):
        return "TASK_SET"
    return ""


def flatten_lines(layout: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten canonical layout without discarding block provenance.

    Lines remain the segmentation primitive, but every line keeps its source
    block geometry/read order so downstream reconstruction can distinguish a
    task marker from the actual statement and preserve two-dimensional context.
    """
    lines: list[dict[str, Any]] = []
    for page in layout.get("pages", []):
        page_no = int(page.get("page_number") or 1)
        page_h = float(page.get("height") or 0)
        page_w = float(page.get("width") or 0)
        for block in page.get("blocks", []):
            block_id = block.get("id") or _stable("block", page_no, block.get("bbox"), block.get("text"))
            block_bbox = block.get("bbox") or [0, 0, 0, 0]
            block_order = int(block.get("reading_order") or 0)
            for line in block.get("lines", []):
                text = str(line.get("text") or "").strip()
                if not text:
                    continue
                spans = line.get("spans") or []
                sizes = [float(s.get("size") or 0) for s in spans if float(s.get("size") or 0) > 0]
                flags = [int(s.get("flags") or 0) for s in spans]
                fonts = [str(s.get("font") or "") for s in spans if str(s.get("font") or "")]
                lines.append({
                    "id": line.get("id") or _stable("line", page_no, line.get("bbox"), text),
                    "text": text,
                    "page": page_no,
                    "bbox": line.get("bbox") or [0, 0, 0, 0],
                    "font_size": max(sizes) if sizes else 0.0,
                    "boldish": any(f & 16 for f in flags),
                    "fonts": fonts,
                    "reading_order": int(line.get("reading_order") or block_order),
                    "block_id": block_id,
                    "block_bbox": block_bbox,
                    "block_reading_order": block_order,
                    "page_height": page_h,
                    "page_width": page_w,
                })
    # Keep canonical extractor reading order first. y/x is only a deterministic
    # tie breaker and no longer destroys column order supplied by the PDF.
    lines.sort(key=lambda x: (
        x["page"],
        int(x.get("reading_order") or 0),
        round(float(x["bbox"][1]), 2),
        float(x["bbox"][0]),
    ))
    return lines

def _normalize_instruction_text(text: str) -> str:
    value = str(text or "")
    # PDF extractors commonly keep end-of-line hyphenation: "an-\nswer".
    # Join only alphabetic fragments, then normalize whitespace.
    value = re.sub(r"([A-Za-zА-Яа-яЁё])-\s*\n\s*([A-Za-zА-Яа-яЁё])", r"\1\2", value)
    return re.sub(r"\s+", " ", value).strip()


OPTION_LINE_RE = re.compile(
    r"^\\s*(?:[A-HА-З][.)]|\\([A-HА-З]\\)|[0-9]{1,2}[.)])\\s+\\S",
    re.I,
)
CAPTION_RE = re.compile(
    r"^\\s*(?:рис\\.?|рисунок|figure|fig\\.?|table|таблица|map|карта|graph|chart|график|diagram|схема)\\b",
    re.I,
)
INSTRUCTION_RE = re.compile(
    r"\\b(?:choose|select|match|complete|fill|answer|write|read|listen|calculate|compute|find|prove|"
    r"выберите|укажите|соотнесите|установите|заполните|ответьте|напишите|прочитайте|вычислите|найдите|докажите|"
    r"расположите|определите|рассмотрите)\\b",
    re.I,
)
DEPENDENCY_RE = re.compile(
    r"\\b(?:previous|preceding|above|earlier|using\\s+your\\s+answer|"
    r"предыдущ|выше|полученн|используя\\s+ответ)\\b",
    re.I,
)
FORMULA_SIGNAL_RE = re.compile(r"[=<>±×÷√∑∫∞≈≠≤≥]|(?:\\b[a-zA-Z]\\s*[²³^]|\\d+\\s*/\\s*\\d+)")
CODE_SIGNAL_RE = re.compile(r"\\b(?:for|while|if|else|return|def|class|print|input|int|float|bool|var|let|const)\\b|[{};]", re.I)


def _union_boxes(boxes: list[list[float]]) -> list[float]:
    usable = [b for b in boxes if b and len(b) == 4]
    if not usable:
        return [0.0, 0.0, 0.0, 0.0]
    return [
        round(min(float(b[0]) for b in usable), 3),
        round(min(float(b[1]) for b in usable), 3),
        round(max(float(b[2]) for b in usable), 3),
        round(max(float(b[3]) for b in usable), 3),
    ]


def _horizontal_overlap_ratio(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != 4 or len(b) != 4:
        return 0.0
    inter = max(0.0, min(float(a[2]), float(b[2])) - max(float(a[0]), float(b[0])))
    denom = max(1.0, min(float(a[2]) - float(a[0]), float(b[2]) - float(b[0])))
    return min(1.0, inter / denom)


def _vertical_gap(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != 4 or len(b) != 4:
        return 10_000.0
    if float(a[3]) < float(b[1]):
        return float(b[1]) - float(a[3])
    if float(b[3]) < float(a[1]):
        return float(a[1]) - float(b[3])
    return 0.0


def _line_role(line: dict[str, Any], *, is_marker: bool = False) -> tuple[str, float, str]:
    text = str(line.get("text") or "").strip()
    if is_marker:
        return "TASK_MARKER", 0.99, "explicit_task_marker"
    page_h = float(line.get("page_height") or 0)
    if page_h and float((line.get("bbox") or [0, 0, 0, 0])[1]) >= page_h * 0.94:
        return "FOOTNOTE", 0.72, "bottom_margin"
    if CAPTION_RE.match(text):
        return "CAPTION", 0.92, "caption_prefix"
    if OPTION_LINE_RE.match(text):
        return "OPTION_LIST", 0.90, "option_marker"
    fonts = " ".join(line.get("fonts") or []).lower()
    if ("courier" in fonts or "mono" in fonts) and CODE_SIGNAL_RE.search(text):
        return "CODE_BLOCK", 0.88, "monospace_code_signal"
    math_hits = len(FORMULA_SIGNAL_RE.findall(text))
    if math_hits >= 2 or (math_hits >= 1 and len(text) <= 90):
        return "FORMULA_TEXT", 0.84, "formula_symbols"
    if INSTRUCTION_RE.search(text):
        return "INSTRUCTION", 0.88, "instruction_verb"
    if len(text) <= 2:
        return "UNKNOWN", 0.45, "too_short"
    return "BODY_TEXT", 0.80, "default_body"


def _task_body(
    lines: list[dict[str, Any]],
    start: int,
    end: int,
    task_id: str,
    repeated_headers: set[str] | None = None,
) -> dict[str, Any]:
    repeated_headers = repeated_headers or set()
    blocks: list[dict[str, Any]] = []
    owned_lines: list[dict[str, Any]] = []
    for idx in range(start, end):
        line = lines[idx]
        if idx != start and _norm_header(line.get("text") or "") in repeated_headers:
            continue
        role, confidence, reason = _line_role(line, is_marker=idx == start)
        row = {
            "id": _stable("task_block", task_id, line.get("id")),
            "source_block_id": line.get("block_id"),
            "line_ids": [line.get("id")],
            "page": int(line.get("page") or 1),
            "bbox": [round(float(x), 3) for x in (line.get("bbox") or [0, 0, 0, 0])],
            "reading_order": int(line.get("reading_order") or 0),
            "text": str(line.get("text") or ""),
            "role": role,
            "role_confidence": confidence,
            "role_reason": reason,
            "source_index": idx,
        }
        blocks.append(row)
        if role not in {"TASK_MARKER", "FOOTNOTE"}:
            owned_lines.append(line)

    by_page: dict[int, list[list[float]]] = {}
    for line in owned_lines:
        by_page.setdefault(int(line["page"]), []).append(line.get("bbox") or [0, 0, 0, 0])
    spans = [
        {"page": page, "bbox": _union_boxes(boxes)}
        for page, boxes in sorted(by_page.items())
    ]
    body_text = "\\n".join(
        b["text"] for b in blocks if b["role"] not in {"TASK_MARKER", "FOOTNOTE"}
    ).strip()

    reasons = ["explicit_task_marker"]
    confidence = 0.97
    if not body_text:
        confidence = 0.42
        reasons.append("empty_body")
    if len(spans) > 1:
        confidence = min(confidence, 0.93)
        reasons.append("multi_page_body")

    # Multiple narrow x-clusters on one page are a useful warning for columns.
    for page, page_blocks in _group_by(blocks, "page").items():
        width = max((float(lines[b["source_index"]].get("page_width") or 0) for b in page_blocks), default=0.0)
        centers = [
            (float(b["bbox"][0]) + float(b["bbox"][2])) / 2
            for b in page_blocks
            if width and (float(b["bbox"][2]) - float(b["bbox"][0])) < width * 0.72
        ]
        if centers and min(centers) < width * 0.42 and max(centers) > width * 0.58:
            confidence = min(confidence, 0.82)
            reasons.append(f"multi_column_page:{page}")

    role_conf = min((float(b["role_confidence"]) for b in blocks if b["role"] != "TASK_MARKER"), default=0.5)
    return {
        "body_text": body_text,
        "body_blocks": blocks,
        "body_spans": spans,
        "boundary_confidence": round(confidence, 3),
        "boundary_reasons": sorted(dict.fromkeys(reasons)),
        "block_role_confidence": round(role_conf, 3),
    }


def _group_by(rows: list[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]:
    out: dict[Any, list[dict[str, Any]]] = {}
    for row in rows:
        out.setdefault(row.get(key), []).append(row)
    return out


def infer_task_kind(text: str, *, has_parts: bool = False) -> str:
    if has_parts:
        return "COMPOSITE"
    normalized = _normalize_instruction_text(text)
    for kind, pattern in KIND_RULES:
        if pattern.search(normalized):
            return kind
    return "UNKNOWN"


def _explicit_section_type(text: str) -> str | None:
    stripped = text.strip()
    if GROUP_SECTION_RE.match(stripped):
        return "PART_GROUP"
    if re.match(r"^writing\b", stripped, re.I) and re.search(r"критери|criteria|rubric", stripped, re.I):
        # "WRITING – Критерии оценивания" is a real rubric heading.
        # "Writing – максимальное количество баллов ... оценивается по критериям"
        # is explanatory prose inside an existing rubric and must not split a section.
        if re.search(r"максимальн|maximum|оценива|evaluat|\bбалл|\bpoints?\b", stripped, re.I):
            return "WRITING"
        return "CRITERIA"
    for kind, pattern in SECTION_PATTERNS:
        if pattern.search(stripped):
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


def detect_section_starts(lines: list[dict[str, Any]], document_role: str = "") -> list[int]:
    if not lines:
        return []
    if document_role == "LISTENING_SCRIPT":
        return [0]

    explicit = [(i, _explicit_section_type(line["text"])) for i, line in enumerate(lines)]
    explicit = [(i, kind) for i, kind in explicit if kind]

    if document_role == "TASK_SET":
        set_starts = [i for i, kind in explicit if kind == "SPEAKING_SET"]
        if set_starts:
            # In oral booklets "SPEAKING" is only a repeated page header; Set N is the real unit.
            return set_starts

    if document_role in {"ANSWER_KEY", "CRITERIA"}:
        out: list[int] = []
        locked_tail = False
        first_skill = next((i for i, kind in explicit if kind in {"LISTENING", "READING", "USE_OF_ENGLISH", "WRITING"}), None)
        for i, kind in explicit:
            text = lines[i]["text"].strip()
            if kind == "ANSWERS" and len(text) > 45:
                continue
            # A document-level title such as "КРИТЕРИИ И МЕТОДИКА ОЦЕНИВАНИЯ" before
            # the first skill block is metadata, not the first scoring section.
            if kind == "CRITERIA" and first_skill is not None and i < first_skill and i < 12:
                continue
            if kind == "METHODOLOGY":
                locked_tail = True
                out.append(i)
                continue
            if kind == "CRITERIA" and re.search(r"схем[аы]\s+подсчет|scheme|rubric", text, re.I):
                locked_tail = True
                out.append(i)
                continue
            if locked_tail and kind in {"LISTENING", "READING", "USE_OF_ENGLISH", "WRITING"}:
                continue
            if locked_tail and kind == "CRITERIA" and re.search(
                r"максимальн|maximum|оценива|evaluat|\bбалл|\bpoints?\b", text, re.I
            ):
                continue
            # Long rubric prose beginning "Listening – максимальное..." is not a new section.
            if kind in {"LISTENING", "READING", "USE_OF_ENGLISH", "WRITING"} and len(text) > 70:
                continue
            out.append(i)
        if out:
            return sorted(dict.fromkeys(out))

    if explicit:
        # Reject sentence-like accidental headings.
        filtered = [i for i, kind in explicit if len(lines[i]["text"].strip()) <= 100]
        if filtered:
            return sorted(dict.fromkeys(filtered))

    explicit_tasks = [
        i for i, line in enumerate(lines)
        if TASK_RE.match(line["text"]) or DECIMAL_TASK_RE.match(line["text"])
    ]
    if explicit_tasks:
        # Subject-agnostic olympiad sheets often have no named sections at all.
        # Treat the task sequence as one review section instead of promoting each
        # bold title / task heading to an arbitrary section.
        return [explicit_tasks[0]]

    sizes = sorted(x["font_size"] for x in lines if x["font_size"] > 0)
    median = sizes[len(sizes) // 2] if sizes else 0.0
    return [i for i, line in enumerate(lines) if _heading_score(line, median) >= 0.65]


def _norm_header(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _repeated_page_headers(lines: list[dict[str, Any]]) -> set[str]:
    pages_by_text: dict[str, set[int]] = {}
    for line in lines:
        height = float(line.get("page_height") or 0)
        y0 = float((line.get("bbox") or [0, 0, 0, 0])[1])
        # Repeated top-of-page strings are boilerplate, not content owned by the
        # preceding section. This is language/subject agnostic.
        if height and y0 > height * 0.18:
            continue
        key = _norm_header(line.get("text") or "")
        if len(key) < 4:
            continue
        pages_by_text.setdefault(key, set()).add(int(line["page"]))
    return {text for text, pages in pages_by_text.items() if len(pages) >= 2}


def _has_substantive_prefix_on_boundary_page(
    lines: list[dict[str, Any]],
    start: int,
    boundary: int,
    repeated_headers: set[str],
) -> bool:
    boundary_page = int(lines[boundary]["page"])
    for line in lines[start:boundary]:
        if int(line["page"]) != boundary_page:
            continue
        text = str(line.get("text") or "").strip()
        if not text:
            continue
        norm = _norm_header(text)
        if norm in repeated_headers:
            continue
        # Generic repeated oral-booklet header before "Set N".
        if re.fullmatch(r"speaking", text, re.I):
            continue
        return True
    return False


def _span_end_page(
    lines: list[dict[str, Any]],
    start: int,
    end: int,
    boundary: int | None,
    repeated_headers: set[str],
) -> int:
    if boundary is not None and boundary < len(lines):
        start_page = int(lines[start]["page"])
        boundary_page = int(lines[boundary]["page"])
        if boundary_page > start_page and not _has_substantive_prefix_on_boundary_page(
            lines, start, boundary, repeated_headers
        ):
            return boundary_page - 1
    return int(lines[end - 1]["page"])


def _writing_task_label(text: str) -> str:
    direct = re.search(
        r"write\s+(?:your\s+|an?\s+|the\s+)?(article|essay|letter|report|review|story)\b",
        text,
        re.I,
    )
    if direct:
        return direct.group(1).capitalize()
    for word, label in [
        ("articles", "Article"),
        ("article", "Article"),
        ("essay", "Essay"),
        ("letter", "Letter"),
        ("report", "Report"),
        ("review", "Review"),
        ("story", "Story"),
    ]:
        if re.search(r"\b" + word + r"\b", text, re.I):
            return label
    return "Writing task"


def detect_task_starts(lines: list[dict[str, Any]], start: int, end: int) -> list[int]:
    return [
        i for i in range(start, end)
        if TASK_RE.match(lines[i]["text"]) or DECIMAL_TASK_RE.match(lines[i]["text"])
    ]


def _task_number(text: str) -> str:
    m = TASK_RE.match(text)
    if m:
        return m.group(1)
    m = DECIMAL_TASK_RE.match(text)
    return m.group(1) if m else ""


def _task_label(text: str) -> str:
    m = TASK_RE.match(text)
    if m:
        return f"Task {m.group(1)}"
    m = DECIMAL_TASK_RE.match(text)
    if m:
        return f"Task {m.group(1)}"
    return text[:80]


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


def _subpart_nodes(lines: list[dict[str, Any]], start: int, end: int, task_id: str, base_kind: str) -> list[dict[str, Any]]:
    # Lower-case/roman subparts are common in maths/science. Do not reinterpret
    # option lists in select/matching tasks as structural parts.
    if base_kind in {"SELECT_ONE", "SELECT_MULTIPLE", "MULTIPLE_CHOICE_CLOZE", "MATCHING"}:
        return []
    candidates: list[tuple[int, str]] = []
    for i in range(start + 1, end):
        m = SUBPART_RE.match(lines[i]["text"])
        if not m:
            continue
        marker = next((x for x in m.groups() if x), "")
        candidates.append((i, marker.lower()))
    if len(candidates) < 2:
        return []
    parts: list[dict[str, Any]] = []
    for pos, (idx, marker) in enumerate(candidates):
        stop = candidates[pos + 1][0] if pos + 1 < len(candidates) else end
        text = "\n".join(x["text"] for x in lines[idx:stop])
        parts.append({
            "id": _stable("part", task_id, lines[idx]["id"], marker),
            "label": f"Part {marker}",
            "page_start": lines[idx]["page"],
            "page_end": lines[stop - 1]["page"],
            "anchor": {"page": lines[idx]["page"], "line_id": lines[idx]["id"], "text": lines[idx]["text"]},
            "kind": infer_task_kind(text),
            "confidence": 0.78,
            "proposal_source": "LAYOUT_RULES",
        })
    return parts


def response_mode_for_kind(kind: str) -> str:
    if kind in {"SELECT_ONE", "SELECT_MULTIPLE", "TRUE_FALSE", "TRUE_FALSE_NOT_STATED", "MATCHING", "ORDERING", "MULTIPLE_CHOICE_CLOZE"}:
        return "SELECT"
    if kind in {"GAP_FILL", "TABLE_GAP_FILL", "FORM_FILL", "OPEN_CLOZE", "OPEN_SHORT", "KEY_WORD_TRANSFORMATION", "WORD_FORMATION", "IDIOM"}:
        return "TEXT_SHORT"
    if kind in {"EXTENDED_RESPONSE", "PROOF", "DERIVATION"}:
        return "TEXT_LONG"
    if kind == "NUMERIC_RESPONSE":
        return "NUMBER"
    if kind == "PROGRAMMING":
        return "CODE"
    if kind == "ORAL_RESPONSE":
        return "SPEECH"
    if kind == "COMPOSITE":
        return "MIXED"
    return "UNKNOWN"


def _item_range(lines: list[dict[str, Any]], start: int, end: int) -> dict[str, int] | None:
    text = "\n".join(line["text"] for line in lines[start:end])
    explicit = RANGE_RE.search(text)
    if explicit:
        a, b = int(explicit.group(1)), int(explicit.group(2))
        if 0 <= a <= b <= 300:
            return {"start": a, "end": b, "count_observed": b - a + 1, "source": "instruction"}

    nums: list[int] = []
    for line in lines[start + 1:end]:
        m = ITEM_RE.match(line["text"])
        if m:
            nums.append(int(m.group(1)))
    if not nums:
        return None
    counts = Counter(nums)
    usable = [n for n in nums if 0 <= n <= 300 and counts[n] <= 3]
    if not usable:
        return None
    return {"start": min(usable), "end": max(usable), "count_observed": len(set(usable)), "source": "items"}


def _task_region(lines: list[dict[str, Any]], start: int, end: int) -> dict[int, tuple[float, float]]:
    """Compatibility vertical bands used only as a loose candidate gate."""
    first = lines[start]
    last = lines[end - 1]
    pages = range(first["page"], last["page"] + 1)
    out: dict[int, tuple[float, float]] = {}
    next_boundary = lines[end] if end < len(lines) else None
    for page in pages:
        same = [x for x in lines[start:end] if x["page"] == page]
        if not same:
            continue
        page_height = max(float(x.get("page_height") or 0) for x in same) or max(float(x["bbox"][3]) for x in same)
        y0 = float(first["bbox"][1]) if page == first["page"] else 0.0
        if next_boundary is not None and int(next_boundary["page"]) == page:
            y1 = max(y0 + 1.0, float(next_boundary["bbox"][1]) - 1.0)
        else:
            y1 = page_height
        out[page] = (y0, y1)
    return out


def _overlaps_vertical(box: list[float], band: tuple[float, float]) -> bool:
    if not box or len(box) != 4:
        return False
    return min(float(box[3]), band[1]) - max(float(box[1]), band[0]) > 1


def _nearby_text(lines: list[dict[str, Any]], page: int, box: list[float], max_gap: float = 72.0) -> str:
    nearby = []
    for line in lines:
        if int(line.get("page") or 0) != page:
            continue
        if _vertical_gap(line.get("bbox") or [0, 0, 0, 0], box) <= max_gap:
            nearby.append(str(line.get("text") or ""))
    return " ".join(nearby)


def _artifact_kind(raw_kind: str, task_kind: str, nearby: str, cells: int = 0) -> tuple[str, float, str]:
    text = nearby.lower()
    if raw_kind == "table":
        if task_kind in {"TRUE_FALSE", "TRUE_FALSE_NOT_STATED", "TABLE_GAP_FILL"}:
            return "RESPONSE_TABLE", 0.94, "task_kind_table"
        if task_kind == "FORM_FILL":
            return "FORM", 0.92, "form_fill_table"
        if re.search(r"word\\s*bank|слова\\s+для\\s+справ", text, re.I):
            return "WORD_BANK", 0.90, "nearby_word_bank_caption"
        if cells >= 16:
            return "GRID", 0.82, "dense_cell_grid"
        return "TABLE", 0.91, "pdf_table"
    if re.search(r"\\b(?:map|карта|картосхем|контурн)", text, re.I):
        return "MAP", 0.88, "nearby_map_caption"
    if re.search(r"\\b(?:graph|chart|plot|график|климатограмм)", text, re.I):
        return "GRAPH", 0.88, "nearby_graph_caption"
    if re.search(r"\\b(?:figure|fig\\.?|рисунок|рис\\.)", text, re.I):
        return "FIGURE", 0.87, "nearby_figure_caption"
    if raw_kind == "image":
        return "FIGURE", 0.78, "generic_image"
    return "DIAGRAM", 0.72, "vector_drawing_group"


def _artifact_binding(
    box: list[float],
    page: int,
    body_spans: list[dict[str, Any]],
    page_width: float,
) -> tuple[float, list[str]]:
    span = next((s.get("bbox") for s in body_spans if int(s.get("page") or 0) == page), None)
    if not span:
        return 0.0, ["no_task_body_on_page"]
    x_overlap = _horizontal_overlap_ratio(box, span)
    gap = _vertical_gap(box, span)
    wide = page_width and (float(box[2]) - float(box[0])) >= page_width * 0.72
    reasons = []
    score = 0.36
    if x_overlap >= 0.5:
        score += 0.34
        reasons.append("x_overlap")
    elif x_overlap >= 0.15:
        score += 0.18
        reasons.append("partial_x_overlap")
    elif wide:
        score += 0.14
        reasons.append("full_width_asset")
    if gap == 0:
        score += 0.22
        reasons.append("body_overlap")
    elif gap <= 48:
        score += 0.16
        reasons.append("near_body")
    elif gap <= 120:
        score += 0.08
        reasons.append("within_task_neighborhood")
    else:
        score -= 0.18
        reasons.append("far_from_body")
    return round(max(0.0, min(0.98, score)), 3), reasons


def _artifact_nodes(
    layout: dict[str, Any],
    lines: list[dict[str, Any]],
    start: int,
    end: int,
    task_id: str,
    task_kind: str = "UNKNOWN",
    body: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    body = body or _task_body(lines, start, end, task_id)
    regions = _task_region(lines, start, end)
    artifacts: list[dict[str, Any]] = []
    pages = {int(p.get("page_number") or 1): p for p in layout.get("pages", [])}

    def add(raw_kind: str, source: dict[str, Any], *, cells: int = 0, source_ids: list[str] | None = None):
        page_no = int(source.get("_page") or 1)
        box = source.get("bbox") or [0, 0, 0, 0]
        band = regions.get(page_no)
        if not band or not _overlaps_vertical(box, band):
            return
        page_width = float((pages.get(page_no) or {}).get("width") or 0)
        binding_conf, binding_reasons = _artifact_binding(box, page_no, body.get("body_spans") or [], page_width)
        # Require two-dimensional evidence. Wide assets are allowed because many
        # maps/tables deliberately span both columns.
        if binding_conf < 0.42:
            return
        nearby = _nearby_text(lines, page_no, box)
        kind, type_conf, type_reason = _artifact_kind(raw_kind, task_kind, nearby, cells)
        caption = next(
            (str(line.get("text") or "") for line in lines
             if int(line.get("page") or 0) == page_no
             and CAPTION_RE.match(str(line.get("text") or ""))
             and _vertical_gap(line.get("bbox") or [0, 0, 0, 0], box) <= 72),
            "",
        )
        row = {
            "id": _stable("artifact", task_id, source.get("id") or box),
            "kind": kind,
            "page": page_no,
            "bbox": [round(float(x), 3) for x in box],
            "source_id": source.get("id"),
            "confidence": round(min(type_conf, binding_conf), 3),
            "type_confidence": type_conf,
            "type_reason": type_reason,
            "asset_binding_confidence": binding_conf,
            "binding_reasons": binding_reasons,
            "caption_text": caption,
        }
        if source_ids:
            row["source_ids"] = source_ids
        artifacts.append(row)

    for page_no, page in pages.items():
        for table in page.get("tables", []):
            add("table", {**table, "_page": page_no}, cells=len(table.get("cells") or []))
        for image in page.get("images", []):
            add("image", {**image, "_page": page_no})
        drawings = [
            d for d in page.get("drawings", [])
            if regions.get(page_no) and _overlaps_vertical(d.get("bbox") or [0, 0, 0, 0], regions[page_no])
        ]
        if len(drawings) >= 4:
            box = _union_boxes([d.get("bbox") or [0, 0, 0, 0] for d in drawings])
            if _bbox_area(box) > 100 and not any(
                a["page"] == page_no and a["kind"] in {"TABLE", "GRID", "RESPONSE_TABLE", "FORM"} and _bbox_iou(a.get("bbox"), box) >= 0.70
                for a in artifacts
            ):
                add(
                    "drawing",
                    {"id": _stable("drawing_group", task_id, page_no, len(drawings)), "bbox": box, "_page": page_no},
                    source_ids=[str(d.get("id") or "") for d in drawings],
                )

    # Formula/code blocks are semantic artifacts even when the PDF stores them as text.
    for block in body.get("body_blocks") or []:
        if block.get("role") not in {"FORMULA_TEXT", "CODE_BLOCK"}:
            continue
        kind = "FORMULA" if block["role"] == "FORMULA_TEXT" else "CODE_BLOCK"
        artifacts.append({
            "id": _stable("artifact", task_id, block["id"], kind),
            "kind": kind,
            "page": block["page"],
            "bbox": block["bbox"],
            "source_id": block.get("source_block_id"),
            "confidence": block.get("role_confidence", 0.8),
            "type_confidence": block.get("role_confidence", 0.8),
            "type_reason": block.get("role_reason"),
            "asset_binding_confidence": 0.99,
            "binding_reasons": ["owned_text_block"],
            "caption_text": "",
        })

    # Same canonical source should not appear twice in one task.
    dedup: dict[tuple, dict[str, Any]] = {}
    for artifact in artifacts:
        key = (artifact.get("page"), artifact.get("source_id"), tuple(artifact.get("bbox") or []), artifact.get("kind"))
        prior = dedup.get(key)
        if prior is None or float(artifact.get("confidence") or 0) > float(prior.get("confidence") or 0):
            dedup[key] = artifact
    return list(dedup.values())


def _composition_graph(
    task_id: str,
    parts: list[dict[str, Any]],
    body: dict[str, Any],
    artifacts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if len(parts) < 2:
        return None
    group_id = _stable("task_group", task_id)
    nodes: list[dict[str, Any]] = [{"id": group_id, "kind": "TASK_GROUP", "task_id": task_id}]
    edges: list[dict[str, Any]] = []

    for part in parts:
        edges.append({"from": group_id, "type": "OWNS_PART", "to": part["id"]})

    first_anchor = str(parts[0].get("anchor", {}).get("line_id") or "")
    first_index = next(
        (int(b["source_index"]) for b in body.get("body_blocks") or [] if first_anchor in (b.get("line_ids") or [])),
        None,
    )
    shared_blocks = [
        b["id"] for b in body.get("body_blocks") or []
        if b.get("role") not in {"TASK_MARKER", "FOOTNOTE"}
        and (first_index is None or int(b.get("source_index") or 0) < first_index)
    ]
    shared_artifacts = [a["id"] for a in artifacts]
    if shared_blocks or shared_artifacts:
        stimulus_id = _stable("shared_stimulus", task_id, *shared_blocks, *shared_artifacts)
        nodes.append({
            "id": stimulus_id,
            "kind": "SHARED_STIMULUS",
            "block_ids": shared_blocks,
            "artifact_ids": shared_artifacts,
            "confidence": 0.86 if shared_blocks else 0.78,
        })
        for part in parts:
            edges.append({"from": part["id"], "type": "USES_STIMULUS", "to": stimulus_id})
        for artifact_id in shared_artifacts:
            edges.append({"from": stimulus_id, "type": "USES_ARTIFACT", "to": artifact_id})

    body_text = str(body.get("body_text") or "")
    if DEPENDENCY_RE.search(body_text):
        for previous, current in zip(parts, parts[1:]):
            edges.append({"from": current["id"], "type": "DEPENDS_ON", "to": previous["id"]})

    return {"nodes": nodes, "edges": edges, "confidence": 0.84}


def _enrich_task(
    task: dict[str, Any],
    layout: dict[str, Any],
    lines: list[dict[str, Any]],
    start: int,
    end: int,
    repeated_headers: set[str] | None = None,
) -> dict[str, Any]:
    body = _task_body(lines, start, end, task["id"], repeated_headers)
    artifacts = _artifact_nodes(
        layout, lines, start, end, task["id"],
        task_kind=str(task.get("kind") or "UNKNOWN"),
        body=body,
    )
    task.update(body)
    task["artifacts"] = artifacts
    composition = _composition_graph(task["id"], task.get("parts") or [], body, artifacts)
    if composition:
        task["composition"] = composition

    asset_conf = min((float(a.get("asset_binding_confidence") or 0) for a in artifacts), default=1.0)
    composition_conf = float(composition.get("confidence") or 1.0) if composition else 1.0
    reconstruction = min(
        float(body.get("boundary_confidence") or 0),
        float(body.get("block_role_confidence") or 0),
        asset_conf,
        composition_conf,
    )
    task["reconstruction_confidence"] = round(reconstruction, 3)
    task["review_required"] = reconstruction < 0.78 or any(
        float(a.get("asset_binding_confidence") or 0) < 0.65 for a in artifacts
    )
    task["reconstruction_reasons"] = {
        "boundary": body.get("boundary_reasons") or [],
        "low_confidence_artifacts": [
            a["id"] for a in artifacts if float(a.get("asset_binding_confidence") or 0) < 0.65
        ],
    }
    return task




def _section_label(line: dict[str, Any], semantic_type: str | None) -> str:
    text = line["text"].strip()
    if semantic_type == "UNKNOWN" and (TASK_RE.match(text) or DECIMAL_TASK_RE.match(text)):
        return "Tasks"
    if semantic_type == "SPEAKING_SET":
        m = SET_RE.match(text)
        if m:
            return f"Speaking Set {m.group(1)}"
    return text[:100]


def _semantic_task(
    layout: dict[str, Any],
    lines: list[dict[str, Any]],
    start: int,
    end: int,
    sid: str,
    label: str,
    kind: str,
    confidence: float = 0.72,
) -> dict[str, Any]:
    line = lines[start]
    text = "\n".join(x["text"] for x in lines[start:end])
    resolved_kind = kind if kind != "INFER" else infer_task_kind(text)
    task = {
        "id": _stable("task", sid, label),
        "label": label,
        "number": "",
        "kind": resolved_kind,
        "response_mode": response_mode_for_kind(resolved_kind),
        "page_start": line["page"],
        "page_end": lines[end - 1]["page"],
        "anchor": {"page": line["page"], "line_id": line["id"], "text": line["text"]},
        "parts": [],
        "artifacts": [],
        "confidence": confidence,
        "proposal_source": "LAYOUT_RULES",
    }
    return _enrich_task(task, layout, lines, start, end)


def _answer_tasks(
    layout: dict[str, Any],
    lines: list[dict[str, Any]],
    start: int,
    end: int,
    sid: str,
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    tasks: list[dict[str, Any]] = []
    for i in range(start, end):
        matches = list(TASK_OCCURRENCE_RE.finditer(lines[i]["text"])) + list(ANSWER_QUESTION_RE.finditer(lines[i]["text"]))
        for m in matches:
            number = m.group(1)
            if number in seen:
                continue
            seen.add(number)
            task = {
                "id": _stable("task", sid, lines[i]["id"], number),
                "label": f"Task {number}",
                "number": number,
                "kind": "ANSWER_GROUP",
                "response_mode": "UNKNOWN",
                "page_start": lines[i]["page"],
                "page_end": lines[end - 1]["page"],
                "anchor": {"page": lines[i]["page"], "line_id": lines[i]["id"], "text": lines[i]["text"]},
                "parts": [],
                "artifacts": [],
                "confidence": 0.91,
                "proposal_source": "LAYOUT_RULES",
            }
            stop = next(
                (j for j in range(i + 1, end) if TASK_RE.match(lines[j]["text"]) or ANSWER_QUESTION_RE.search(lines[j]["text"])),
                end,
            )
            tasks.append(_enrich_task(task, layout, lines, i, stop))
    if tasks:
        return tasks
    return [_semantic_task(layout, lines, start, end, sid, "Answers", "ANSWER_GROUP", 0.76)]


def _script_structure(layout: dict[str, Any], lines: list[dict[str, Any]], digest: str, filename: str) -> dict[str, Any]:
    sid = _stable("section", digest, "transcription")
    task_starts = [i for i, line in enumerate(lines) if TASK_RE.match(line["text"])]
    tasks: list[dict[str, Any]] = []
    if task_starts:
        for pos, start in enumerate(task_starts):
            end = task_starts[pos + 1] if pos + 1 < len(task_starts) else len(lines)
            heading = lines[start]
            number = _task_number(heading["text"])
            task = {
                "id": _stable("task", sid, heading["id"], number),
                "label": f"Task {number}",
                "number": number,
                "kind": "TRANSCRIPT_SEGMENT",
                "response_mode": "NONE",
                "page_start": heading["page"],
                "page_end": lines[end - 1]["page"],
                "anchor": {"page": heading["page"], "line_id": heading["id"], "text": heading["text"]},
                "parts": [],
                "artifacts": [],
                "confidence": 0.96,
                "proposal_source": "LAYOUT_RULES",
            }
            tasks.append(_enrich_task(task, layout, lines, start, end))
    else:
        tasks.append(_semantic_task(layout, lines, 0, len(lines), sid, "Transcript segment", "TRANSCRIPT_SEGMENT", 0.82))
    section = {
        "id": sid,
        "label": "Transcription",
        "semantic_type": "TRANSCRIPTION",
        "content_role": "SCRIPT",
        "page_start": lines[0]["page"],
        "page_end": lines[-1]["page"],
        "anchor": {"page": lines[0]["page"], "line_id": lines[0]["id"], "text": lines[0]["text"]},
        "tasks": tasks,
        "confidence": 0.96,
        "proposal_source": "LAYOUT_RULES",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "document_sha256": digest,
        "filename": filename,
        "document_role": "LISTENING_SCRIPT",
        "sections": [section],
        "warnings": [],
    }


def propose_structure(layout: dict[str, Any], *, filename: str = "", document_role: str = "") -> dict[str, Any]:
    lines = flatten_lines(layout)
    digest = str(layout.get("document_sha256") or "")
    role = infer_document_role(filename, document_role)
    if not lines:
        return {
            "schema_version": SCHEMA_VERSION,
            "document_sha256": digest,
            "filename": filename,
            "document_role": role,
            "sections": [],
            "warnings": ["no_text_lines"],
        }

    if role == "LISTENING_SCRIPT":
        return _script_structure(layout, lines, digest, filename)

    starts = detect_section_starts(lines, role)
    if not starts:
        starts = [0]
    repeated_headers = _repeated_page_headers(lines)

    sections: list[dict[str, Any]] = []
    for pos, start in enumerate(starts):
        boundary = starts[pos + 1] if pos + 1 < len(starts) else None
        end = boundary if boundary is not None else len(lines)
        line = lines[start]
        section_end_page = _span_end_page(lines, start, end, boundary, repeated_headers)
        semantic_type = _explicit_section_type(line["text"]) or "UNKNOWN"
        # In answer-key documents the Writing block is normally the scoring rubric,
        # not a new learner task. Treat it as criteria even when PDF font encoding
        # makes the Cyrillic/English "criteria" suffix unreadable.
        if role in {"ANSWER_KEY", "CRITERIA"} and semantic_type == "WRITING":
            semantic_type = "CRITERIA"
        sid = _stable("section", digest, line["id"], semantic_type)
        tasks: list[dict[str, Any]] = []

        if role in {"ANSWER_KEY", "CRITERIA"}:
            if semantic_type in {"LISTENING", "READING", "USE_OF_ENGLISH", "PART_GROUP"}:
                tasks = _answer_tasks(layout, lines, start, end, sid)
            elif semantic_type == "CRITERIA":
                tasks = [_semantic_task(layout, lines, start, end, sid, "Rubric / rationale", "CRITERION_GROUP", 0.84)]
            elif semantic_type == "METHODOLOGY":
                tasks = [_semantic_task(layout, lines, start, end, sid, "Methodology block", "OTHER", 0.82)]
            elif semantic_type == "WRITING":
                tasks = [_semantic_task(layout, lines, start, end, sid, "Writing criteria", "CRITERION_GROUP", 0.82)]
        else:
            task_starts = detect_task_starts(lines, start, end)
            for tpos, tstart in enumerate(task_starts):
                task_boundary = task_starts[tpos + 1] if tpos + 1 < len(task_starts) else boundary
                tend = task_starts[tpos + 1] if tpos + 1 < len(task_starts) else end
                heading = lines[tstart]
                tid = _stable("task", sid, heading["id"], _task_number(heading["text"]))
                text = "\n".join(x["text"] for x in lines[tstart:tend])
                base_kind = infer_task_kind(text)
                parts = _part_nodes(lines, tstart, tend, tid)
                if not parts:
                    parts = _subpart_nodes(lines, tstart, tend, tid, base_kind)
                kind = "COMPOSITE" if parts else base_kind
                if semantic_type in {"SPEAKING_SET", "SPEAKING"}:
                    kind = "ORAL_RESPONSE"
                    parts = []
                item_range = None if kind == "ORAL_RESPONSE" else _item_range(lines, tstart, tend)
                task_end_page = _span_end_page(lines, tstart, tend, task_boundary, repeated_headers)
                task = {
                    "id": tid,
                    "label": _task_label(heading["text"]),
                    "number": _task_number(heading["text"]),
                    "kind": kind,
                    "response_mode": response_mode_for_kind(kind),
                    "page_start": heading["page"],
                    "page_end": task_end_page,
                    "anchor": {"page": heading["page"], "line_id": heading["id"], "text": heading["text"]},
                    "parts": parts,
                    "artifacts": [],
                    "confidence": 0.97,
                    "proposal_source": "LAYOUT_RULES",
                }
                if item_range:
                    task["item_range"] = item_range
                tasks.append(_enrich_task(task, layout, lines, tstart, tend, repeated_headers))

            if not tasks and semantic_type == "WRITING" and role == "TASK_SET":
                writing_text = "\n".join(x["text"] for x in lines[start:end])
                writing_label = _writing_task_label(writing_text)
                tasks = [_semantic_task(layout, lines, start, end, sid, writing_label, "INFER", 0.92)]
                tasks[0]["page_end"] = section_end_page
            elif not tasks and semantic_type in {"TRANSCRIPTION", "ANSWERS", "CRITERIA", "METHODOLOGY"}:
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
                tasks = [_semantic_task(layout, lines, start, end, sid, label, kind, 0.68)]

        label = _section_label(line, semantic_type)
        content_role = ""
        if role in {"ANSWER_KEY", "CRITERIA"}:
            content_role = "CRITERIA" if semantic_type in {"CRITERIA", "WRITING", "METHODOLOGY"} else "ANSWERS"

        sections.append({
            "id": sid,
            "label": label,
            "semantic_type": semantic_type,
            "content_role": content_role or None,
            "page_start": line["page"],
            "page_end": section_end_page,
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
        "document_role": role,
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
