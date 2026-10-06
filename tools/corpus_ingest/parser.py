from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import fitz

from crawler import DropboxClient, require_env, sha256_bytes, utc_now
from layout_pipeline import manifest_path as parsed_manifest_path
from layout_pipeline import parse_pdf_bytes as parse_pdf_bytes_layout

PARSER_VERSION = "0.4"
KEYWORD_TASK_RE = re.compile(
    r"^\s*(?:(?:task|problem|question|задача|задание|вопрос)\s*)"
    r"(?:№\s*)?(\d{1,3})\s*(?:[.)\]:—-]\s*)?$",
    re.I,
)
KEYWORD_TASK_PREFIX_RE = re.compile(
    r"^\s*(?:(?:task|problem|question|задача|задание|вопрос)\s*)"
    r"(?:№\s*)?(\d{1,3})\b",
    re.I,
)
BARE_TASK_RE = re.compile(r"^\s*(\d{1,2})[.)]\s+\S")
SUSPICIOUS_RE = re.compile(r"[�□]{1,}|\?{3,}")
SUPPORTED_PARSE_EXTENSIONS = {".pdf"}


@dataclass
class Line:
    page: int
    rect: fitz.Rect
    text: str


@dataclass
class Candidate:
    candidate_id: str
    number: str | None
    boundary_method: str
    boundary_confidence: float
    lines: list[Line]


def load_jsonl_bytes(data: bytes | None, key: str) -> dict[str, dict]:
    if not data:
        return {}
    out: dict[str, dict] = {}
    for raw in data.decode("utf-8").splitlines():
        if not raw.strip():
            continue
        item = json.loads(raw)
        out[str(item[key])] = item
    return out


def dump_jsonl_bytes(items: dict[str, dict], sort_key: str) -> bytes:
    rows = sorted(items.values(), key=lambda x: str(x.get(sort_key, "")))
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        for row in rows
    ).encode("utf-8")


def extension_from_path(path: str) -> str:
    return Path(path).suffix.lower()


def page_lines(page: fitz.Page) -> list[Line]:
    out: list[Line] = []
    raw = page.get_text("dict")
    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = "".join(span.get("text", "") for span in spans).strip()
            if not text:
                continue
            out.append(Line(page.number + 1, fitz.Rect(line["bbox"]), text))
    out.sort(key=lambda x: (x.page, round(x.rect.y0, 1), x.rect.x0))
    return out


def flatten_lines(doc: fitz.Document) -> list[Line]:
    out: list[Line] = []
    for page in doc:
        out.extend(page_lines(page))
    return out


def detect_task_starts(lines: list[Line]) -> tuple[list[tuple[int, str]], str, float]:
    keyword: list[tuple[int, str]] = []
    bare: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        m = KEYWORD_TASK_PREFIX_RE.match(line.text)
        if m:
            keyword.append((i, m.group(1)))
            continue
        m = BARE_TASK_RE.match(line.text)
        if m:
            bare.append((i, m.group(1)))
    if keyword:
        return keyword, "keyword_heading", 0.97
    if bare:
        return bare, "numbered_line", 0.86
    return [], "page_fragment", 0.45


def segment_document(doc: fitz.Document, digest: str) -> list[Candidate]:
    lines = flatten_lines(doc)
    if not lines:
        return []

    starts, method, confidence = detect_task_starts(lines)
    candidates: list[Candidate] = []

    if starts:
        for pos, (start, number) in enumerate(starts):
            end = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
            selected = lines[start:end]
            if not selected:
                continue
            candidate_id = f"{digest[:16]}-t{pos + 1:04d}"
            candidates.append(
                Candidate(candidate_id, number, method, confidence, selected)
            )
        return candidates

    by_page: dict[int, list[Line]] = defaultdict(list)
    for line in lines:
        by_page[line.page].append(line)
    for pos, page_num in enumerate(sorted(by_page), start=1):
        candidates.append(
            Candidate(
                f"{digest[:16]}-p{page_num:04d}",
                None,
                "page_fragment",
                0.45,
                by_page[page_num],
            )
        )
    return candidates


