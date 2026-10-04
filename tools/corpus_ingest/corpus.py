from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import fitz  # PyMuPDF
import requests

TASK_START_RE = re.compile(r"^\s*(?:(?:Задача|Problem)\s*)?(\d{1,3})\s*[.)]\s+", re.I)
SUSPICIOUS_TEXT_RE = re.compile(r"[�□]{1,}|\?{3,}")
MATH_HINT_RE = re.compile(r"[=<>±×÷√∑∫∞≤≥∠⊥∥]|\b(?:sin|cos|tg|ctg|log)\b", re.I)


@dataclass
class SourceRow:
    source_id: str
    url: str
    subject: str = ""
    year: str = ""
    olympiad: str = ""
    stage: str = ""
    grade: str = ""


@dataclass
class TaskCandidate:
    page: int
    number: str | None
    text: str
    rect: fitz.Rect
    has_image: bool
    has_drawing: bool
    confidence: float
    status: str
    reason: str


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            source_id TEXT NOT NULL,
            url TEXT NOT NULL,
            sha256 TEXT NOT NULL UNIQUE,
            local_path TEXT NOT NULL,
            subject TEXT,
            year TEXT,
            olympiad TEXT,
            stage TEXT,
            grade TEXT,
            pages INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            document_id INTEGER NOT NULL REFERENCES documents(id),
            page INTEGER NOT NULL,
            task_number TEXT,
            extracted_text TEXT NOT NULL,
            edited_text TEXT,
            formula_latex TEXT,
            crop_path TEXT NOT NULL,
            has_image INTEGER NOT NULL DEFAULT 0,
            has_drawing INTEGER NOT NULL DEFAULT 0,
            confidence REAL NOT NULL,
            status TEXT NOT NULL,
            review_reason TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE TABLE IF NOT EXISTS review_events (
            id INTEGER PRIMARY KEY,
            task_id INTEGER NOT NULL REFERENCES tasks(id),
            action TEXT NOT NULL,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    return conn


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_sources(path: Path) -> Iterable[SourceRow]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if not row.get("url"):
                continue
            yield SourceRow(**{k: (row.get(k) or "").strip() for k in SourceRow.__annotations__})


def extension_for(url: str, content_type: str | None) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".pdf", ".docx", ".zip", ".html", ".htm"}:
        return suffix
    if content_type and "pdf" in content_type.lower():
        return ".pdf"
    return ".bin"


