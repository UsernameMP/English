# RIFT Downloader — 200-file pilot

Independent, resumable archive importer for existing `source_discovery/resources_shards/resource_*.jsonl`. **It never discovers new URLs and never touches the old crawler.** The pilot stops once **200 distinct original binary files** have been verified in Google Drive. Nothing is automatically downloaded during installation or import.

## Design

- SQLite WAL local ledger: source URL, progress, attempts, HTTP statuses, response times and enforced waits, SHA-256, verified Drive ID; restart recovery.
- Separate HTTP staging and Google Drive upload stages. The first pilot processes them serially (one worker, safer than three), with independent persisted states.
- Per-domain minimum 10 seconds (robots.txt fetch counts); respects robots directives/crawl delay, Retry-After and backoff after 429/5xx. No logins, proxy rotation, bypasses or flooding.
- URL/redirect screening rejects non-public IPs and non-HTTP(S) targets. DNS checked before connection. DNS pinning/TOCTOU rebinding protection is **not** implemented: deploy in a restricted egress environment for untrusted URLs.
- MIME evidence from headers/extensions/file signatures. HTML pages are deferred without storing their body. Preserves PDFs, Office, ZIP/RAR/7z, TEX and other documents as original bytes; does not extract/classify contents.
- SQLite online backup snapshots of the URL-to-Drive index are uploaded to `RIFT/index` every 25 newly verified files and again when stopping if newer entries exist. Every snapshot is SHA-256 addressed, remotely checked via size/MD5 and recorded as an index event; failure halts the pilot rather than continuing without a recoverable index.
- Content-addressed SHA-256 with Google Drive `appProperties.rift_sha256` supports deduplication after upload/DB crash. Confirms Drive size and MD5 metadata before deleting the staged file.
- Pilot hard cap: 200 **unique verified Drive objects**, not 200 inspected URLs. `--max-checks` also limits HTTP attempts.

## Installation on VPS (Python 3.11+)

```bash
git clone https://github.com/UsernameMP/English.git
cd English
git checkout rift-source-index
python3 -m venv .venv
. .venv/bin/activate
pip install -r rift_downloader/requirements.txt
python -m unittest discover -s rift_downloader/tests -v
python -m rift_downloader.cli --db state/rift.sqlite3 import 'source_discovery/resources_shards/resource_*.jsonl'
python -m rift_downloader.cli --db state/rift.sqlite3 status
```

Do not launch two concurrent workers against the same queue during this pilot. Note: the 331k link shards may make this Git checkout sizable.

## Google Drive authorization — once, requires the account owner

1. In Google Cloud Console create a project, enable Google Drive API, configure OAuth consent, and create an **OAuth Desktop Application** client. Download its JSON **to a trusted computer**, not GitHub.
2. Install the requirements on that computer and authorize in the browser:

```bash
python -m rift_downloader.auth --client-secrets /private/client_secret.json --token /private/google_token.json
```

3. Securely transfer the generated refresh token to the VPS *outside the Git worktree* (`chmod 600`). For sustained operation avoid Google OAuth external **Testing** mode refresh tokens that can expire after 7 days.
4. The app requests only the `drive.file` scope; it creates its own `RIFT/raw/00...ff` hierarchy in My Drive. Credentials belonging to the ChatGPT Google Drive connector **cannot be passed to a standalone VPS daemon**.

## Dry run and 200-file pilot

```bash
python -m rift_downloader.cli --db state/rift.sqlite3 run --token /private/google_token.json --dry-run
python -m rift_downloader.cli --db state/rift.sqlite3 run \
    --token /private/google_token.json --spool state/spool \
    --limit-success 200 --max-checks 3000 \
    --min-delay 10 --max-file-mb 100 --spool-max-gb 10 --backup-every 25
python -m rift_downloader.cli --db state/rift.sqlite3 export-report --output state/pilot_report.json
```

```bash
python -m rift_downloader.cli --db state/rift.sqlite3 pause
python -m rift_downloader.cli --db state/rift.sqlite3 resume
python -m rift_downloader.cli --db state/rift.sqlite3 recover
python -m rift_downloader.cli --db state/rift.sqlite3 status
```

The database contains HTTP attempts, wait timings, source URLs and Drive IDs; JSON report summarizes MIME, errors, codes, bytes and top domains. Upload failures leave staged original bytes on VPS and stop processing to prevent buffer exhaustion. Google Drive contains content-addressed `RIFT/raw/xx` files as well as consistent `RIFT/index` SQLite snapshots, avoiding VPS-only index dependence. Re-running `run` retries the staged upload, checking the remote hash before recreating it.

## Operating constraints

- Check website terms and local rules governing private archival. Public downloadability/robots allow does not grant redistribution rights.
- Initial concurrency is intentionally **one**. We will measure actual delays/errors before raising it.
- The 5 TB Google One capacity does not eliminate Drive API rate limits or account upload restrictions; API credentials and quotas are distinct.
- HTML and its embedded images, MathJax, OCR, archives unpacking and content classification are out of scope.
- The MVP does not create a background cron or systemd timer and does not resume discovery. Its first real run must be monitored; the 200-file cap is hard.
- Never commit OAuth secrets, refresh tokens, downloaded bodies, spool, or SQLite database to GitHub.


## VPS one-shot user service (no interference with other services)

After generating your Google Drive OAuth token on a trusted computer, place it on
the VPS **outside the Git checkout** with permissions 600. The service installer
does **not** start or schedule downloads or change system-wide services.

```bash
cd /opt/rift/English
git checkout rift-source-index
python3 -m venv .venv
.venv/bin/python -m pip install -r rift_downloader/requirements.txt
mkdir -p ~/.local/share/rift-downloader
.venv/bin/python -m rift_downloader.cli \
   --db ~/.local/share/rift-downloader/rift.sqlite3 \
   import 'source_discovery/resources_shards/resource_*.jsonl'
chmod 600 ~/.config/rift/drive-token.json
.venv/bin/python -m rift_downloader.deploy_service \
   --token ~/.config/rift/drive-token.json \
   --state-dir ~/.local/share/rift-downloader
systemctl --user daemon-reload
systemctl --user start rift-downloader-pilot.service
journalctl --user -u rift-downloader-pilot.service -f
```

The one-shot service stops after 200 successfully verified unique objects, at
the maximum-check limit, or on a controlled error. No restart policy and no
timer. The service contains paths to the private token, never its contents.
Login-session termination can stop a user service unless user lingering is
configured; only enable lingering deliberately after inspecting VPS policies.

The command `export-report` now creates an audit bundle alongside the JSON
summary: `pilot_report_manifest.csv`, `pilot_report_attempts.csv`,
`pilot_report_hosts.csv` and `pilot_report_noncompleted.csv`.
For every object: original URL, discovery source, checksum, Drive ID and MIME.
For HTTP requests: status code, enforced wait and elapsed time.
Per host: request count, average/p95/max latency, 403/429/503, retries.
Failed/deferred/blocked links remain recoverably indexed.

A Linux file lock prevents two workers using the same database concurrently;
crash recovery removes orphaned partial transfers but preserves referenced
staged bodies. Verify index backups in Google Drive before relying on them.
