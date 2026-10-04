from __future__ import annotations

import argparse
import csv
import hashlib
import json
import mimetypes
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

import requests

USER_AGENT = "OlympiadCorpusCrawler/0.2 (+https://github.com/UsernameMP/English)"
SUPPORTED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".zip",
    ".mp3", ".wav", ".m4a",
    ".jpg", ".jpeg", ".png",
}
DEFAULT_DROPBOX_ROOT = "/OlympiadCorpus"
DEFAULT_DROPBOX_QUOTA_BYTES = 2 * 1024 * 1024 * 1024
DEFAULT_QUOTA_STOP_RATIO = 0.95


class QuotaLimitReached(RuntimeError):
    pass


class QuotaCheckUnavailable(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def stable_document_id(url: str) -> str:
    normalized = urldefrag(url.strip())[0]
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:20]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def guess_extension(url: str, content_type: str | None = None) -> str:
    ext = Path(urlparse(url).path).suffix.lower()
    if ext in SUPPORTED_EXTENSIONS:
        return ext
    ctype = (content_type or "").split(";", 1)[0].strip().lower()
    mapping = {
        "application/pdf": ".pdf",
        "application/zip": ".zip",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "audio/mpeg": ".mp3",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mp4": ".m4a",
        "image/jpeg": ".jpg",
        "image/png": ".png",
    }
    return mapping.get(ctype) or (mimetypes.guess_extension(ctype) if ctype else None) or ".bin"


def raw_dropbox_path(root: str, digest: str, ext: str) -> str:
    return f"{root.rstrip('/')}/raw/{digest[:2]}/{digest}{ext}"


def metadata_dropbox_path(root: str, digest: str) -> str:
    return f"{root.rstrip('/')}/metadata/{digest[:2]}/{digest}.json"


def build_quota_report(
    used: int,
    api_allocated: int,
    configured_limit: int,
    stop_ratio: float,
    incoming_bytes: int = 0,
) -> dict:
    limits = [x for x in (api_allocated, configured_limit) if x > 0]
    if not limits:
        raise ValueError("Dropbox quota is unknown")
    effective_quota = min(limits)
    threshold = int(effective_quota * stop_ratio)
    projected = used + max(0, incoming_bytes)
    return {
        "used": used,
        "api_allocated": api_allocated,
        "configured_limit": configured_limit,
        "effective_quota": effective_quota,
        "stop_ratio": stop_ratio,
        "threshold": threshold,
        "incoming_bytes": max(0, incoming_bytes),
        "projected_used": projected,
        "used_percent": round((used / effective_quota) * 100, 3),
        "projected_percent": round((projected / effective_quota) * 100, 3),
        "stop": projected >= threshold,
    }


@dataclass
class Source:
    source_id: str
    name: str
    url: str
    subject: str = ""
    source_type: str = "archive"
    adapter: str = "html_links"
    year_from: str = ""
    year_to: str = ""
    grades: str = ""
    geography: str = ""
    olympiad: str = ""
    stage: str = ""
    enabled: str = "true"
    priority: str = "100"
    max_depth: str = "1"
    crawl_regex: str = ""
    include_regex: str = ""
    exclude_regex: str = ""
    rights_note: str = ""

    @property
    def is_enabled(self) -> bool:
        return self.enabled.lower() not in {"0", "false", "no", "off"}

    @property
    def priority_int(self) -> int:
        try:
            return int(self.priority)
        except ValueError:
            return 100

    @property
    def max_depth_int(self) -> int:
        try:
            return max(0, min(int(self.max_depth), 4))
        except ValueError:
            return 1


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs) -> None:
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


def parse_links(html: str, base_url: str) -> list[str]:
    parser = LinkParser()
    parser.feed(html)
    out, seen = [], set()
    for href in parser.hrefs:
        url = urldefrag(urljoin(base_url, href))[0]
        if url.startswith(("http://", "https://")) and url not in seen:
            seen.add(url)
            out.append(url)
    return out


