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


def test_listening_script_is_one_transcription_container_with_real_tasks():
    layout = layout_from_pages([
        ["The Transcript", "Task 1. First script.", "Speaker: hello"],
        ["Task 2. Second script.", "Speaker: goodbye"],
    ])
    proposal = propose_structure(layout, filename="script-engl-demo.pdf")
    assert proposal["document_role"] == "LISTENING_SCRIPT"
    assert len(proposal["sections"]) == 1
    section = proposal["sections"][0]
    assert section["semantic_type"] == "TRANSCRIPTION"
    assert [t["label"] for t in section["tasks"]] == ["Task 1", "Task 2"]
    assert all(t["kind"] == "TRANSCRIPT_SEGMENT" for t in section["tasks"])


def test_oral_set_ignores_repeated_speaking_header_and_sentence_ending_answer():
    layout = layout_from_pages([[
        "SPEAKING",
        "Set 1",
        "Task 1",
        "1. Monologue. Speak about a writer.",
        "Ask your partner for an answer.",
        "Task 2",
        "Dialogue with the examiner.",
    ]])
    proposal = propose_structure(layout, filename="tasks-engl-9-11-ustn-mun-demo-25-26.pdf")
    assert [x["label"] for x in proposal["sections"]] == ["Speaking Set 1"]
    assert [x["label"] for x in proposal["sections"][0]["tasks"]] == ["Task 1", "Task 2"]


def test_answer_key_keeps_skill_sections_and_creates_answer_groups():
    layout = layout_from_pages([[
        "КРИТЕРИИ И МЕТОДИКА ОЦЕНИВАНИЯ",
        "Listening",
        "Keys",
        "Task 1. A B C",
        "Task 2. D E F",
        "Reading",
        "KEYS",
        "1 A",
        "2 B",
        "WRITING – КРИТЕРИИ ОЦЕНИВАНИЯ",
        "Maximum 10 points",
    ]])
    proposal = propose_structure(layout, filename="ans-engl-demo.pdf")
    assert proposal["document_role"] == "ANSWER_KEY"
    assert [x["semantic_type"] for x in proposal["sections"]] == ["LISTENING", "READING", "CRITERIA"]
    assert [t["kind"] for t in proposal["sections"][0]["tasks"]] == ["ANSWER_GROUP", "ANSWER_GROUP"]
    assert proposal["sections"][1]["tasks"][0]["kind"] == "ANSWER_GROUP"
    assert proposal["sections"][2]["tasks"][0]["kind"] == "CRITERION_GROUP"


def test_writing_without_task_number_is_still_an_assessable_task():
    layout = layout_from_pages([[
        "WRITING",
        "Write your review (150-190 words).",
    ]])
    proposal = propose_structure(layout, filename="tasks-engl-demo.pdf")
    task = proposal["sections"][0]["tasks"][0]
    assert task["label"] == "Review"
    assert task["kind"] == "EXTENDED_RESPONSE"


def test_math_lettered_subparts_become_parts_not_tasks():
    layout = layout_from_pages([[
        "MATHEMATICS",
        "Problem 1. Prove the following statements.",
        "a) Prove the first identity.",
        "b) Prove the second identity.",
    ]])
    proposal = propose_structure(layout, filename="tasks-math-demo.pdf")
    tasks = flatten_tasks(proposal)
    assert len(tasks) == 1
    assert tasks[0]["kind"] == "COMPOSITE"
    assert [p["label"] for p in tasks[0]["parts"]] == ["Part a", "Part b"]
    assert tasks[0]["response_mode"] == "MIXED"


def test_multiple_choice_lowercase_options_are_not_promoted_to_parts():
    layout = layout_from_pages([[
        "READING",
        "Task 1. Choose the correct answer.",
        "a) first",
        "b) second",
        "c) third",
    ]])
    task = flatten_tasks(propose_structure(layout, filename="tasks-engl-demo.pdf"))[0]
    assert task["kind"] == "SELECT_ONE"
    assert task["parts"] == []


