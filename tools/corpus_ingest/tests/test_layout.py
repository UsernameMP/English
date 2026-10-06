import hashlib

import fitz

from layout import extract_pdf_layout


def make_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Task 1. Choose the correct answer.")
    page.insert_text((72, 96), "A) Alpha   B) Beta")
    return doc.tobytes()


def test_layout_ids_are_stable_for_same_document():
    data = make_pdf()
    digest = hashlib.sha256(data).hexdigest()
    first = extract_pdf_layout(data, digest)
    second = extract_pdf_layout(data, digest)

    assert first["schema_version"] == "layout.v1"
    assert first["page_count"] == 1
    assert first == second
    assert first["pages"][0]["blocks"]
    line = first["pages"][0]["blocks"][0]["lines"][0]
    assert line["id"].startswith("line_")
    assert len(line["bbox"]) == 4


def test_layout_preserves_source_coordinates():
    data = make_pdf()
    digest = hashlib.sha256(data).hexdigest()
    layout = extract_pdf_layout(data, digest)

    page = layout["pages"][0]
    assert page["source"]["document_sha256"] == digest
    assert page["source"]["page_number"] == 1
    for block in page["blocks"]:
        assert len(block["bbox"]) == 4
        for line in block["lines"]:
            assert len(line["bbox"]) == 4
            for span in line["spans"]:
                assert len(span["bbox"]) == 4
                assert len(span["origin"]) == 2
