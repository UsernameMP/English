# Document Triage Workbench

A human-first browser workbench for OlympiadCorpus document ground truth.

## Browser launch

The intended permanent URL is:

https://usernamemp.github.io/English/

GitHub Pages must be enabled once for this repository:

1. Open repository **Settings**.
2. Open **Pages**.
3. Under **Build and deployment → Source**, choose **GitHub Actions**.
4. The committed workflow `.github/workflows/document-triage-pages.yml` deploys `tools/document_triage/` as the site root.

After that, opening the Pages URL launches the workbench directly in a browser. No git clone or local launcher is required.

Temporary direct static preview (if needed before Pages is enabled):

https://raw.githack.com/UsernameMP/English/main/tools/document_triage/index.html

## Why

Do **not** segment raw files into tasks before knowing what the document is.

The first pass is deliberately manual:

RAW document → human document triage → ground-truth document record → later machine classifier / section parser.

No LLM suggestions are shown in this version. That is intentional: the first labels should be independent ground truth.

## What the right panel records

- one or more document roles;
- subject / olympiad / year / stage / grades / region / tour;
- duration and maximum score;
- structural signals such as embedded answers, visual answer marking, rationales, tables, images, crossword, distractors;
- free-form notes;
- review status.

Labels are autosaved in browser `localStorage`.

Use **Export JSONL** or **Export CSV** to persist the work outside the browser.

## Document roles

Current v0.1 roles:

- `TASK_SET`
- `ANSWER_KEY`
- `CRITERIA`
- `LISTENING_SCRIPT`
- `AUDIO_REFERENCE`
- `METHODOLOGY`
- `ANSWER_SHEET`
- `OTHER`

Roles are multi-select. A mixed file can therefore be `ANSWER_KEY + CRITERIA`, rather than forcing a single coarse `MIXED` type.

## Signals

- `EMBEDDED_ANSWERS`
- `HAS_RATIONALE_OR_EXPLANATIONS`
- `VISUAL_ANSWER_MARKING`
- `HAS_TABLES`
- `HAS_IMAGES_OR_DIAGRAMS`
- `HAS_CROSSWORD`
- `HAS_MULTIPLE_SECTIONS`
- `HAS_DISTRACTOR_OPTIONS`
- `MIXED_DOCUMENT`
- `UNCLEAR_OR_AMBIGUOUS`

## Next version

After enough manual ground truth exists:

1. machine proposes document roles + metadata;
2. human accepts or edits;
3. machine proposes section boundaries and section types;
4. human compares against the original document;
5. only then do type-specific extractors create Task / Answer / Criteria / Script objects.
