# Document Triage Workbench

Browser-only human labeling tool for OlympiadCorpus document ground truth.

## Launch

Open:

https://usernamemp.github.io/English/

No git clone, batch file, or local server is required.

## Current architecture

RAW remains immutable in Dropbox.

For browser review, the workbench loads the original public PDF URL recorded in RAW metadata:

RAW PDF in Dropbox
→ metadata/<sha>.json
→ original_url
→ PDF viewer on the left
→ human labels on the right

Dropbox preview is not embedded in the workbench because Dropbox blocks iframe embedding.

The current batch is mapped in:

- tools/document_triage/source_urls.json

The UI is:

- tools/document_triage/index.html

GitHub Pages deployment is:

- .github/workflows/document-triage-pages.yml

## Human-first rule

The first pass is deliberately manual:

RAW document → human document triage → ground-truth document record → later machine classifier / section parser.

No LLM suggestions are shown in this version.

## Labels

The right panel records:

- one or more document roles;
- subject / olympiad / year / stage / grades / region / tour;
- duration and maximum score;
- structural signals;
- notes;
- review status.

Labels are stored in browser localStorage and can be exported as JSONL or CSV.

## Next stage

After enough manual ground truth exists:

1. machine proposes document roles and metadata;
2. human accepts or edits;
3. machine proposes section boundaries and section types;
4. human compares against the original document;
5. type-specific extractors create Task / Answer / Criteria / Script objects.