def looks_like_document(url: str) -> bool:
    return Path(urlparse(url).path).suffix.lower() in SUPPORTED_EXTENSIONS


def allowed_by_patterns(url: str, include_regex: str, exclude_regex: str) -> bool:
    if include_regex and not re.search(include_regex, url, re.I):
        return False
    if exclude_regex and re.search(exclude_regex, url, re.I):
        return False
    return True


def should_crawl_page(source: Source, url: str) -> bool:
    if looks_like_document(url):
        return False
    if urlparse(url).netloc.lower() != urlparse(source.url).netloc.lower():
        return False
    if source.crawl_regex:
        return bool(re.search(source.crawl_regex, url, re.I))
    prefix = urlparse(source.url).path.rstrip("/")
    return urlparse(url).path.startswith(prefix)


def read_sources(path: Path) -> list[Source]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    fields = Source.__annotations__.keys()
    result = []
    for row in rows:
        data = {k: (row.get(k) or "").strip() for k in fields}
        if data["source_id"] and data["url"]:
            result.append(Source(**data))
    return result


def load_state(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            out[item["document_id"]] = item
    return out


def save_state(path: Path, state: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(state.values(), key=lambda x: (x.get("source_id", ""), x.get("url", "")))
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        for item in ordered:
            f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(path)


def merge_states(a: dict[str, dict], b: dict[str, dict]) -> dict[str, dict]:
    merged = dict(a)
    for key, item in b.items():
        old = merged.get(key)
        if old is None or item.get("updated_at", "") >= old.get("updated_at", ""):
            merged[key] = item
    return merged


def normalize_refresh_token(value: str) -> str:
    """Accept the raw refresh token plus common copy/paste wrappers."""
    raw = value.strip()
    if not raw:
        return raw

    if raw.startswith("{") and raw.endswith("}"):
        try:
            payload = json.loads(raw)
            token = payload.get("refresh_token")
            if isinstance(token, str) and token.strip():
                raw = token.strip()
        except json.JSONDecodeError:
            pass

    match = re.match(r"(?is)^refresh_token\s*[:=]\s*(.+)$", raw)
    if match:
        raw = match.group(1).strip()

    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        raw = raw[1:-1].strip()

    return raw


class DropboxClient:
    def __init__(self, app_key: str, app_secret: str, refresh_token: str, root: str) -> None:
        self.app_key = app_key
        self.app_secret = app_secret
        self.refresh_token = normalize_refresh_token(refresh_token)
        self.root = root.rstrip("/") or DEFAULT_DROPBOX_ROOT
        self.http = requests.Session()
        self.access_token: str | None = None

    def token(self) -> str:
        if self.access_token:
            return self.access_token
        r = self.http.post(
            "https://api.dropboxapi.com/oauth2/token",
            data={"grant_type": "refresh_token", "refresh_token": self.refresh_token},
            auth=(self.app_key, self.app_secret),
            timeout=30,
        )
        if not r.ok:
            try:
                detail = r.json()
            except Exception:
                detail = {"body": r.text[:500]}
            safe_detail = {
                k: v for k, v in detail.items()
                if k not in {"access_token", "refresh_token", "token", "client_secret"}
            }
            if detail.get("error") == "invalid_grant" and "refresh token is malformed" in str(detail.get("error_description", "")).lower():
                raise RuntimeError(
                    "Dropbox rejected DROPBOX_REFRESH_TOKEN as malformed. "
                    "The GitHub secret must contain the refresh_token value returned by the OAuth token exchange, "
                    "not the authorization code, access_token, app secret, or curl command."
                )
            raise RuntimeError(
                f"Dropbox OAuth token exchange failed: HTTP {r.status_code}: "
                f"{json.dumps(safe_detail, ensure_ascii=False)}"
            )
        self.access_token = r.json()["access_token"]
        return self.access_token

    def api_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token()}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _raise_dropbox_error(response: requests.Response, operation: str) -> None:
        if response.ok:
            return
        body = response.text[:1200]
        request_id = response.headers.get("x-dropbox-request-id", "")
        raise RuntimeError(
            f"Dropbox API {operation} failed: HTTP {response.status_code}; "
            f"request_id={request_id or 'n/a'}; body={body}"
        )

    def ensure_folder(self, path: str) -> None:
        current = ""
        for part in [p for p in path.split("/") if p]:
            current += "/" + part
            r = self.http.post(
                "https://api.dropboxapi.com/2/files/create_folder_v2",
                headers=self.api_headers(),
                json={"path": current, "autorename": False},
                timeout=30,
            )
            if r.status_code == 409 and "conflict" in r.text:
                continue
            r.raise_for_status()

    def upload_bytes(self, path: str, data: bytes, overwrite: bool = False) -> dict:
        self.ensure_folder(str(Path(path).parent).replace("\\", "/"))
        headers = {
            "Authorization": f"Bearer {self.token()}",
            "Content-Type": "application/octet-stream",
            "Dropbox-API-Arg": json.dumps({
                "path": path,
                "mode": "overwrite" if overwrite else "add",
                "autorename": False,
                "mute": True,
                "strict_conflict": True,
            }),
        }
        r = self.http.post(
            "https://content.dropboxapi.com/2/files/upload",
            headers=headers,
            data=data,
            timeout=120,
        )
        if r.status_code == 409 and not overwrite:
            return {"path_display": path, "existing": True}
        r.raise_for_status()
        return r.json()

    def download_bytes(self, path: str) -> bytes | None:
        headers = {
            "Authorization": f"Bearer {self.token()}",
            "Dropbox-API-Arg": json.dumps({"path": path}),
        }
        r = self.http.post(
            "https://content.dropboxapi.com/2/files/download",
            headers=headers,
            timeout=60,
        )
        if r.status_code == 409:
            return None
        self._raise_dropbox_error(r, "files/download")
        return r.content

    def exists(self, path: str) -> bool:
        r = self.http.post(
            "https://api.dropboxapi.com/2/files/get_metadata",
            headers=self.api_headers(),
            json={"path": path, "include_deleted": False},
            timeout=30,
        )
        if r.status_code == 409:
            return False
        self._raise_dropbox_error(r, "files/get_metadata")
        return True

    def get_space_usage(self) -> dict[str, int]:
        r = self.http.post(
            "https://api.dropboxapi.com/2/users/get_space_usage",
            headers=self.api_headers(),
            data="null",
            timeout=30,
        )
        self._raise_dropbox_error(r, "users/get_space_usage")
        payload = r.json()
        allocation = payload.get("allocation") or {}
        allocated = int(allocation.get("allocated") or 0)
        return {"used": int(payload.get("used") or 0), "allocated": allocated}

    def checkpoint_path(self) -> str:
        return f"{self.root}/state/checkpoint.jsonl"

    def upload_checkpoint(self, state: dict[str, dict]) -> None:
        payload = "".join(
            json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n"
            for x in sorted(state.values(), key=lambda r: (r.get("source_id", ""), r.get("url", "")))
        ).encode("utf-8")
        self.upload_bytes(self.checkpoint_path(), payload, overwrite=True)

    def load_checkpoint(self) -> dict[str, dict]:
        path = self.checkpoint_path()
        # First run is expected to have no Dropbox checkpoint yet.
        # Check metadata first instead of calling /files/download on a missing path.
        if not self.exists(path):
            return {}
        data = self.download_bytes(path)
        if not data:
            return {}
        out = {}
        for line in data.decode("utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                out[item["document_id"]] = item
        return out


class Crawler:
    def __init__(
        self,
        sources: list[Source],
        state: dict[str, dict],
        dbx: DropboxClient,
        max_bytes: int,
        quota_bytes: int = DEFAULT_DROPBOX_QUOTA_BYTES,
        quota_stop_ratio: float = DEFAULT_QUOTA_STOP_RATIO,
    ) -> None:
        self.sources = [s for s in sources if s.is_enabled]
        self.source_by_id = {s.source_id: s for s in self.sources}
        self.state = state
        self.dbx = dbx
        self.max_bytes = max_bytes
        self.quota_bytes = quota_bytes
        self.quota_stop_ratio = quota_stop_ratio
        self.last_quota: dict | None = None
        self.quota_warning = ""
        self.http = requests.Session()
        self.http.headers.update({"User-Agent": USER_AGENT})

    def enforce_quota(self, incoming_bytes: int = 0) -> dict:
        try:
            usage = self.dbx.get_space_usage()
        except Exception as exc:
            raise QuotaCheckUnavailable(
                "Dropbox quota check failed; downloads stopped fail-safe: " + str(exc)
            ) from exc
        report = build_quota_report(
            usage["used"],
            usage.get("allocated", 0),
            self.quota_bytes,
            self.quota_stop_ratio,
            incoming_bytes,
        )
        self.last_quota = report
        if report["stop"]:
            raise QuotaLimitReached(
                "Dropbox quota guard: stopping before 95% limit "
                f"(used={report['used']} bytes, incoming={report['incoming_bytes']} bytes, "
                f"projected={report['projected_percent']}%, threshold={self.quota_stop_ratio * 100:.1f}%, "
                f"effective_quota={report['effective_quota']} bytes)."
            )
        return report

    def record_discovery(self, source: Source, url: str, discovered_from: str) -> None:
        doc_id = stable_document_id(url)
        if doc_id in self.state:
            return
        now = utc_now()
        self.state[doc_id] = {
            "document_id": doc_id,
            "source_id": source.source_id,
            "url": url,
            "discovered_from": discovered_from,
            "status": "PENDING",
            "attempts": 0,
            "sha256": "",
            "dropbox_path": "",
            "content_type": "",
            "bytes": 0,
            "http_status": 0,
            "first_seen": now,
            "updated_at": now,
            "last_error": "",
        }

    def discover_source(self, source: Source) -> tuple[int, str | None]:
        before = len(self.state)
        if source.source_type == "document" or source.adapter == "direct" or looks_like_document(source.url):
            self.record_discovery(source, source.url, source.url)
            return len(self.state) - before, None

        queue = [(source.url, 0)]
        visited = set()
        try:
            while queue:
                page_url, depth = queue.pop(0)
                if page_url in visited or depth > source.max_depth_int:
                    continue
                visited.add(page_url)
                r = self.http.get(page_url, timeout=45)
                r.raise_for_status()
                for link in parse_links(r.text, page_url):
                    if looks_like_document(link):
                        if allowed_by_patterns(link, source.include_regex, source.exclude_regex):
                            self.record_discovery(source, link, page_url)
                    elif depth < source.max_depth_int and should_crawl_page(source, link):
                        queue.append((link, depth + 1))
            return len(self.state) - before, None
        except Exception as exc:
            return len(self.state) - before, str(exc)

    def discover_all(self) -> list[dict]:
        report = []
        for source in sorted(self.sources, key=lambda s: (-s.priority_int, s.source_id)):
            new, error = self.discover_source(source)
            report.append({"source_id": source.source_id, "new": new, "error": error})
        return report

    def validate(self, data: bytes, ext: str, content_type: str) -> str | None:
        if not data:
            return "empty_body"
        if len(data) > self.max_bytes:
            return "file_too_large"
        if ext == ".pdf" and not data.startswith(b"%PDF-"):
            return "invalid_pdf_magic"
        if ext == ".zip" and not data.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
            return "invalid_zip_magic"
        if "text/html" in content_type.lower() and ext in {".pdf", ".doc", ".docx", ".zip"}:
            return "html_instead_of_document"
        return None

    def make_metadata(self, rec: dict, digest: str, ext: str, raw_path: str, response: requests.Response) -> dict:
        source = self.source_by_id.get(rec["source_id"])
        return {
            "schema_version": 1,
            "sha256": digest,
            "raw_path": raw_path,
            "source_id": rec["source_id"],
            "source": asdict(source) if source else None,
            "original_url": rec["url"],
            "discovered_from": rec.get("discovered_from", ""),
            "extension": ext,
            "content_type": response.headers.get("content-type", ""),
            "bytes": len(response.content),
            "etag": response.headers.get("etag", ""),
            "last_modified": response.headers.get("last-modified", ""),
            "downloaded_at": utc_now(),
            "crawler_version": "0.2",
        }

    def process_one(self, rec: dict) -> None:
        rec["status"] = "DOWNLOADING"
        rec["attempts"] = int(rec.get("attempts", 0)) + 1
        rec["updated_at"] = utc_now()
        self.dbx.upload_checkpoint(self.state)
        try:
            r = self.http.get(rec["url"], timeout=90, allow_redirects=True)
            rec["http_status"] = r.status_code
            r.raise_for_status()
            ctype = r.headers.get("content-type", "")
            ext = guess_extension(r.url, ctype)
            error = self.validate(r.content, ext, ctype)
            if error:
                raise ValueError(error)

            digest = sha256_bytes(r.content)
            existing = next((
                x for x in self.state.values()
                if x.get("document_id") != rec["document_id"]
                and x.get("sha256") == digest
                and x.get("status") in {"DOWNLOADED", "DUPLICATE"}
            ), None)
            if existing:
                rec.update({
                    "status": "DUPLICATE",
                    "sha256": digest,
                    "dropbox_path": existing.get("dropbox_path", ""),
                    "content_type": ctype,
                    "bytes": len(r.content),
                    "updated_at": utc_now(),
                    "last_error": "",
                })
                return

            self.enforce_quota(len(r.content))
            raw_path = raw_dropbox_path(self.dbx.root, digest, ext)
            self.dbx.upload_bytes(raw_path, r.content, overwrite=False)
            metadata = self.make_metadata(rec, digest, ext, raw_path, r)
            self.dbx.upload_bytes(
                metadata_dropbox_path(self.dbx.root, digest),
                json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"),
                overwrite=False,
            )
            if not self.dbx.exists(raw_path):
                raise RuntimeError("dropbox_raw_verification_failed")

            rec.update({
                "status": "DOWNLOADED",
                "sha256": digest,
                "dropbox_path": raw_path,
                "content_type": ctype,
                "bytes": len(r.content),
                "updated_at": utc_now(),
                "last_error": "",
            })
        except (QuotaLimitReached, QuotaCheckUnavailable) as exc:
            rec["status"] = "PENDING"
            rec["attempts"] = max(0, int(rec.get("attempts", 1)) - 1)
            rec["last_error"] = str(exc)[:800]
            rec["updated_at"] = utc_now()
            self.quota_warning = str(exc)
            raise
        except requests.HTTPError as exc:
            code = getattr(exc.response, "status_code", 0) or 0
            rec["status"] = "FAILED_TERMINAL" if code in {401, 403, 404, 410} else "FAILED_RETRYABLE"
            rec["last_error"] = f"HTTP {code}: {exc}"
            rec["updated_at"] = utc_now()
        except Exception as exc:
            attempts = int(rec.get("attempts", 0))
            terminal = attempts >= 5 or str(exc) in {"file_too_large", "invalid_pdf_magic", "invalid_zip_magic"}
            rec["status"] = "FAILED_TERMINAL" if terminal else "FAILED_RETRYABLE"
            rec["last_error"] = str(exc)[:800]
            rec["updated_at"] = utc_now()
        finally:
            self.dbx.upload_checkpoint(self.state)

    def process_batch(self, limit: int) -> int:
        try:
            self.enforce_quota(0)
        except (QuotaLimitReached, QuotaCheckUnavailable) as exc:
            self.quota_warning = str(exc)
            print(f"::warning::{self.quota_warning}")
            return 0

        eligible = [
            r for r in self.state.values()
            if r.get("status") in {"PENDING", "FAILED_RETRYABLE", "CLAIMED", "DOWNLOADING"}
            and int(r.get("attempts", 0)) < 5
        ]
        eligible.sort(key=lambda r: (
            -self.source_by_id.get(r.get("source_id", ""), Source("", "", "")).priority_int,
            int(r.get("attempts", 0)),
            r.get("first_seen", ""),
        ))
        processed = 0
        for rec in eligible[:limit]:
            try:
                self.process_one(rec)
                processed += 1
            except (QuotaLimitReached, QuotaCheckUnavailable) as exc:
                self.quota_warning = str(exc)
                print(f"::warning::{self.quota_warning}")
                break
        return processed


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def status_summary(state: dict[str, dict]) -> dict[str, int]:
    out = {}
    for item in state.values():
        status = item.get("status", "UNKNOWN")
        out[status] = out.get(status, 0) + 1
    return dict(sorted(out.items()))


def main() -> None:
    p = argparse.ArgumentParser(description="Stateful olympiad archive crawler -> Dropbox RAW")
    p.add_argument("--sources", type=Path, default=Path("registry/sources.csv"))
    p.add_argument("--state", type=Path, default=Path("state/crawl_state.jsonl"))
    p.add_argument("--max-documents", type=int, default=int(os.getenv("MAX_DOCUMENTS", "50")))
    p.add_argument("--max-bytes", type=int, default=int(os.getenv("MAX_FILE_BYTES", str(100 * 1024 * 1024))))
    p.add_argument("--quota-bytes", type=int, default=int(os.getenv("DROPBOX_QUOTA_BYTES", str(DEFAULT_DROPBOX_QUOTA_BYTES))))
    p.add_argument("--quota-stop-ratio", type=float, default=float(os.getenv("DROPBOX_STOP_AT_RATIO", str(DEFAULT_QUOTA_STOP_RATIO))))
    args = p.parse_args()
    if not 0 < args.quota_stop_ratio < 1:
        raise SystemExit("--quota-stop-ratio must be between 0 and 1")

    dbx = DropboxClient(
        require_env("DROPBOX_APP_KEY"),
        require_env("DROPBOX_APP_SECRET"),
        require_env("DROPBOX_REFRESH_TOKEN"),
        os.getenv("DROPBOX_ROOT", DEFAULT_DROPBOX_ROOT),
    )
    github_state = load_state(args.state)
    dropbox_state = dbx.load_checkpoint()
    state = merge_states(github_state, dropbox_state)

    crawler = Crawler(
        read_sources(args.sources),
        state,
        dbx,
        args.max_bytes,
        quota_bytes=args.quota_bytes,
        quota_stop_ratio=args.quota_stop_ratio,
    )
    try:
        crawler.enforce_quota(0)
    except (QuotaLimitReached, QuotaCheckUnavailable) as exc:
        crawler.quota_warning = str(exc)
        print(f"::warning::{crawler.quota_warning}")
        discovery = []
        processed = 0
    else:
        discovery = crawler.discover_all()
        dbx.upload_checkpoint(state)
        processed = crawler.process_batch(max(0, args.max_documents))
    save_state(args.state, state)

    summary = {
        "discovery": discovery,
        "processed": processed,
        "status": status_summary(state),
        "quota": crawler.last_quota,
        "warning": crawler.quota_warning or None,
    }
    remaining = sum(
        count for status, count in summary["status"].items()
        if status in {"PENDING", "FAILED_RETRYABLE", "CLAIMED", "DOWNLOADING"}
    )
    summary["remaining"] = remaining
    summary["should_continue"] = bool(
        remaining > 0 and processed > 0 and not crawler.quota_warning
    )
    Path("run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
