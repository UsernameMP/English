#!/usr/bin/env python3
"""RIFT: resumable public HTML link inventory. Never downloads task files."""
import hashlib
import html
import json
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from link_intelligence import hint, likely_file, resource_id

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "crawl_state.json"
RAW = ROOT / "links_raw.jsonl"  # legacy staging file, migrated into readable shards
SHARDS = ROOT / "links_shards"
SHARD_ROWS = 100
SOURCES = ROOT / "sources.jsonl"
OBSERVATIONS = ROOT / "resource_observations.jsonl"
MAX_PAGES = int(os.getenv("RIFT_PAGES_PER_RUN", "60"))
PER_SITE = int(os.getenv("RIFT_PAGES_PER_SITE", "12"))
MAX_DEPTH = int(os.getenv("RIFT_MAX_DEPTH", "6"))
FILE_EXTS = (".pdf", ".doc", ".docx", ".zip", ".rar", ".7z", ".djvu",
             ".tex", ".ps", ".xls", ".xlsx", ".ppt", ".pptx", ".torrent")
KEYWORDS = ("olymp", "olimpi", "olimpí", "archive", "past", "problem",
            "solution", "answer", "exam", "contest", "math", "physics",
            "zadani", "zadání", "zadania", "provas", "gabarito", "sujet",
            "corrig", "задач", "олимпи", "решени", "задани", "архив",
            "математ", "отбор", "тур", "competition", "paper", "round")


def decode_href(value):
    """Preserve bare ampersands such as ?item=problems&section=2026 in href."""
    # html.parser unescapes semicolonless entities in attribute values:
    # '&section' otherwise turns into '§ion'.
    safe = re.sub(
        r'&(?!(?:#[0-9]+|#[xX][0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]+);)',
        '&amp;', value
    )
    return html.unescape(safe)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize(url):
    url = urldefrag(url.strip())[0]
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    return parsed._replace(scheme=parsed.scheme.lower(),
                           netloc=parsed.netloc.lower()).geturl()


def read_jsonl(path):
    if not path.exists():
        return []
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                result.append(obj)
        except json.JSONDecodeError:
            continue
    return result


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.heading = ""
        self.in_heading = False
        self.heading_parts = []
        self.anchor = None
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            # HTMLParser's attrs are already unescaped; use raw start tag.
            raw_tag = self.get_starttag_text() or ""
            found = re.search(
                r"""(?<![-\w:])href\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""",
                raw_tag, flags=re.IGNORECASE
            )
            if found:
                raw_href = next((v for v in found.groups() if v is not None), "")
                attrs["href"] = decode_href(raw_href)
        if tag in ("h1", "h2", "h3", "h4"):
            self.in_heading = True
            self.heading_parts = []
        if tag == "a" and attrs.get("href"):
            self.anchor = {"href": attrs["href"], "title": attrs.get("title", ""),
                           "text_parts": [], "heading": self.heading}

    def handle_data(self, data):
        if self.in_heading:
            self.heading_parts.append(data)
        if self.anchor is not None:
            self.anchor["text_parts"].append(data)

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4") and self.in_heading:
            self.heading = " ".join(" ".join(self.heading_parts).split())[:250]
            self.in_heading = False
        if tag == "a" and self.anchor is not None:
            a = self.anchor
            a["text"] = " ".join(" ".join(a.pop("text_parts")).split())[:250]
            self.links.append(a)
            self.anchor = None


def permitted(url, cache):
    parsed = urlparse(url)
    site = parsed.scheme + "://" + parsed.netloc
    if site not in cache:
        rp = RobotFileParser()
        rp.set_url(site + "/robots.txt")
        try:
            rp.read()
            cache[site] = rp
        except Exception:
            # Do not assume access when robots.txt cannot be checked.
            cache[site] = False
    return bool(cache[site]) and cache[site].can_fetch("RIFTResearchBot", url)


def fetch_html(url):
    # Only read response bodies when the server declares HTML.
    req = Request(url, headers={"User-Agent": "RIFTResearchBot/0.1",
                                "Accept": "text/html,application/xhtml+xml"})
    with urlopen(req, timeout=20) as resp:
        kind = resp.headers.get("Content-Type", "").lower()
        if not ("text/html" in kind or "application/xhtml" in kind):
            return None, "non-html:" + kind
        data = resp.read(2_000_001)
    if len(data) > 2_000_000:
        return None, "html-page-too-large"
    charset = "utf-8"
    m = re.search(r"charset=([A-Za-z0-9_-]+)", kind)
    if m:
        charset = m.group(1)
    return data.decode(charset, errors="replace"), None


