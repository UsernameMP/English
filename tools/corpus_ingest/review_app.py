from __future__ import annotations

import sqlite3
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Corpus Human Desk", layout="wide")
st.title("Olympiad Corpus — Human Desk")

root = Path(st.sidebar.text_input("Corpus root", ".corpus"))
db_path = root / "corpus.sqlite3"
if not db_path.exists():
    st.info("Run corpus.py first; corpus.sqlite3 is not present yet.")
    st.stop()

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
show_llm = st.sidebar.checkbox("Also show needs_llm", value=True)
statuses = ["needs_human"] + (["needs_llm"] if show_llm else [])
placeholders = ",".join("?" for _ in statuses)
row = conn.execute(
    f"""SELECT t.*, d.source_id,d.subject,d.year,d.olympiad,d.stage,d.grade
         FROM tasks t JOIN documents d ON d.id=t.document_id
         WHERE t.status IN ({placeholders}) ORDER BY t.confidence ASC,t.id LIMIT 1""",
    statuses,
).fetchone()

if not row:
    st.success("Review queue is empty.")
    st.stop()

left, right = st.columns([1.15, 1])
with left:
    st.caption(f"Source: {row['source_id']} · page {row['page']} · confidence {row['confidence']:.2f}")
    crop = Path(row["crop_path"])
    if crop.exists():
        st.image(str(crop), use_container_width=True)
    else:
        st.error(f"Missing crop: {crop}")

with right:
    st.write(f"**Reason:** `{row['review_reason']}`")
    text_value = st.text_area("Task text", value=row["edited_text"] or row["extracted_text"], height=320)
    formula = st.text_area("Formula LaTeX (only when needed)", value=row["formula_latex"] or "", height=110)
    issue = st.selectbox("Issue type", ["none", "formula", "image", "boundary", "ocr", "other"])
    note = st.text_input("Note", "")

    c1, c2, c3 = st.columns(3)
    if c1.button("Accept", type="primary", use_container_width=True):
        conn.execute(
            "UPDATE tasks SET edited_text=?,formula_latex=?,status='verified',updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (text_value, formula, row["id"]),
        )
        conn.execute("INSERT INTO review_events(task_id,action,note) VALUES (?,?,?)", (row["id"], "verified", note or issue))
        conn.commit()
        st.rerun()
    if c2.button("Keep for human", use_container_width=True):
        conn.execute(
            "UPDATE tasks SET edited_text=?,formula_latex=?,status='needs_human',updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (text_value, formula, row["id"]),
        )
        conn.execute("INSERT INTO review_events(task_id,action,note) VALUES (?,?,?)", (row["id"], "needs_human", note or issue))
        conn.commit()
        st.rerun()
    if c3.button("Reject boundary", use_container_width=True):
        conn.execute("UPDATE tasks SET status='rejected',updated_at=CURRENT_TIMESTAMP WHERE id=?", (row["id"],))
        conn.execute("INSERT INTO review_events(task_id,action,note) VALUES (?,?,?)", (row["id"], "rejected", note or "bad task boundary"))
        conn.commit()
        st.rerun()
