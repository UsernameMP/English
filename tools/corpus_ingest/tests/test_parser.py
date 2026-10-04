import fitz

from parser import (
    detect_task_starts,
    document_text_stats,
    group_documents,
    page_lines,
    segment_document,
)


def make_pdf(pages):
    doc = fitz.open()
    for lines in pages:
        page = doc.new_page()
        y = 72
        for line in lines:
            page.insert_text((72, y), line)
            y += 20
    return doc


def test_keyword_headings_win_over_numbered_subitems():
    doc = make_pdf([[
        "Task 1",
        "Read the text.",
        "1. First subquestion",
        "2. Second subquestion",
        "Task 2",
        "Write an answer.",
    ]])
    lines = page_lines(doc[0])
    starts, method, confidence = detect_task_starts(lines)
    assert method == "keyword_heading"
    assert [n for _, n in starts] == ["1", "2"]
    assert confidence > 0.9


def test_segment_keyword_tasks_not_subitems():
    doc = make_pdf([[
        "Task 1",
        "Read the text.",
        "1. First subquestion",
        "2. Second subquestion",
        "Task 2",
        "Write an answer.",
    ]])
    candidates = segment_document(doc, "a" * 64)
    assert len(candidates) == 2
    assert candidates[0].number == "1"
    assert candidates[1].number == "2"


def test_page_fragments_when_no_task_boundary():
    doc = make_pdf([
        ["Instructions only on this page."],
        ["Another page without a task heading."],
    ])
    candidates = segment_document(doc, "b" * 64)
    assert len(candidates) == 2
    assert all(x.boundary_method == "page_fragment" for x in candidates)


def test_scanned_like_pdf_needs_ocr():
    doc = fitz.open()
    doc.new_page()
    stats = document_text_stats(doc)
    assert stats["needs_ocr"] is True


def test_group_documents_deduplicates_by_sha():
    state = {
        "1": {"status": "DOWNLOADED", "sha256": "abc", "url": "a"},
        "2": {"status": "DUPLICATE", "sha256": "abc", "url": "b"},
        "3": {"status": "PENDING", "sha256": "", "url": "c"},
    }
    grouped = group_documents(state)
    assert list(grouped) == ["abc"]
    assert len(grouped["abc"]) == 2
