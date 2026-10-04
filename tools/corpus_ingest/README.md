# Olympiad corpus ingestion

The corpus layer is split into two independent stages:

`crawler -> immutable RAW in Dropbox -> parser/reviewer`

The crawler does **not** parse tasks. Its job is only to discover source documents, download them safely, deduplicate them by SHA-256, preserve provenance, and maintain resumable state.

## Autonomous crawler

Control plane:

- `registry/sources.csv` — seed/archive registry kept in GitHub.
- `state/crawl_state.jsonl` — auditable document state kept in GitHub.
- `crawler.py` — stateful downloader.
- `.github/workflows/corpus-crawler.yml` — hourly + manual GitHub Actions runner.

Data plane in Dropbox:

```text
/OlympiadCorpus/
  raw/<sha-prefix>/<sha256>.<ext>
  metadata/<sha-prefix>/<sha256>.json
  state/checkpoint.jsonl
```

RAW objects are content-addressed and immutable. If five URLs contain the same bytes, one RAW object is stored and the other occurrences are marked `DUPLICATE`.

### State machine

```text
PENDING
  -> DOWNLOADING
  -> DOWNLOADED

FAILED_RETRYABLE -> retried on a later run
FAILED_TERMINAL  -> requires registry/source correction
DUPLICATE        -> points to an existing RAW object
```

Before a document is marked `DOWNLOADED`, the crawler validates HTTP success, basic file signature, computes SHA-256, uploads RAW + sidecar metadata, and confirms the RAW object exists in Dropbox.

A Dropbox checkpoint is written after each document. At the end of a GitHub Actions batch, `state/crawl_state.jsonl` is committed back to GitHub. If a runner dies mid-batch, the next run merges GitHub state with the newer Dropbox checkpoint and resumes.

### One-time Dropbox setup

Create a Dropbox API app and add these repository Actions secrets:

- `DROPBOX_APP_KEY`
- `DROPBOX_APP_SECRET`
- `DROPBOX_REFRESH_TOKEN`

The workflow uses a refresh token to obtain short-lived access tokens. No Dropbox credential is stored in the repository.

### Schedule

The workflow runs hourly at minute 17 and can also be started manually with `workflow_dispatch`.

Defaults:

- max 50 documents per run;
- max 100 MiB per single document;
- only one crawler run at a time;
- up to 5 attempts for retryable failures.

## Source registry

`registry/sources.csv` contains archive/root pages plus a few direct smoke-test documents. Archive rows are preferable: the crawler discovers concrete PDF/DOC/ZIP/audio links and records them in state.

The initial registry is intentionally English-first. Expanding it to a comprehensive multi-subject source registry is a separate research/enrichment stream and does not require changing crawler architecture.

## Existing parser prototype

The earlier parser/Human Desk prototype remains available:

```text
CSV/direct file -> local RAW -> PyMuPDF segmentation -> task candidate -> Human Desk
```

Run locally for parser experiments:

```bash
cd tools/corpus_ingest
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python corpus.py sources.example.csv --root .corpus
streamlit run review_app.py
```

The production direction is to feed the parser from Dropbox RAW instead of downloading source documents itself.
