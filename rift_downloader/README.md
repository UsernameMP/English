# RIFT Downloader — MVP (Issue #239)

Independent offline queue foundation for a future **200 successfully uploaded files** pilot.

## Current capabilities
- Imports `source_discovery/resources_shards/resource_*.jsonl` without downloading any documents.
- SQLite WAL durable state, deduplicated `resource_id` / URL, status inspection, interrupted checking-lease recovery.
- Schema for attempts, content-hash objects and audit events.
- No downloader, Google Drive upload, OAuth, or automatic network requests implemented **yet**.

## Run
```bash
python -m rift_downloader.cli --db ./state/rift.sqlite3 import 'source_discovery/resources_shards/resource_*.jsonl'
python -m rift_downloader.cli --db ./state/rift.sqlite3 status
python -m rift_downloader.cli --db ./state/rift.sqlite3 recover
python -m unittest discover -s rift_downloader/tests -v
```

Never commit SQLite databases, credentials, downloaded files, or OAuth tokens.
The paused Discovery automation must remain paused. A future downloader must enforce robots.txt, host throttling, SSRF protections, and rights checks before any live requests.