def test_oral_set_spans_stop_before_next_repeated_set_header():
    layout = layout_from_pages([
        ["SPEAKING", "Set 1", "Task 1", "1. Monologue. Speak about A.", "Task 2", "1. Listen to your partner.", "2. Ask two questions."],
        ["Fact file A"],
        ["Fact file B"],
        ["SPEAKING", "Set 2", "Task 1", "1. Monologue. Speak about B.", "Task 2", "1. Listen to your partner.", "2. Ask two questions."],
        ["Fact file C"],
        ["Fact file D"],
    ])
    proposal = propose_structure(layout, filename="tasks-engl-9-11-ustn-mun-demo-25-26.pdf")
    first = proposal["sections"][0]
    second = proposal["sections"][1]
    assert first["page_start"] == 1
    assert first["page_end"] == 3
    assert second["page_start"] == 4
    assert first["tasks"][1]["kind"] == "ORAL_RESPONSE"
    assert first["tasks"][1]["page_end"] == 3
    assert first["tasks"][1].get("item_range") is None


def test_writing_semantic_task_uses_real_response_label():
    layout = layout_from_pages([[
        "WRITING",
        "ARTICLES WANTED",
        "Write your article (180-200 words).",
    ]])
    proposal = propose_structure(layout, filename="tasks-engl-demo.pdf")
    task = proposal["sections"][0]["tasks"][0]
    assert task["label"] == "Article"
    assert task["kind"] == "EXTENDED_RESPONSE"


def test_answer_score_summary_does_not_create_extra_criteria_section():
    layout = layout_from_pages([[
        "LISTENING",
        "Task 1 A B",
        "READING",
        "1 A",
        "WRITING – Criteria",
        "Rubric table",
        "Criteria and scoring scheme",
        "Writing – maximum 15 points. The task is evaluated by criteria.",
        "Maximum total score is 56 points.",
    ]])
    proposal = propose_structure(layout, filename="ans-engl-demo.pdf")
    labels = [s["label"] for s in proposal["sections"]]
    assert "Writing – maximum 15 points. The task is evaluated by criteria." not in labels
    assert [s["semantic_type"] for s in proposal["sections"]].count("CRITERIA") >= 1


def test_hyphenated_pdf_line_break_still_classifies_select_one():
    layout = layout_from_pages([[
        "READING",
        "Task 2. For questions 10-14, choose the an-",
        "swer (A, B, C or D) which fits best according to the text.",
    ]])
    task = flatten_tasks(propose_structure(layout, filename="tasks-engl-demo.pdf"))[0]
    assert task["kind"] == "SELECT_ONE"


def test_subject_agnostic_math_tasks_form_one_section():
    layout = layout_from_pages([[
        "MATHEMATICS",
        "Problem 1. Calculate the value.",
        "Problem 2. Prove the statement.",
        "Problem 3. Find the number.",
    ]])
    proposal = propose_structure(layout, filename="tasks-math-9-mun-demo-24-25.pdf")
    assert len(proposal["sections"]) == 1
    assert proposal["sections"][0]["label"] == "Tasks"
    assert [t["label"] for t in proposal["sections"][0]["tasks"]] == ["Task 1", "Task 2", "Task 3"]


def test_biology_part_groups_accept_decimal_tasks():
    layout = layout_from_pages([[
        "Part 1.",
        "1.1. Choose one correct answer.",
        "1.2. Choose all correct answers.",
        "Part 2.",
        "2.1. Match the items.",
    ]])
    proposal = propose_structure(layout, filename="tasks-biol-10-mun-demo-24-25.pdf")
    assert [s["semantic_type"] for s in proposal["sections"]] == ["PART_GROUP", "PART_GROUP"]
    assert [t["label"] for t in proposal["sections"][0]["tasks"]] == ["Task 1.1", "Task 1.2"]
    assert proposal["sections"][0]["tasks"][0]["kind"] == "SELECT_ONE"
    assert proposal["sections"][0]["tasks"][1]["kind"] == "SELECT_MULTIPLE"
    assert proposal["sections"][1]["tasks"][0]["kind"] == "MATCHING"


