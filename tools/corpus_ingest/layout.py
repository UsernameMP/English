from __future__ import annotations

import hashlib
import json
from typing import Any

import fitz  # PyMuPDF

SCHEMA_VERSION = "layout.v1"


def _r(v: float) -> float:
    return round(float(v), 3)


def _bbox(box: Any) -> list[float]:
    r = fitz.Rect(box)
    return [_r(r.x0), _r(r.y0), _r(r.x1), _r(r.y1)]


def stable_layout_id(kind: str, document_sha256: str, page_index: int, bbox: Any, payload: str = "") -> str:
    material = json.dumps(
        {
            "kind": kind,
            "document_sha256": document_sha256,
            "page_index": page_index,
            "bbox": _bbox(bbox),
            "payload": payload.strip(),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"{kind}_{hashlib.sha1(material.encode('utf-8')).hexdigest()[:20]}"


def extract_pdf_layout(pdf_bytes: bytes, document_sha256: str) -> dict[str, Any]:
    """Create the one canonical layout representation used by downstream stages."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[dict[str, Any]] = []

    for page_index, page in enumerate(doc):
        page_number = page_index + 1
        text_dict = page.get_text("dict")
        blocks: list[dict[str, Any]] = []
        reading_order = 0

        for raw_block in text_dict.get("blocks", []):
            block_bbox = raw_block.get("bbox") or (0, 0, 0, 0)
            if raw_block.get("type") != 0:
                continue

            lines: list[dict[str, Any]] = []
            block_text_parts: list[str] = []
            for line_index, raw_line in enumerate(raw_block.get("lines", [])):
                spans: list[dict[str, Any]] = []
                line_text_parts: list[str] = []
                for span_index, raw_span in enumerate(raw_line.get("spans", [])):
                    text = raw_span.get("text", "")
                    span_bbox = raw_span.get("bbox") or raw_line.get("bbox") or block_bbox
                    span_id = stable_layout_id(
                        "span", document_sha256, page_index, span_bbox,
                        f"{line_index}:{span_index}:{text}",
                    )
                    spans.append(
                        {
                            "id": span_id,
                            "text": text,
                            "bbox": _bbox(span_bbox),
                            "font": raw_span.get("font", ""),
                            "size": _r(raw_span.get("size", 0)),
                            "flags": int(raw_span.get("flags", 0)),
                            "color": int(raw_span.get("color", 0)),
                            "origin": [*_bbox((*raw_span.get("origin", (0, 0)), *raw_span.get("origin", (0, 0))))[:2]],
                            "source": {"page": page_number, "block": len(blocks), "line": line_index, "span": span_index},
                        }
                    )
                    line_text_parts.append(text)

                line_text = "".join(line_text_parts).strip()
                if not line_text and not spans:
                    continue
                line_bbox = raw_line.get("bbox") or block_bbox
                line_id = stable_layout_id(
                    "line", document_sha256, page_index, line_bbox,
                    f"{line_index}:{line_text}",
                )
                lines.append(
                    {
                        "id": line_id,
                        "text": line_text,
                        "bbox": _bbox(line_bbox),
                        "spans": spans,
                        "reading_order": reading_order,
                    }
                )
                reading_order += 1
                if line_text:
                    block_text_parts.append(line_text)

            block_text = "\n".join(block_text_parts)
            block_id = stable_layout_id(
                "block", document_sha256, page_index, block_bbox, block_text
            )
            blocks.append(
                {
                    "id": block_id,
                    "type": "text",
                    "text": block_text,
                    "bbox": _bbox(block_bbox),
                    "lines": lines,
                    "reading_order": lines[0]["reading_order"] if lines else reading_order,
                }
            )

        images = []
        for idx, image in enumerate(page.get_image_info(xrefs=True)):
            box = image.get("bbox")
            if not box:
                continue
            images.append(
                {
                    "id": stable_layout_id("image", document_sha256, page_index, box, str(image.get("xref", idx))),
                    "bbox": _bbox(box),
                    "xref": int(image.get("xref", 0) or 0),
                    "width": int(image.get("width", 0) or 0),
                    "height": int(image.get("height", 0) or 0),
                }
            )

        drawings = []
        for idx, drawing in enumerate(page.get_drawings()):
            box = drawing.get("rect")
            if not box:
                continue
            drawings.append(
                {
                    "id": stable_layout_id("drawing", document_sha256, page_index, box, str(idx)),
                    "bbox": _bbox(box),
                    "item_count": len(drawing.get("items", [])),
                }
            )

        tables = []
        if hasattr(page, "find_tables"):
            try:
                finder = page.find_tables()
                for idx, table in enumerate(getattr(finder, "tables", [])):
                    tb = table.bbox
                    cells = []
                    for cidx, cell in enumerate(getattr(table, "cells", []) or []):
                        if cell is None:
                            continue
                        cells.append(
                            {
                                "id": stable_layout_id("cell", document_sha256, page_index, cell, str(cidx)),
                                "bbox": _bbox(cell),
                            }
                        )
                    tables.append(
                        {
                            "id": stable_layout_id("table", document_sha256, page_index, tb, str(idx)),
                            "bbox": _bbox(tb),
                            "cells": cells,
                        }
                    )
            except Exception:
                # Table extraction is additive; failure must not invalidate canonical text/layout.
                pass

        pages.append(
            {
                "id": stable_layout_id("page", document_sha256, page_index, page.rect, str(page_number)),
                "page_number": page_number,
                "width": _r(page.rect.width),
                "height": _r(page.rect.height),
                "blocks": blocks,
                "tables": tables,
                "images": images,
                "drawings": drawings,
                "source": {"document_sha256": document_sha256, "page_number": page_number},
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "document_sha256": document_sha256,
        "page_count": len(pages),
        "pages": pages,
    }


def dumps_layout(layout: dict[str, Any]) -> bytes:
    return json.dumps(layout, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
