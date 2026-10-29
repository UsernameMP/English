# RIFT Downloader: GitHub Actions control center

## Operational model

The original Colab pilot scanned **328 URLs** to save **200 distinct files**.
The new system exposes two separate modes, so that mistake cannot recur.

- download-new: check exactly N previously unattempted URLs, regardless of file result.
- retry-failed: revisit at most N URLs with recoverable failures or prior attempts.
- dashboard: restore progress and generate summary WITHOUT downloading source files.
- The old 200-successful-file mode remains for compatibility with the Colab notebook.

Dashboard counters include: unique checked URLs, total URL attempts, saved
unique file hashes, bytes, http requests including robots/redirects, status
codes 403/404/429/5xx, skipped/blocked/retry, latency p95, MIME and hosts.
Generated HTML is standalone. The Actions run Summary also shows counters.
Source URLs, credentials, and file bodies are NOT included in the public
metrics file.

## Russian-first master verification

The current GitHub checkout is NOT YET confirmed to contain the newly sorted
Russian-first master list. The known original shard
`source_discovery/resources_shards/resource_000001.jsonl` starts with
`http://www.imc-math.org.uk`, not `.ru`.

Publish the corrected ordered file at
`source_discovery/download_master.jsonl` on branch `rift-source-index`,
or provide its exact relative GitHub path in the workflow `source_path`
input. Every new batch re-reads the file and follows its row order.
The new-URL GitHub runner will **refuse to download** when the first URL
has a non-Russian domain. It will report a source-priority mismatch instead
of silently crawling the old index. `dashboard` remains usable without
new source traffic, and `retry-failed` handles old retries independently.

The expected 380k+ URL master should show a Russian domain in position 1.
The dashboard displays the first actual domain, count of .ru/.рф among
the first 20 links, and a warning if the priority has not been confirmed.

## Dashboard v2

The standalone HTML report now includes vertical histograms of real daily
URL checks and saved files (7 / 14 / 30-day controls), distribution of HTTP
codes, file-format donut, status bars, per-host rejection table and archive
progress. Historical pilots without day-level data intentionally show an
empty activity graph rather than fabricated activity.

The HTML panel remains a **snapshot** generated for each workflow run;
it is saved as an Actions artifact and in the RIFT reports folder.
Refreshing a downloaded HTML file does not initiate a new GitHub Action.

## One-time setup (no VPS needed)

1. Open the default-branch GitHub workflow:
   https://github.com/UsernameMP/English/actions
   and select "RIFT Downloader Control Center" -> "Run workflow".
   Choose "dashboard" and run it: without credentials it generates an
   explicitly HISTORICAL panel, not current live monitoring.
2. To enable live download + persistent storage, authorize an OAuth
   desktop client for Drive. The GitHub runner cannot borrow your Colab
   Drive mount or the ChatGPT Drive connector.
3. SAFER: authorize a dedicated Google account, share the existing
   RIFT folder with that account as Editor, and keep other Google Drive
   files outside that account. Because the original 200 files came from
   Colab (another OAuth client), the worker needs the broader Google
   Drive scope, not merely drive.file. A normal account can be used,
   but granting Drive access to Actions is a larger security risk.
4. Create a Google Cloud OAuth Desktop Client for your own use and enable
   Google Drive API. Standard API usage is free within quota; the $300
   cloud trial and paid Colab are not requirements. Keep OAuth publishing
   status in Production for persistent refresh tokens: External/Testing
   commonly expires after seven days.
5. On a trusted computer that has Python and the RIFT repository:

       python -m pip install -r rift_downloader/requirements.txt
       python -m rift_downloader.auth --scope drive \
         --client-secrets /private/oauth-desktop-client.json \
         --token /private/rift-authorized-user.json

   Approve access in the browser. Store this file privately. NEVER paste
   a refresh token into chat, a repo file, an issue, or a workflow input.
6. In GitHub repo Settings -> Secrets and variables -> Actions, add an
   encrypted repository secret named RIFT_GOOGLE_TOKEN_JSON. Its value
   is the whole authorized-user JSON file. GitHub must be trusted with
   that token; collaborators who can alter trusted workflow code could
   misuse it. Prefer a dedicated Google account as above.
7. Run the "dashboard" operation with OAuth to confirm the 200-file
   checkpoint is accessible, followed by "download-new" with url_count 20
   as a small real trial. Review Drive reports and HTTP error counts.
8. When happy, set repository VARIABLE (not secret)
   RIFT_AUTORUN_ENABLED=true at:
   https://github.com/UsernameMP/English/settings/variables/actions
   The scheduled job then automatically checks 200 new URLs each day
   at 02:17 UTC. Set this variable to false to pause.
   The old RIFT Discovery cron remains disabled.

## Durable state and security

The workflow checks out branch rift-source-index and restores the latest
valid SHA-256 SQLite snapshot from the EXISTING Drive RIFT/index folder.
Database runs on local runner disk, never on Drive mount; after each batch
it stores a new consistent Drive index snapshot, even if all URLs fail.

Original bytes remain in RIFT/raw and are verified using Drive API.
Per-run reports are stored in RIFT/reports/actions-<run_id> and verified
by Drive metadata size and MD5. A separate HTML dashboard and aggregate
JSON are saved as GitHub Actions artifacts for 30 days. The GitHub Actions
job Summary provides counters. Source URLs and filenames are kept
inside Drive rather than published as dashboard data.

Important: Google-hosted GitHub Action jobs cannot run forever; the GitHub
Actions runner has a 6-hour maximum, this workflow has a 5-hour timeout.
Schedules can be delayed. The Google Drive OAuth credential must be valid
on every subsequent run. No automatic downloads run until
RIFT_AUTORUN_ENABLED is explicitly enabled by the owner.

Original existing Drive folder:
https://drive.google.com/drive/folders/1uyPU91NHIfIf-wGXO5UAAnNCG9CqQD1o
