# RIFT Downloader — 200-file pilot

## Актуальный мастер-список: строгий порядок сверху вниз

GitHub Actions **при каждом запуске** перечитывает мастер-файл ссылок из
`rift-source-index`. Новые URL, добавленные в его начало, идут первыми;
старый приоритет по доменам (`pilot_rank`) для новых запусков игнорируется.
Прошлые попытки и загруженные файлы сопоставляются по URL и SHA-256:
передвижение ссылки на другую строку **не вызывает повторной загрузки**.

При выборе `source_path=auto` загрузчик берёт первый доступный файл:

- `source_discovery/download_master.jsonl`
- `source_discovery/download_master.csv`
- `source_discovery/download_master.txt`
- если единого файла ещё нет, существующие
  `source_discovery/resources_shards/resource_*.jsonl` по порядку шарда и строки.

Путь можно переопределить в параметре `source_path` на экране
GitHub Actions или в переменной репозитория `RIFT_MASTER_PATH` для расписания.
Если явно указанный мастер-файл не найден, запуск **останавливается с ошибкой**,
не подменяя его другим индексом. Все сохранённые файлы остаются в
`RIFT/raw` (никакого `TMP`). Уже существующие 200 оригиналов
не перемещаются и не удаляются.

```bash
# Пересчитать позиции ссылок без обращений к сайтам:
python -m rift_downloader.cli --db state/rift.sqlite3 sync-master --source auto

# Найти конкретный ресурс по позиции, URL или хешу файла:
python -m rift_downloader.cli --db state/rift.sqlite3 lookup --position 1
python -m rift_downloader.cli --db state/rift.sqlite3 lookup --url 'https://example.org/tasks.pdf'
python -m rift_downloader.cli --db state/rift.sqlite3 lookup --sha256 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

Отчёт содержит `pilot_report_url_ledger.csv` с каждой обработанной ссылкой,
позицией в мастере, URL страницы-источника, результатом HTTP, ошибкой,
SHA-256, MIME, размером и идентификатором файла в Drive. Старые файлы,
которых в текущем мастер-списке нет, сохраняются в архиве и учёте,
но больше не попадают в новую очередь.


## Автоматическая работа и дашборд через GitHub Actions

**Новый режим:** [инструкция по управлению загрузчиком и настройке GitHub Actions](ACTIONS_SETUP.md).

Для пробных заданий различайте **200 URL** и **200 успешных файлов**.
Параметр `run --limit-urls 200 --queue-mode new` проверяет 200 ранее не
проверенных URL; он не обещает 200 сохранённых оригиналов.
Ошибки и повторные попытки обрабатываются отдельно, а в отчёт записываются
URL, коды HTTP, паузы, MIME и статистика Google Drive.

Генерация автономного HTML-дашборда без интернет-запросов:

```bash
python -m rift_downloader.ops_metrics --baseline \
  --output rift-dashboard.html --json rift-status.json
python -m rift_downloader.ops_metrics --db state/rift.sqlite3 \
  --output rift-dashboard.html --json rift-status.json