def union_rect(lines: list[Line]) -> fitz.Rect:
    rect = fitz.Rect(lines[0].rect)
    for line in lines[1:]:
        rect |= line.rect
    return rect


def rect_to_list(rect: fitz.Rect) -> list[float]:
    return [round(rect.x0, 2), round(rect.y0, 2), round(rect.x1, 2), round(rect.y1, 2)]


def candidate_page_spans(candidate: Candidate) -> list[dict]:
    by_page: dict[int, list[Line]] = defaultdict(list)
    for line in candidate.lines:
        by_page[line.page].append(line)
    spans = []
    for page_num in sorted(by_page):
        rect = union_rect(by_page[page_num])
        spans.append({
            "page": page_num,
            "bbox": rect_to_list(rect),
            "line_count": len(by_page[page_num]),
        })
    return spans


def page_visual_rects(page: fitz.Page) -> list[fitz.Rect]:
    rects: list[fitz.Rect] = []
    for info in page.get_image_info(xrefs=True):
        bbox = info.get("bbox")
        if bbox:
            rects.append(fitz.Rect(bbox))
    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if rect and rect.get_area() > 9:
            rects.append(fitz.Rect(rect))
    return rects


def relevant_visuals(page: fitz.Page, text_rect: fitz.Rect) -> list[fitz.Rect]:
    band = fitz.Rect(
        page.rect.x0,
        max(page.rect.y0, text_rect.y0 - 80),
        page.rect.x1,
        min(page.rect.y1, text_rect.y1 + 120),
    )
    out = []
    for rect in page_visual_rects(page):
        if (band & rect).get_area() > 1:
            out.append(rect)
    return out


def render_visual_crop(page: fitz.Page, text_rect: fitz.Rect, visuals: list[fitz.Rect]) -> bytes:
    crop = fitz.Rect(text_rect)
    for rect in visuals:
        crop |= rect
    crop = fitz.Rect(
        max(page.rect.x0, crop.x0 - 10),
        max(page.rect.y0, crop.y0 - 10),
        min(page.rect.x1, crop.x1 + 10),
        min(page.rect.y1, crop.y1 + 10),
    )
    pix = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), clip=crop, alpha=False)
    return pix.tobytes("png")


def text_quality(text: str) -> dict:
    stripped = text.strip()
    suspicious = bool(SUSPICIOUS_RE.search(stripped))
    return {
        "chars": len(stripped),
        "suspicious_glyphs": suspicious,
        "looks_empty": len(stripped) < 8,
    }


def candidate_payload(
    candidate: Candidate,
    digest: str,
    occurrences: list[dict],
    assets: list[dict],
) -> dict:
    text = "\n".join(line.text for line in candidate.lines).strip()
    spans = candidate_page_spans(candidate)
    return {
        "schema_version": "0.2",
        "task_id": candidate.candidate_id,
        "status": "queued_extract",
        "candidate_type": "task" if candidate.number is not None else "page_fragment",
        "task_number_hint": candidate.number,
        "statement_raw": text,
        "statement_structured": [
            {"type": "text", "text": line.text, "page": line.page, "bbox": rect_to_list(line.rect)}
            for line in candidate.lines
        ],
        "page_spans": spans,
        "assets": assets,
        "provenance": {
            "document_sha256": digest,
            "source_occurrences": [
                {
                    "source_id": x.get("source_id", ""),
                    "url": x.get("url", ""),
                    "discovered_from": x.get("discovered_from", ""),
                    "dropbox_path": x.get("dropbox_path", ""),
                }
                for x in occurrences
            ],
        },
        "parser": {
            "version": PARSER_VERSION,
            "boundary_method": candidate.boundary_method,
            "boundary_confidence": candidate.boundary_confidence,
            "text_quality": text_quality(text),
            "requires_model_verification": True,
            "canonical": False,
        },
    }


