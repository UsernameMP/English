# Corpus Assessor Workbench

Browser-first assessor UI for OlympiadCorpus.

## Launch

Current manual triage:
https://usernamemp.github.io/English/

New multi-pass assessor prototype:
https://usernamemp.github.io/English/arm.html

No git clone or local server is required.

## Architecture

RAW remains immutable in Dropbox.

Production ingest now follows:

RAW
→ canonical layout JSON
→ machine document profile
→ ProblemSet bundle proposal
→ Pass 1 human review
→ machine Section / Task proposal
→ Pass 2 boundary review
→ Answer / Criterion / Media linker
→ exception review
→ canonical corpus graph

The canonical layout implementation is in:
- `tools/corpus_ingest/layout.py`
- `tools/corpus_ingest/layout_pipeline.py`

The stable graph implementation is in:
- `tools/corpus_ingest/corpus_graph.py`

The parser entrypoint is routed through the layout-first pipeline; the old RAW→candidate path is no longer the production path.

## Assessor prototype

`arm.html` has three modes.

### Pass 1 — Document + ProblemSet

Machine proposes:
- document type;
- subject;
- language;
- academic year;
- grades;
- competition;
- stage;
- tour;
- region;
- ProblemSet.

Every reviewed field stores:
- machine value;
- human value;
- confidence;
- evidence;
- human decision.

The reviewer can confirm a whole document, correct one field, mark Needs review, and confirm the proposed ProblemSet bundle.

### Pass 2 — Sections + Tasks

Machine proposes a `Section → Task → Subtask` tree.

The reviewer can:
- confirm the structure;
- show only low-confidence boundaries;
- move a boundary;
- split a section;
- merge with the next section;
- accept an individual node.

Boundary edits recalculate child task spans.

### Links — Answers / Criteria / Media

The prototype shows:
- ProblemSet coverage;
- suggested graph edges;
- confirm/reject actions;
- unresolved-only queue;
- structural exceptions.

Current exceptions include:
- task without answer;
- answer without task;
- media without task;
- incomplete bundle;
- ambiguous/duplicate task numbering;
- one criterion target reused by multiple tasks.

## Important prototype limitation

The review contracts and audit structure are production-shaped, but the machine proposals visible in `arm.html` are currently heuristic proposals derived from source filenames and the current ten-document calibration batch.

They are intentionally replaceable by the future classifier/sectioner without changing the assessor UI or stored human-decision schema.

## Ground truth

Reviewer decisions are stored locally in the browser and can be exported as audit JSON. The next production step is server-side persistence of these decisions and direct loading of evidence from canonical `layout.json`.
