# RIFT: link-only ingestion mode (2026-10-14)

**Active:** RIFT Link Enumeration (`.github/workflows/rift-link-enumeration.yml`).
It fetches public HTML pages to discover URLs, deduplicates them, and commits URL/resource
indices and crawler state to the **`rift-source-index` GitHub branch**. The link
index is not a raw-document archive.

**Paused:** `corpus-crawler.yml` and `corpus-parser.yml`.
Neither has a scheduled or push-triggered run. Both are manual-only with a
*double opt-in*: the workflow dispatch checkbox `enable_raw_pipeline=true`
and an explicitly configured repository variable `RIFT_ENABLE_RAW_PIPELINE=true`.
No such variable is configured by this change. Even a standalone run of either
Python entry point returns without touching Dropbox unless
`RIFT_ALLOW_RAW_INGEST=true` is deliberately provided.

Disabled RAW ingestion includes:
- Remote PDF/ZIP/MP3 downloads and RAW Dropbox uploads
- Dropbox metadata/checkpoint updates from the RAW crawler
- Dropbox parsed/candidate JSON writes and parser checkpoint updates
- Automatic chained resubmission of additional RAW or parser batches

**Historical material is preserved:** no existing Dropbox data or GitHub JSON
state is deleted, overwritten, or reclassified by this pause.

Note: `document-triage-pages.yml` is a separate manually/push-triggered reviewer
deployment that can download selected assets to GitHub Pages, **not Dropbox**.
It does not run on a schedule. It should not be confused with the active
link enumeration workflow.

To resume RAW processing later, review capacity, data rights, and storage
location first, then explicitly enable the repository variable and manually
request a batch. Do not restore cron schedules by default.
