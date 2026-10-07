import hashlib

import fitz

from layout import extract_pdf_layout
from task_structure import flatten_tasks, propose_structure


def layout_from_pages(pages):
    doc = fitz.open()
    for rows in pages:
        page = doc.new_page()
        y = 72
        for row in rows:
            if isinstance(row, tuple):
                text, size = row
            else:
                text, size = row, 11
            page.insert_text((72, y), text, fontsize=size)
            y += 24
    data = doc.tobytes()
    return extract_pdf_layout(data, hashlib.sha256(data).hexdigest())


def test_explicit_tasks_win_over_numbered_items():
    layout = layout_from_pages([[
        ("READING", 18),
        "Task 1. Read the text.",
        "1. First statement",
        "2. Second statement",
        "Task 2. Match the paragraphs.",
        "11. Alpha",
        "12. Beta",
    ]])
    proposal = propose_structure(layout, filename="tasks-demo.pdf")
    tasks = flatten_tasks(proposal)
    assert [t["label"] for t in tasks] == ["Task 1", "Task 2"]
    assert tasks[0]["item_range"]["start"] == 1
    assert tasks[0]["item_range"]["end"] == 2
    assert tasks[1]["kind"] == "MATCHING"


def test_parts_make_one_composite_task_not_three_tasks():
    layout = layout_from_pages([[
        ("LISTENING", 18),
        "Task 1. You will hear a speech.",
        "Part 1. Complete the form.",
        "1. Name",
        "2. City",
        "Part 2. Answer the questions.",
        "6. Why?",
        "Part 3. Choose the correct answer.",
        "11. A B C",
    ]])
    proposal = propose_structure(layout)
    tasks = flatten_tasks(proposal)
    assert len(tasks) == 1
    assert tasks[0]["kind"] == "COMPOSITE"
    assert [p["label"] for p in tasks[0]["parts"]] == ["Part 1", "Part 2", "Part 3"]


def test_repeated_task_numbers_allowed_in_repeated_sets():
    layout = layout_from_pages([
        [("Speaking Set 1", 18), "Task 1. Speak.", "Task 2. Discuss."],
        [("Speaking Set 2", 18), "Task 1. Speak.", "Task 2. Discuss."],
    ])
    proposal = propose_structure(layout)
    assert [s["semantic_type"] for s in proposal["sections"]] == ["SPEAKING_SET", "SPEAKING_SET"]
    assert [[t["number"] for t in s["tasks"]] for s in proposal["sections"]] == [["1", "2"], ["1", "2"]]


def test_visual_table_is_attached_as_artifact():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "LISTENING", fontsize=18)
    page.insert_text((72, 110), "Task 1. Complete the table.")
    # Draw a simple grid under the task so layout.find_tables can preserve it where supported.
    for x in [72, 172, 272, 372]:
        page.draw_line((x, 150), (x, 270))
    for y in [150, 190, 230, 270]:
        page.draw_line((72, y), (372, y))
    data = doc.tobytes()
    layout = extract_pdf_layout(data, hashlib.sha256(data).hexdigest())
    task = flatten_tasks(propose_structure(layout))[0]
    assert task["kind"] in {"TABLE_GAP_FILL", "GAP_FILL"}
    # Table detection is additive and backend-version dependent; drawings must at least survive.
    assert any(a["kind"] in {"TABLE", "GRID", "DIAGRAM"} for a in task["artifacts"])


def test_no_task_heading_does_not_promote_bare_numbers_to_tasks():
    layout = layout_from_pages([[
        ("READING", 18),
        "Read the passage and answer the questions.",
        "1. First item",
        "2. Second item",
        "3. Third item",
    ]])
    proposal = propose_structure(layout)
    assert len(proposal["sections"]) == 1
    assert proposal["sections"][0]["tasks"] == []
    assert "no_explicit_tasks" in proposal["warnings"]