def parser_state_path(root: str) -> str:
    return f"{root.rstrip('/')}/state/parse_state.jsonl"


def candidate_manifest_path(root: str, digest: str) -> str:
    # Compatibility name: v0.4 stores the canonical parsed-document manifest.
    return parsed_manifest_path(root, digest)


def candidate_asset_path(root: str, digest: str, candidate_id: str, page: int) -> str:
    return f"{root.rstrip('/')}/candidate/{digest[:2]}/{digest}/assets/{candidate_id}-p{page:04d}.png"


def group_documents(crawl_state: dict[str, dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in crawl_state.values():
        digest = str(row.get("sha256") or "")
        if not digest:
            continue
        if row.get("status") not in {"DOWNLOADED", "DUPLICATE"}:
            continue
        grouped[digest].append(row)
    return dict(grouped)


def document_text_stats(doc: fitz.Document) -> dict:
    chars_by_page = [len(page.get_text("text").strip()) for page in doc]
    total = sum(chars_by_page)
    nonempty = sum(1 for x in chars_by_page if x >= 20)
    return {
        "pages": len(doc),
        "total_chars": total,
        "nonempty_pages": nonempty,
        "chars_by_page": chars_by_page,
        "needs_ocr": total < max(80, len(doc) * 20),
    }


def parse_pdf_bytes(
    data: bytes,
    digest: str,
    occurrences: list[dict],
    dbx: DropboxClient,
) -> tuple[dict, int]:
    if sha256_bytes(data) != digest:
        raise ValueError("raw_sha256_mismatch")

    doc = fitz.open(stream=data, filetype="pdf")
    stats = document_text_stats(doc)
    if stats["needs_ocr"]:
        return {
            "schema_version": "0.2",
            "document_sha256": digest,
            "status": "needs_ocr",
            "parser_version": PARSER_VERSION,
            "stats": stats,
            "candidate_count": 0,
            "candidates": [],
        }, 0

    candidates = segment_document(doc, digest)
    payloads = []
    visual_asset_count = 0

    for candidate in candidates:
        by_page: dict[int, list[Line]] = defaultdict(list)
        for line in candidate.lines:
            by_page[line.page].append(line)

        assets = []
        for page_num, lines in sorted(by_page.items()):
            page = doc[page_num - 1]
            text_rect = union_rect(lines)
            visuals = relevant_visuals(page, text_rect)
            if not visuals:
                continue
            crop = render_visual_crop(page, text_rect, visuals)
            path = candidate_asset_path(dbx.root, digest, candidate.candidate_id, page_num)
            dbx.upload_bytes(path, crop, overwrite=False)
            visual_asset_count += 1
            assets.append({
                "type": "source_visual_crop",
                "page": page_num,
                "path": path,
                "sha256": hashlib.sha256(crop).hexdigest(),
                "mime": "image/png",
                "bytes": len(crop),
            })

        payloads.append(candidate_payload(candidate, digest, occurrences, assets))

    manifest = {
        "schema_version": "0.2",
        "document_sha256": digest,
        "status": "parsed_candidates",
        "parser_version": PARSER_VERSION,
        "stats": stats,
        "candidate_count": len(payloads),
        "visual_asset_count": visual_asset_count,
        "source_occurrences": [
            {
                "source_id": x.get("source_id", ""),
                "url": x.get("url", ""),
                "dropbox_path": x.get("dropbox_path", ""),
            }
            for x in occurrences
        ],
        "candidates": payloads,
    }
    return manifest, len(payloads)


def summarize_parse_state(state: dict[str, dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in state.values():
        status = row.get("status", "UNKNOWN")
        out[status] = out.get(status, 0) + 1
    return dict(sorted(out.items()))


def main() -> None:
    p = argparse.ArgumentParser(description="Incremental Dropbox RAW -> task candidates parser")
    p.add_argument("--max-documents", type=int, default=int(os.getenv("PARSER_MAX_DOCUMENTS", "20")))
    args = p.parse_args()

    dbx = DropboxClient(
        require_env("DROPBOX_APP_KEY"),
        require_env("DROPBOX_APP_SECRET"),
        require_env("DROPBOX_REFRESH_TOKEN"),
        os.getenv("DROPBOX_ROOT", "/OlympiadCorpus"),
    )

    crawl_state = load_jsonl_bytes(dbx.download_bytes(dbx.checkpoint_path()), "document_id")
    parse_path = parser_state_path(dbx.root)
    parse_state = load_jsonl_bytes(dbx.download_bytes(parse_path), "document_sha256")
    grouped = group_documents(crawl_state)

    eligible = []
    for digest, occurrences in grouped.items():
        prior = parse_state.get(digest)
        if (
            prior
            and prior.get("status") in {"PARSED", "NEEDS_OCR", "UNSUPPORTED", "FAILED_TERMINAL"}
            and prior.get("parser_version") == PARSER_VERSION
        ):
            continue
        eligible.append((digest, occurrences))
    eligible.sort(key=lambda item: min(x.get("first_seen", "") for x in item[1]))

    processed = 0
    for digest, occurrences in eligible[: max(0, args.max_documents)]:
        now = utc_now()
        raw_path = next((x.get("dropbox_path") for x in occurrences if x.get("dropbox_path")), "")
        ext = extension_from_path(raw_path)
        row = parse_state.get(digest, {
            "document_sha256": digest,
            "attempts": 0,
            "first_seen": now,
        })
        row["updated_at"] = now
        row["attempts"] = int(row.get("attempts", 0)) + 1
        row["raw_path"] = raw_path
        row["source_count"] = len(occurrences)
        row["parser_version"] = PARSER_VERSION

        if ext not in SUPPORTED_PARSE_EXTENSIONS:
            row["status"] = "UNSUPPORTED"
            row["last_error"] = f"parser does not yet support {ext or 'unknown'}"
            parse_state[digest] = row
            processed += 1
            continue

        try:
            data = dbx.download_bytes(raw_path)
            if not data:
                raise RuntimeError("raw_missing_in_dropbox")
            manifest, count = parse_pdf_bytes_layout(data, digest, occurrences, dbx)
            manifest_path = candidate_manifest_path(dbx.root, digest)
            dbx.upload_bytes(
                manifest_path,
                json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
                overwrite=True,
            )
            row["status"] = "NEEDS_OCR" if manifest["status"] == "needs_ocr" else "PARSED"
            row["candidate_count"] = count
            row["manifest_path"] = manifest_path
            row["last_error"] = ""
        except Exception as exc:
            attempts = int(row.get("attempts", 0))
            row["status"] = "FAILED_TERMINAL" if attempts >= 4 else "FAILED_RETRYABLE"
            row["last_error"] = str(exc)[:1000]
        row["updated_at"] = utc_now()
        parse_state[digest] = row
        dbx.upload_bytes(parse_path, dump_jsonl_bytes(parse_state, "document_sha256"), overwrite=True)
        processed += 1

    # Always checkpoint parser state, including empty/unsupported runs.
    dbx.upload_bytes(parse_path, dump_jsonl_bytes(parse_state, "document_sha256"), overwrite=True)

    remaining = sum(
        1 for digest in grouped
        if digest not in parse_state
        or parse_state[digest].get("status") == "FAILED_RETRYABLE"
    )
    summary = {
        "processed": processed,
        "unique_raw_documents": len(grouped),
        "remaining": remaining,
        "status": summarize_parse_state(parse_state),
        "should_continue": processed > 0 and remaining > 0,
    }
    Path("parser_run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