def prioritize_queue(queue):
    """Prefer archive sections without starving peripheral navigation or large sites."""
    important, peripheral = [], []
    for task in queue:
        if task.get("priority", hint(task["url"])["priority"]) >= 2:
            important.append(task)
        else:
            peripheral.append(task)
    ordered = []
    # Four likely archive pages, one exploratory page. All pages stay queued.
    while important or peripheral:
        ordered.extend(important[:4])
        del important[:4]
        if peripheral:
            ordered.append(peripheral.pop(0))
    return ordered


def observe_mime(observations, url, mime, source_url="", parent_url=""):
    """Record MIME evidence with no binary body download."""
    rid = resource_id(url)
    if not rid or (rid, mime) in {(v["resource_id"], v["mime"]) for v in observations}:
        return
    observations.append({
        "resource_id": rid, "url": url, "mime": mime,
        "source_url": source_url, "parent_url": parent_url,
        "file_candidate": likely_file(url, mime), "observed_at": now()
    })


def main():
    sources = [s for s in read_jsonl(SOURCES) if normalize(s.get("url", ""))]
    if STATE.exists():
        state = json.loads(STATE.read_text(encoding="utf-8"))
    else:
        state = {"queue": [], "visited": [], "errors": {}, "version": 1}
    queue, visited = state["queue"], set(state["visited"])
    queued = {t["url"] for t in queue}
    for source in sources:
        u = normalize(source["url"])
        if u not in visited and u not in queued:
            queue.append({"url": u, "root": u, "depth": 0, "priority": 2})
            queued.add(u)

    # Migrate any older large single-file ledger into small connector-readable shards.
    SHARDS.mkdir(exist_ok=True)
    legacy = read_jsonl(RAW)
    shard_paths = sorted(SHARDS.glob("batch_*.jsonl"))
    seen = {row.get("id") for row in legacy}
    malformed_parents = {}
    for fp in shard_paths:
        for row in read_jsonl(fp):
            seen.add(row.get("id"))
            if "§ion" in row.get("url", "") and row.get("parent_url"):
                malformed_parents[row["parent_url"]] = row.get("source_url") or row["parent_url"]
    # One-time re-enumeration of pages with corrupted URL parameters.
    if not state.get("html_ampersand_repair_v2"):
        for parent, root in sorted(malformed_parents.items()):
            visited.discard(parent)
            if parent not in queued:
                queue.insert(0, {"url": parent, "root": root, "depth": 0})
                queued.add(parent)
        state["html_ampersand_repair_v2"] = True
        state["html_ampersand_requeued"] = len(malformed_parents)
    observations = read_jsonl(OBSERVATIONS)
    errors = state.setdefault("errors", {})
    # Backfill earlier PDF/images incorrectly counted as crawl errors.
    # They were only MIME discoveries, not parsing failures.
    for seen_url, old_error in list(errors.items()):
        if isinstance(old_error, str) and old_error.startswith("non-html:"):
            observe_mime(observations, seen_url, old_error[9:])
            del errors[seen_url]
    # Repair legacy malformed IMC URLs left in state, without deleting
    # original evidence or permanently suppressing their corrected targets.
    for broken in list(errors):
        if "imc-math.org.uk" in broken and "§ion" in broken:
            repaired = broken.replace("§ion", "&section")
            if repaired not in visited and repaired not in queued:
                queue.insert(0, {"url": repaired, "root": "https://www.imc-math.org.uk/?item=problems",
                                 "depth": 1, "priority": 2})
                queued.add(repaired)
    queue = prioritize_queue(queue)
    new = []
    per_site = defaultdict(int)
    robots = {}
    processed = 0
    stopped = []

    # Avoid dropping a slow or blocked site from the persistent frontier.
    while queue and processed < MAX_PAGES:
        task = queue.pop(0)
        url, root = task["url"], task["root"]
        if url in visited:
            continue
        host = urlparse(root).hostname or ""
        if per_site[host] >= PER_SITE:
            stopped.append(task)
            if len(stopped) >= len(queue) + 1:
                break
            continue
        per_site[host] += 1
        if urlparse(url).path.lower().endswith(FILE_EXTS):
            visited.add(url)
            continue
        if not permitted(url, robots):
            errors[url] = "robots-denied-or-unavailable"
            visited.add(url)
            continue
        try:
            html, err = fetch_html(url)
        except Exception as exc:
            n = int(errors.get(url, {}).get("tries", 0)) + 1 if isinstance(errors.get(url), dict) else 1
            errors[url] = {"tries": n, "error": type(exc).__name__}
            if n < 3:
                stopped.append(task)
            else:
                visited.add(url)
            continue
        visited.add(url)
        processed += 1
        if err is not None:
            if err.startswith("non-html:"):
                observe_mime(observations, url, err[len("non-html:"):],
                             source_url=root, parent_url=task.get("parent_url", ""))
                errors.pop(url, None)
            else:
                errors[url] = err
            continue
        parser = Links()
        parser.feed(html)
        for anchor in parser.links:
            target = normalize(urljoin(url, anchor["href"]))
            if not target:
                continue
            source_text = " ".join((anchor["text"], anchor["title"],
                                    anchor["heading"], target)).lower()
            score = sum(1 for kw in KEYWORDS if kw in source_text)
            signal = hint(target, anchor["text"], anchor["title"], anchor["heading"])
            file_link = signal["file_candidate"]
            # URLs ending in /PDF/ often redirect to a binary file; they must
            # still be HEAD/GET-header inspected rather than HTML-crawled.
            ends_in_known_extension = urlparse(target).path.lower().endswith(FILE_EXTS)
            link_id = hashlib.sha256((root + "\n" + url + "\n" + target).encode()).hexdigest()[:24]
            if link_id not in seen:
                new.append({"id": link_id, "url": target, "parent_url": url,
                            "source_url": root, "anchor_text": anchor["text"],
                            "title": anchor["title"], "heading": anchor["heading"],
                            "resource_id": resource_id(target),
                            "file_candidate": file_link, "type_hint": signal["type_hint"],
                            "hint_evidence": signal["hint_evidence"],
                            "heuristic_score": score,
                            "classification": "unreviewed",
                            "found_at": now()})
                seen.add(link_id)
            thost = urlparse(target).hostname or ""
            same_site = thost == host or thost.endswith("." + host)
            if same_site and not ends_in_known_extension and task["depth"] < MAX_DEPTH:
                if target not in visited and target not in queued:
                    queue.append({"url": target, "root": root,
                                  "parent_url": url, "priority": signal["priority"],
                                  "depth": task["depth"] + 1})
                    queued.add(target)
        time.sleep(0.25)

    queue.extend(stopped)
    # Commit-sized shards let ChatGPT fetch and classify URLs without truncation.
    # Keep EVERY raw candidate. Do not discard entries based on heuristic score.
    records = legacy + new
    if records:
        last_num = int(shard_paths[-1].stem.split("_")[-1]) if shard_paths else 0
        last_path = shard_paths[-1] if shard_paths else None
        last_count = len(read_jsonl(last_path)) if last_path else 0
        index = 0
        while index < len(records):
            if last_path is None or last_count >= SHARD_ROWS:
                last_num += 1
                last_path = SHARDS / f"batch_{last_num:06d}.jsonl"
                last_count = 0
            take = min(SHARD_ROWS - last_count, len(records) - index)
            with last_path.open("a", encoding="utf-8") as output:
                for row in records[index:index + take]:
                    output.write(json.dumps(row, ensure_ascii=False) + "\n")
            index += take
            last_count += take
        # Legacy file is emptied only after all records have been copied.
        RAW.write_text("", encoding="utf-8")
    OBSERVATIONS.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in observations),
        encoding="utf-8")
    state["queue"] = queue
    state["visited"] = sorted(visited)
    state["updated_at"] = now()
    state["last_run"] = {"html_pages": processed, "new_links": len(new),
                         "pending_pages": len(queue), "blocked_or_failed": len(errors)}
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(state["last_run"], ensure_ascii=False))


if __name__ == "__main__":
    main()