def test_answer_part_group_detects_answer_to_question_lines():
    layout = layout_from_pages([[
        "Section 1.",
        "Answer to question 1: 2",
        "Answer to question 2: 4",
    ]])
    proposal = propose_structure(layout, filename="ans-biol-10-mun-demo-24-25.pdf")
    assert proposal["sections"][0]["semantic_type"] == "PART_GROUP"
    assert [t["label"] for t in proposal["sections"][0]["tasks"]] == ["Task 1", "Task 2"]
    assert all(t["kind"] == "ANSWER_GROUP" for t in proposal["sections"][0]["tasks"])


def test_task_reconstruction_separates_marker_from_statement_blocks():
    layout = layout_from_pages([[
        ("GEOGRAPHY", 18),
        "Task 1",
        "Determine the map scale using the information below.",
        "A. 1:10 000",
        "B. 1:100 000",
        "Task 2",
        "Name the process.",
    ]])
    tasks = flatten_tasks(propose_structure(layout, filename="tasks-geog-demo.pdf"))
    first = tasks[0]
    assert first["body_blocks"][0]["role"] == "TASK_MARKER"
    assert "Task 1" not in first["body_text"]
    assert "Determine the map scale" in first["body_text"]
    assert any(b["role"] == "INSTRUCTION" for b in first["body_blocks"])
    assert all(b.get("source_block_id") for b in first["body_blocks"])
    assert first["body_spans"]
    assert first["boundary_confidence"] >= 0.8


def test_task_boundary_does_not_swallow_next_task_heading():
    layout = layout_from_pages([[
        "Task 1",
        "Read this statement carefully.",
        "First body line.",
        "Task 2",
        "Second body line.",
    ]])
    tasks = flatten_tasks(propose_structure(layout, filename="tasks-history-demo.pdf"))
    assert len(tasks) == 2
    assert "Task 2" not in tasks[0]["body_text"]
    assert "Second body line" not in tasks[0]["body_text"]
    assert "Second body line" in tasks[1]["body_text"]


def test_composite_task_emits_task_group_and_shared_stimulus_edges():
    layout = layout_from_pages([[
        "Problem 1. Read the common source.",
        "The same source is used for both parts.",
        "a) Find the first value.",
        "b) Using the previous answer, prove the claim.",
    ]])
    task = flatten_tasks(propose_structure(layout, filename="tasks-math-demo.pdf"))[0]
    composition = task["composition"]
    kinds = {n["kind"] for n in composition["nodes"]}
    edge_types = {e["type"] for e in composition["edges"]}
    assert "TASK_GROUP" in kinds
    assert "SHARED_STIMULUS" in kinds
    assert "OWNS_PART" in edge_types
    assert "USES_STIMULUS" in edge_types
    assert "DEPENDS_ON" in edge_types


def test_formula_text_becomes_typed_artifact():
    layout = layout_from_pages([[
        "Problem 1. Calculate the value.",
        "x^2 + y^2 = 25",
        "Find x when y = 3.",
    ]])
    task = flatten_tasks(propose_structure(layout, filename="tasks-math-demo.pdf"))[0]
    assert any(a["kind"] == "FORMULA" for a in task["artifacts"])
    formula = next(a for a in task["artifacts"] if a["kind"] == "FORMULA")
    assert formula["asset_binding_confidence"] >= 0.9


def test_reconstruction_confidence_and_review_flag_are_emitted():
    layout = layout_from_pages([[
        "Task 1",
        "Choose the correct answer.",
        "A. Alpha",
        "B. Beta",
    ]])
    task = flatten_tasks(propose_structure(layout, filename="tasks-demo.pdf"))[0]
    assert 0 <= task["reconstruction_confidence"] <= 1
    assert isinstance(task["review_required"], bool)
    assert "boundary" in task["reconstruction_reasons"]
