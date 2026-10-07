from __future__ import annotations

import hashlib
import json
from typing import Any

from layout import dumps_layout, extract_pdf_layout
from task_structure import flatten_tasks, propose_structure


PIPELINE_VERSION = "layout-pipeline.v1"


def layout_path(root: str, digest: str) -> str:
    return f"{root.rstrip('/')}/parsed/{digest[:2]}/{digest}/layout.json"


def manifest_path(root: str, digest: str) -> str:
    return f"{root.rstrip('/')}/parsed/{digest[:2]}/{digest}/manifest.json"


def layout_text_stats(layout: dict[str, Any]) -> dict[str, Any]:
    chars_by_page: list[int] = []
    for page in layout.get("pages", []):
        total = 0
        for block in page.get("blocks", []):
            total += len((block.get("text") or "").strip())
        chars_by_page.append(total)
    total_chars = sum(chars_by_page)
    nonempty_pages = sum(1 for x in chars_by_page if x >= 20)
    page_count = int(layout.get("page_count") or len(chars_by_page))
    return {
        "pages": page_count,
        "total_chars": total_chars,
        "nonempty_pages": nonempty_pages,
        "chars_by_page": chars_by_page,
        "needs_ocr": total_chars < max(80, page_count * 20),
    }


def parse_pdf_bytes(
    data: bytes,
    digest: str,
    occurrences: list[dict],
    dbx: Any,
) -> tuple[dict, int]:
    actual = hashlib.sha256(data).hexdigest()
    if actual != digest:
        raise ValueError("raw_sha256_mismatch")

    layout = extract_pdf_layout(data, digest)
    stats = layout_text_stats(layout)
    lpath = layout_path(dbx.root, digest)
    dbx.upload_bytes(lpath, dumps_layout(layout), overwrite=True)

    status = "needs_ocr" if stats["needs_ocr"] else "layout_ready"
    source_filename = ""
    if occurrences:
        source_filename = str(
            occurrences[0].get("dropbox_path")
            or occurrences[0].get("url")
            or ""
        ).rsplit("/", 1)[-1]
    structure = propose_structure(layout, filename=source_filename) if status == "layout_ready" else {
        "schema_version": "structure-proposal.v2",
        "document_sha256": digest,
        "filename": source_filename,
        "sections": [],
        "warnings": ["needs_ocr"],
    }
    manifest = {
        "schema_version": "parsed-document.v2",
        "document_sha256": digest,
        "status": status,
        "pipeline_version": PIPELINE_VERSION,
        "layout_schema_version": layout.get("schema_version"),
        "structure_schema_version": structure.get("schema_version"),
        "layout_path": lpath,
        "layout_sha256": hashlib.sha256(dumps_layout(layout)).hexdigest(),
        "stats": stats,
        "source_occurrences": [
            {
                "source_id": x.get("source_id", ""),
                "url": x.get("url", ""),
                "discovered_from": x.get("discovered_from", ""),
                "dropbox_path": x.get("dropbox_path", ""),
            }
            for x in occurrences
        ],
        "derived": {
            "document_profile": None,
            "problemset_links": [],
            "sections": structure.get("sections", []),
            "tasks": flatten_tasks(structure),
            "structure_proposal": structure,
        },
        "next_stage": "document_triage" if status == "layout_ready" else "ocr",
    }
    return manifest, 0