```

Для независимого ежедневного запуска используется отдельный
GitHub Actions workflow на ветке main, **автозагрузка по расписанию
по умолчанию выключена**. Google Drive хранит снимки SQLite, оригиналы
и результаты каждого запуска; GitHub Actions показывает сводку и
прикладывает HTML-панель. Старый Discovery не затрагивается.


## Первый запуск без VPS и OAuth — Google Colab

**[Открыть RIFT 200 File Pilot в Google Colab](https://colab.research.google.com/github/UsernameMP/English/blob/rift-source-index/rift_downloader/RIFT_200_File_Pilot.ipynb)**

Это самый простой вариант для первого эксперимента. Не требует SSH-доступа,
Google Cloud Console, OAuth client ID, refresh token и правок существующей VPS.

1. Откройте блокнот под своим Google-аккаунтом.
2. В меню Colab выберите **Среда выполнения → Выполнить все**.
3. При запросе Google подтвердите подключение Google Drive.
4. Файлы и отчёты появятся в **Мой диск / RIFT**.

Колаб выполняет код из этого GitHub-репозитория с доступом к Google Drive.
Подтверждайте запрос только при доверии этому исходному коду. Google Drive
mount предоставляет исполняемому коду широкий доступ к Диску; в рамках
нашего проекта запись ограничена папкой `RIFT`. Для 200 файлов Colab
подходит как экспериментальная среда, но **не гарантирует непрерывную работу**:
при прерывании сеанса запустите блокнот повторно. SQLite восстанавливается
из `RIFT/index`, а последние записи — из `RIFT/receipts`. Файлы
хранятся индивидуально по SHA-256 в `RIFT/raw`, а не в GitHub.

Контрольная проверка смонтированных файлов — по SHA-256 при чтении с
Google Drive mount; это **не** подтверждение ответа Drive API о завершении
облачной синхронизации. После запуска наличие файлов можно проверить в
обычном веб-интерфейсе Google Drive.

**Вариант ниже с OAuth и VPS сохранён как вариант будущей постоянной службы.**
Не следует устанавливать его на потенциально скомпрометированный сервер.


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


## Offline inventory and persistent politeness (pilot hardening)

Before any network activity, inspect an **estimate**, not verified file counts:

```bash
python -m rift_downloader.cli --db state/rift.sqlite3 plan --sample 10
```

The output uses only existing RIFT resource shard URLs and observed MIME metadata,
showing likely PDF/Word/archive/presentation/spreadsheet counts, candidate domain
distribution, and selected URL examples. No URLs are visited; unknowns remain unknown.

**Rate limits now survive worker restarts** in the `host_pacing` SQLite table.
Every attempted actual HTTP request, including `robots.txt`, redirects and final
resource responses, is recorded in `http_events`. The downloader enforces
a crawl-delay as the full minimum gap since the preceding request, not
an incremental partial delay. The fresh HTTP telemetry is exported into
`pilot_report_http_events.csv` and `pilot_report_http_hosts.csv`.
These are distinct from the per-URL `attempts` audit: one URL may issue several
HTTP requests (robots, redirects), and the exact count matters for assessing
the sites' tolerance.

A loopback HTTP fixture tests real streaming/redirect/robots handling without
requesting any public website. It is test-only and deliberately uses an
injected transport; never disable DNS checks in production.


## Preparing a representative, multi-domain 200-file pilot (October 2026)

Use the existing archive index; **do not restart Link Discovery**. The
pilot sample is deterministic, uses only original URL/MIME metadata, and
selects one likely downloadable file per source host in its first sweep,
then a second file from each host in subsequent sweeps. It is not AI
classification and never alters the original source resource shards.

```bash
# Import if not already completed:
python -m rift_downloader.cli --db state/rift.sqlite3 import \
    'source_discovery/resources_shards/resource_*.jsonl'
# Optional: create a persistent, idempotent first-5000 URL ordering offline.
python -m rift_downloader.cli --db state/rift.sqlite3 seed --limit 5000
# Check local prerequisites without any remote connections:
python -m rift_downloader.cli --db state/rift.sqlite3 doctor \
    --token /private/google_token.json --spool state/spool
# With explicit network authorization, check Drive metadata only:
python -m rift_downloader.cli --db state/rift.sqlite3 doctor \
    --token /private/google_token.json --spool state/spool --check-drive
# This does not require an OAuth token and makes zero network requests:
python -m rift_downloader.cli --db state/rift.sqlite3 run --dry-run
```

When the actual pilot starts, the program **automatically seeds the same
stable queue** if not already prepared and uses existing ranks after a
restart. The first 200 saved objects therefore tend to represent many
servers instead of an arbitrary cluster of URLs in one archive. Since
some hosts may deny access, the number of *successful* source hosts will
be measured, not assumed.

The `doctor` command reports only booleans, scope presence and disk
capacity. No token values, OAuth client identifiers or secrets are emitted.
`--check-drive` issues a single Drive metadata list request, but does
not create any file. The live downloader **refuses** a Google token that
is readable by group/other Linux users. OAuth scope must be
`https://www.googleapis.com/auth/drive.file`. Keep the token outside
the repository and back up the SQLite index to a user-owned Drive folder.