def download(source: SourceRow, raw_dir: Path) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    r = requests.get(source.url, timeout=60, stream=True, headers={"User-Agent": "OlympiadCorpusPrototype/0.1"})
    r.raise_for_status()
    ext = extension_for(source.url, r.headers.get("content-type"))
    tmp = raw_dir / f".{source.source_id}.download"
    with tmp.open("wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            if chunk:
                f.write(chunk)
    digest = sha256_file(tmp)
    dest = raw_dir / f"{digest}{ext}"
    if dest.exists():
        tmp.unlink()
    else:
        tmp.replace(dest)
    return dest


def line_blocks(page: fitz.Page) -> list[tuple[fitz.Rect, str]]:
    out: list[tuple[fitz.Rect, str]] = []
    raw = page.get_text("dict")
    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = "".join(span.get("text", "") for span in spans).strip()
            if not text:
                continue
            rect = fitz.Rect(line["bbox"])
            out.append((rect, text))
    out.sort(key=lambda x: (round(x[0].y0, 1), x[0].x0))
    return out


def intersects_any(rect: fitz.Rect, rects: list[fitz.Rect]) -> bool:
    return any((rect & other).get_area() > 1 for other in rects)


def candidate_confidence(text: str, has_image: bool, has_drawing: bool, numbered: bool) -> tuple[float, str, str]:
    score = 0.97
    reasons: list[str] = []
    if len(text.strip()) < 40:
        score -= 0.28
        reasons.append("very_short_text")
    if SUSPICIOUS_TEXT_RE.search(text):
        score -= 0.32
        reasons.append("broken_glyphs")
    if has_image:
        score -= 0.18
        reasons.append("embedded_image")
    if has_drawing:
        score -= 0.14
        reasons.append("vector_drawing")
    if MATH_HINT_RE.search(text) and len(text) < 90:
        score -= 0.08
        reasons.append("formula_heavy")
    if not numbered:
        score -= 0.18
        reasons.append("task_boundary_uncertain")
    score = max(0.0, min(1.0, score))
    if score >= 0.90:
        status = "accepted"
    elif score >= 0.65:
        status = "needs_llm"
    else:
        status = "needs_human"
    return score, status, ",".join(reasons) or "clean_text"


def segment_page(page: fitz.Page) -> list[TaskCandidate]:
    lines = line_blocks(page)
    if not lines:
        return []

    image_rects = [fitz.Rect(img["bbox"]) for img in page.get_image_info(xrefs=True) if img.get("bbox")]
    drawing_rects = [d["rect"] for d in page.get_drawings() if d.get("rect")]

    starts: list[tuple[int, str]] = []
    for idx, (_, text) in enumerate(lines):
        m = TASK_START_RE.match(text)
        if m:
            starts.append((idx, m.group(1)))

    candidates: list[TaskCandidate] = []
    groups: list[tuple[int, int, str | None]] = []
    if starts:
        for n, (start_idx, number) in enumerate(starts):
            end_idx = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
            groups.append((start_idx, end_idx, number))
    else:
        groups.append((0, len(lines), None))

    for start, end, number in groups:
        selected = lines[start:end]
        text = "\n".join(t for _, t in selected).strip()
        rect = selected[0][0]
        for r, _ in selected[1:]:
            rect |= r

        band = fitz.Rect(
            page.rect.x0,
            max(page.rect.y0, rect.y0 - 8),
            page.rect.x1,
            min(page.rect.y1, rect.y1 + 80),
        )
        relevant_images = [r for r in image_rects if intersects_any(band, [r])]
        relevant_drawings = [r for r in drawing_rects if intersects_any(band, [r])]
        for r in relevant_images + relevant_drawings:
            rect |= r

        rect = fitz.Rect(
            max(0, rect.x0 - 12),
            max(0, rect.y0 - 12),
            min(page.rect.x1, rect.x1 + 12),
            min(page.rect.y1, rect.y1 + 12),
        )
        score, status, reason = candidate_confidence(
            text,
            bool(relevant_images),
            bool(relevant_drawings),
            number is not None,
        )
        candidates.append(
            TaskCandidate(
                page.number + 1,
                number,
                text,
                rect,
                bool(relevant_images),
                bool(relevant_drawings),
                score,
                status,
                reason,
            )
        )
    return candidates


def render_crop(page: fitz.Page, rect: fitz.Rect, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=rect, alpha=False)
    pix.save(path)


def insert_document(conn: sqlite3.Connection, source: SourceRow, path: Path, pages: int) -> int:
    digest = sha256_file(path)
    conn.execute(
        """INSERT OR IGNORE INTO documents
        (source_id,url,sha256,local_path,subject,year,olympiad,stage,grade,pages)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            source.source_id,
            source.url,
            digest,
            str(path),
            source.subject,
            source.year,
            source.olympiad,
            source.stage,
            source.grade,
            pages,
        ),
    )
    row = conn.execute("SELECT id FROM documents WHERE sha256=?", (digest,)).fetchone()
    assert row
    return int(row["id"])


def parse_pdf(conn: sqlite3.Connection, source: SourceRow, pdf_path: Path, crop_dir: Path) -> dict:
    doc = fitz.open(pdf_path)
    document_id = insert_document(conn, source, pdf_path, len(doc))
    existing = conn.execute("SELECT COUNT(*) c FROM tasks WHERE document_id=?", (document_id,)).fetchone()["c"]
    if existing:
        return {"document_id": document_id, "skipped": True, "tasks": existing}

    counts = {"accepted": 0, "needs_llm": 0, "needs_human": 0}
    total = 0
    for page in doc:
        for cand in segment_page(page):
            total += 1
            crop_path = crop_dir / str(document_id) / f"p{cand.page:04d}_t{total:04d}.png"
            render_crop(page, cand.rect, crop_path)
            conn.execute(
                """INSERT INTO tasks
                (document_id,page,task_number,extracted_text,crop_path,has_image,has_drawing,confidence,status,review_reason)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    document_id,
                    cand.page,
                    cand.number,
                    cand.text,
                    str(crop_path),
                    int(cand.has_image),
                    int(cand.has_drawing),
                    cand.confidence,
                    cand.status,
                    cand.reason,
                ),
            )
            counts[cand.status] += 1
    conn.commit()
    return {"document_id": document_id, "skipped": False, "tasks": total, **counts}


def export_llm_queue(conn: sqlite3.Connection, path: Path) -> int:
    rows = conn.execute(
        """SELECT t.id,t.page,t.task_number,t.extracted_text,t.crop_path,t.confidence,t.review_reason,
                  d.source_id,d.subject,d.year,d.olympiad,d.stage,d.grade
           FROM tasks t JOIN documents d ON d.id=t.document_id
           WHERE t.status='needs_llm' ORDER BY t.id"""
    ).fetchall()

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            payload = dict(r)
            payload["instruction"] = (
                "Extract only what is visible. Never reconstruct unreadable formulas or missing text. "
                "If uncertain, return needs_human=true and issue_type formula/image/boundary/ocr/other."
            )
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return len(rows)


def ingest_sources(sources_csv: Path, root: Path) -> None:
    conn = connect(root / "corpus.sqlite3")
    raw_dir, crop_dir = root / "raw", root / "crops"

    for source in read_sources(sources_csv):
        try:
            path = download(source, raw_dir)
            if path.suffix.lower() != ".pdf":
                print(
                    json.dumps(
                        {
                            "source_id": source.source_id,
                            "status": "downloaded_non_pdf",
                            "path": str(path),
                        },
                        ensure_ascii=False,
                    )
                )
                continue

            result = parse_pdf(conn, source, path, crop_dir)
            print(json.dumps({"source_id": source.source_id, **result}, ensure_ascii=False))
        except Exception as exc:
            print(json.dumps({"source_id": source.source_id, "error": str(exc)}, ensure_ascii=False))

    n = export_llm_queue(conn, root / "queues" / "needs_llm.jsonl")
    print(json.dumps({"llm_queue": n, "db": str(root / "corpus.sqlite3")}, ensure_ascii=False))


def main() -> None:
    p = argparse.ArgumentParser(description="Prototype olympiad corpus downloader/parser")
    p.add_argument("sources", type=Path, help="CSV source registry")
    p.add_argument("--root", type=Path, default=Path(".corpus"), help="local corpus workspace")
    args = p.parse_args()
    ingest_sources(args.sources, args.root)


if __name__ == "__main__":
    main()
