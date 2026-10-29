#!/usr/bin/env python3
"""One-shot targeted HTML link enumeration for 171 Russian olympiad URLs.

Append new URL observations to existing shards without rewriting the 332k index.
Build a downloader-ready, DEDUPED priority-first ordered URL manifest.
This script never fetches or saves document bodies.
"""
from __future__ import annotations
import collections
import concurrent.futures
import csv
import gzip
import hashlib
import json
import os
import re
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from crawl_links import Links, fetch_html, normalize
from link_intelligence import hint, resource_id, canonical_resource_url, likely_file

ROOT = Path(__file__).resolve().parent
SEEDS = ROOT / "targeted_seeds/olympiad_centres_ru_20261029.txt"
MAX_DEPTH = int(os.getenv("RIFT_RU_DEPTH", "6"))
PER_HOST = int(os.getenv("RIFT_RU_PAGES_PER_HOST", "32"))
WORKERS = int(os.getenv("RIFT_RU_WORKERS", "24"))
MAX_NEW_RECORDS_PER_SHARD = 100
STAMP = "ru_olympiad_20261029"
OUTPUT = ROOT / "targeted_results"
OUTPUT.mkdir(exist_ok=True, parents=True)

def host(url):
    try:
        h = (urlparse(url).hostname or "").lower().rstrip(".")
        return h.encode("idna").decode("ascii")
    except Exception:
        return ""

def is_same_host(url, h):
    t = host(url)
    return t == h or t == "www." + h or (h.startswith("www.") and t == h[4:])

def load_records(pattern):
    for fp in sorted(ROOT.glob(pattern)):
        with fp.open(encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                    if isinstance(row, dict):
                        yield row
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue

def grouped_seeds():
    groups = collections.OrderedDict()
    for line in SEEDS.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        url = normalize(line)
        if not url:
            continue
        groups.setdefault(host(url), [])
        if url not in groups[host(url)]:
            groups[host(url)].append(url)
    return groups

def scan_host(pair):
    h, roots = pair
    visited = set()
    queue = deque((r, r, 0) for r in roots)
    queued = {r for r in roots}
    output, attempts, errors = [], 0, []
    robots = {}
    def allowed(url):
        p = urlparse(url)
        origin = p.scheme + "://" + p.netloc
        if origin not in robots:
            rp = RobotFileParser()
            rp.set_url(origin + "/robots.txt")
            try:
                rp.read()
                robots[origin] = rp
            except Exception:
                robots[origin] = False
        try:
            return bool(robots[origin]) and robots[origin].can_fetch("RIFTResearchBot",url)
        except Exception:
            return False
    while queue and attempts < PER_HOST:
        url, root, depth = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        if not allowed(url):
            errors.append({"url": url, "kind": "robots_denied_or_unavailable"})
            continue
        attempts += 1
        try:
            body, error = fetch_html(url)
        except Exception as ex:
            errors.append({"url":url,"kind":type(ex).__name__})
            continue
        if error:
            errors.append({"url":url,"kind":error})
            continue
        parser = Links()
        try:
            parser.feed(body)
        except Exception as ex:
            errors.append({"url":url,"kind":"HTMLParser:"+type(ex).__name__})
            continue
        for anchor in parser.links:
            target = normalize(urljoin(url,anchor["href"]))
            if not target:
                continue
            signal = hint(target, anchor["text"],anchor["title"],anchor["heading"])
            row = {
                "id":hashlib.sha256((root+"\n"+url+"\n"+target).encode()).hexdigest()[:24],
                "url":target, "parent_url":url,"source_url":root,
                "anchor_text":anchor["text"],"title":anchor["title"],
                "heading":anchor["heading"],"resource_id":resource_id(target),
                "file_candidate":signal["file_candidate"],"type_hint":signal["type_hint"],
                "hint_evidence":signal["hint_evidence"],"heuristic_score":0,
                "classification":"unreviewed",
                "found_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "targeted_batch":STAMP
            }
            output.append(row)
            if depth < MAX_DEPTH and is_same_host(target,h) and not signal["file_candidate"]:
                if target not in queued and target not in visited:
                    if signal["priority"] >= 2:
                        queue.appendleft((target,root,depth+1))
                    else:
                        queue.append((target,root,depth+1))
                    queued.add(target)
        time.sleep(.20)
    return {"host":h,"seeds":roots,"html_attempted":attempts,"visited":len(visited),
            "pending":len(queue),"links":output,"errors":errors}

def append_shards(folder, prefix, rows):
    if not rows:
        return 0
    d = ROOT / folder
    d.mkdir(exist_ok=True)
    existing = sorted(d.glob(prefix+"*.jsonl"))
    last = int(existing[-1].stem.split("_")[-1]) if existing else 0
    n = 0
    for i in range(0,len(rows),MAX_NEW_RECORDS_PER_SHARD):
        last += 1
        target = d / (prefix + f"{last:06d}.jsonl")
        with target.open("w", encoding="utf-8") as f:
            for row in rows[i:i+MAX_NEW_RECORDS_PER_SHARD]:
                f.write(json.dumps(row,ensure_ascii=False)+"\n")
        n += 1
    return n

def main():
    groups=grouped_seeds()
    if len(groups)!=169 or sum(map(len,groups.values()))!=171:
        raise RuntimeError(f"Expected 171 URLs/169 hosts; got {sum(map(len,groups.values()))}/{len(groups)}")
    print("SEEDS",len(groups),"hosts",sum(map(len,groups.values())),"urls",flush=True)
    old_urls=[]
    known_ids=set()
    for row in load_records("resources_shards/resource_*.jsonl"):
        u = row.get("url") or ""
        rid = resource_id(u)
        if rid and rid not in known_ids:
            old_urls.append((u,bool(row.get("file_candidate") or likely_file(u,row.get("mime") or ""))))
            known_ids.add(rid)
    known_occ={r.get("id") for r in load_records("links_shards/batch_*.jsonl")}
    print("OLD",len(old_urls),"unique URL resources",len(known_occ),"observations",flush=True)
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures=[pool.submit(scan_host,p) for p in groups.items()]
        for index,f in enumerate(concurrent.futures.as_completed(futures),1):
            r=f.result()
            results.append(r)
            if index%20==0 or index==len(groups):
                print("CRAWLED",index,"/",len(groups),"hosts",flush=True)
    # Preserve original seed order in priority output; secondary within each host is traversal order.
    by_host={r["host"]:r for r in results}
    priority_urls=[]
    priority_ids=set()
    new_links=[]
    new_resources=[]
    seen_discovery=set()
    new_ids=set()
    # Include all seed URLs, even if blocked, so the user can inspect them.
    for h,roots in groups.items():
        r=by_host[h]
        for url in roots:
            rid=resource_id(url)
            if rid and rid not in priority_ids:
                priority_ids.add(rid);priority_urls.append((url,likely_file(url)))
        for row in r["links"]:
            url=row["url"]
            rid=row["resource_id"]
            if rid and rid not in priority_ids:
                priority_ids.add(rid);priority_urls.append((url,bool(row["file_candidate"])))
            if row["id"] not in known_occ and row["id"] not in seen_discovery:
                seen_discovery.add(row["id"])
                new_links.append(row)
            if rid and rid not in known_ids and rid not in new_ids:
                new_ids.add(rid)
                new_resources.append({
                    "resource_id":rid,"url":canonical_resource_url(url),
                    "first_occurrence_id":row["id"],"first_parent_url":row["parent_url"],
                    "first_source_url":row["source_url"],"anchor_text":row["anchor_text"],
                    "heading":row["heading"],"type_hint":row["type_hint"],
                    "hint_evidence":row["hint_evidence"],
                    "file_candidate":row["file_candidate"],"mime":None,
                    "review_status":"unreviewed","targeted_batch":STAMP
                })
    # Also bring previously indexed links from targeted hosts to the front.
    for url, file_flag in old_urls:
        h = host(url)
        if any(h == seedhost or h.endswith("." + seedhost) for seedhost in groups):
            rid = resource_id(url)
            if rid and rid not in priority_ids:
                priority_ids.add(rid)
                priority_urls.append((url, file_flag))
    # Download files first, without dropping non-document URL observations.
    priority_urls.sort(key=lambda entry: (not entry[1], resource_id(entry[0]) in known_ids))
    # Register seed URLs, including unreachable ones, for future monitoring.
    source_path=ROOT/"sources.jsonl"
    existing_source_urls={canonical_resource_url(s.get("url","")) for s in load_records("sources.jsonl")}
    source_added=0
    with source_path.open("a",encoding="utf-8") as f:
        for roots in groups.values():
            for url in roots:
                canon=canonical_resource_url(url)
                if canon not in existing_source_urls:
                    f.write(json.dumps({"url":url,"name":"Russian olympiad centre (targeted seed)",
                        "country":"RU","subject":"multisubject","status":"unverified",
                        "origin":"RIFT targeted Russian olympiad centres 2026-10-29",
                        "first_seen":"2026-10-29","next_action":"targeted_crawled"},ensure_ascii=False)+"\n")
                    existing_source_urls.add(canon);source_added+=1
    # The ordered downloader list is new+known target-site URLs FIRST, then rest of old index.
    # Exact resource-id duplicates are excluded. No destructive reorder of evidence shards.
    manifest_path=OUTPUT/(STAMP+"_downloader_priority_urls.txt.gz")
    file_manifest=OUTPUT/(STAMP+"_downloader_priority_documents.txt.gz")
    first_plain=OUTPUT/(STAMP+"_priority_urls.txt")
    tail_exclusions=set(priority_ids)
    all_count=0; file_count=0
    with gzip.open(manifest_path,"wt",encoding="utf-8",compresslevel=6) as f, gzip.open(file_manifest,"wt",encoding="utf-8",compresslevel=6) as ff, first_plain.open("w",encoding="utf-8") as fp:
        for url,file_candidate in priority_urls:
            fp.write(url+"\n");f.write(url+"\n");all_count+=1
            if file_candidate:ff.write(url+"\n");file_count+=1
        for url,file_candidate in old_urls:
            rid=resource_id(url)
            if rid in tail_exclusions:continue
            f.write(url+"\n");all_count+=1
            if file_candidate:ff.write(url+"\n");file_count+=1
    raw_shards_added=append_shards("links_shards","batch_",new_links)
    resource_shards_added=append_shards("resources_shards","resource_",new_resources)
    host_results=[{"host":h,"seed_urls":len(by_host[h]["seeds"]),"visited":by_host[h]["visited"],
        "html_attempted":by_host[h]["html_attempted"],"discovered_links":len(by_host[h]["links"]),
        "pending":by_host[h]["pending"],"errors":len(by_host[h]["errors"]),
        "error_samples":by_host[h]["errors"][:3]} for h in groups]
    with (OUTPUT/(STAMP+"_host_results.json")).open("w",encoding="utf-8") as f:
        json.dump(host_results,f,ensure_ascii=False,indent=2)
    result={"seed_urls":sum(map(len,groups.values())),"seed_hosts":len(groups),
        "existing_unique_resources":len(old_urls),
        "target_priority_unique_urls":len(priority_urls),
        "new_unique_resource_urls":len(new_resources),
        "new_raw_link_occurrences":len(new_links),
        "visited_html_pages":sum(r["html_attempted"] for r in results),
        "hosts_with_html":sum(r["html_attempted"]>0 for r in results),
        "hosts_with_discoveries":sum(bool(r["links"]) for r in results),
        "hosts_blocked_or_unreachable":sum(r["html_attempted"]==0 for r in results),
        "pending_targeted_pages":sum(r["pending"] for r in results),
        "new_source_registry_entries":source_added,
        "new_raw_shards":raw_shards_added,"new_resource_shards":resource_shards_added,
        "download_priority_all_count":all_count,"download_priority_file_candidate_count":file_count,
        "download_priority_manifest":str(manifest_path.relative_to(ROOT)),
        "download_file_candidate_manifest":str(file_manifest.relative_to(ROOT))}
    (OUTPUT/(STAMP+"_summary.json")).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("RU_TARGET_CRAWL_RESULT_START")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print("RU_TARGET_CRAWL_RESULT_END",flush=True)
if __name__=="__main__":
    main()
