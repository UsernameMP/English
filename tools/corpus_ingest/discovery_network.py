#!/usr/bin/env python3
"""Read-only RU Discovery Network snapshot from existing RAW crawler observations.

No crawling or OCR: this is a lossless, proof-oriented view of the current
Dropbox checkpoint and approved competition/source registry. All URL
observations survive even if year/stage/competition is unresolved.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from coverage_dashboard import (
    REGISTRY, STATE, dropbox_checkpoint, identify, read_jsonl_bytes,
    read_jsonl, merge_checkpoint_rows, validate_registry,
)

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "tools/document_triage/corpus/ru/network.json"


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}_{digest}"


def normalized_url(value: str) -> str:
    """Do not strip query params, whose values may identify real artifacts."""
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in {"https", "http"} or not parts.netloc:
        raise ValueError(f"Not HTTP(S): {value!r}")
    # Strip fragment only: HTTP never sends it to the origin.
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path,
                       parts.query, ""))


def hostname(value: str) -> str:
    return urlsplit(normalized_url(value)).hostname or ""


def build_network(registry: dict, observations: list[dict],
                  segment_id: str = "RU",
                  origin: str = "Dropbox RAW checkpoint",
                  timestamp: str | None = None) -> dict:
    validate_registry(registry)
    segments = {x["id"]: x for x in registry.get("segments", [])}
    if segment_id not in segments:
        raise ValueError(f"Unknown discovery segment: {segment_id}")
    segment = segments[segment_id]

    approved = [
        {
            "id": c["id"], "name": c["name"],
            "subject_ids": c["subject_ids"],
            "grade_min": c.get("grade_min"), "grade_max": c.get("grade_max"),
            "season_from": c.get("from"), "season_to": c.get("to"),
            "stages": c["stages"],
            "country_codes": c.get("country_codes"),  # unknown != RU by default
            "identity_status": "approved_bootstrap_registry",
        }
        for c in registry["competitions"]
        if segment_id in c.get("discovery_segment_ids", [])
    ]
    approved_ids = {x["id"] for x in approved}
    sites: dict[str, dict] = {}
    archives: dict[str, dict] = {}
    results: list[dict] = []
    assets: dict[str, dict] = {}
    seen_urls: set[str] = set()

    def register_site(url: str, from_archive: bool) -> str:
        host = hostname(url)
        sid = stable_id("site", host)
        if sid not in sites:
            sites[sid] = {
                "id": sid, "hostname": host,
                "has_archive_link": False, "observed_url_count": 0,
            }
        if from_archive:
            sites[sid]["has_archive_link"] = True
        return sid

    for cmp in registry["competitions"]:
        if cmp["id"] not in approved_ids:
            continue
        for link in cmp.get("archive_links", []):
            try:
                url = normalized_url(link["url"])
            except ValueError:
                continue
            sid = register_site(url, True)
            aid = stable_id("archive", url)
            if aid not in archives:
                archives[aid] = {
                    "id": aid, "url": url, "site_id": sid,
                    "titles": [], "competition_ids": [],
                    "state": "known_link_not_verified_as_crawled_archive",
                }
            if cmp["id"] not in archives[aid]["competition_ids"]:
                archives[aid]["competition_ids"].append(cmp["id"])
            if link["title"] not in archives[aid]["titles"]:
                archives[aid]["titles"].append(link["title"])

    for row in observations:
        raw_url = row.get("url", "")
        try:
            url = normalized_url(raw_url)
        except ValueError:
            # Preserve non-HTTP source observations rather than silently
            # losing them. The caller must retain evidence separately.
            url = raw_url.strip()
            site_id = None
        else:
            site_id = register_site(url, False)
            sites[site_id]["observed_url_count"] += 1
        doc_id = row.get("document_id") or stable_id("legacydoc", url)
        oid = stable_id("observation", f"{segment_id}|{doc_id}|{url}")
        # Existing crawler state is keyed by URL; do not drop observations
        # due to absent metadata or unrecognized competition.
        seen_urls.add(oid)
        meta = identify(row, registry) if site_id else {
            "competition_id": None, "subject_id": None, "season": None,
            "stage_id": None, "grade_band": "не указан", "role": "other",
        }
        if meta["competition_id"] not in approved_ids:
            meta["competition_id"] = None
        sha = row.get("sha256", "").lower()
        asset_id = f"sha256:{sha}" if len(sha) == 64 and all(c in "0123456789abcdef" for c in sha) else None
        if asset_id:
            if asset_id not in assets:
                assets[asset_id] = {
                    "id": asset_id, "sha256": sha,
                    "observation_ids": [], "content_type": row.get("content_type"),
                    "bytes": row.get("bytes"), "has_raw_download": False,
                }
            assets[asset_id]["observation_ids"].append(oid)
            if row.get("status") in {"DOWNLOADED", "DUPLICATE"}:
                assets[asset_id]["has_raw_download"] = True

        parent = row.get("discovered_from", "")
        parent_id = None
        if parent:
            try:
                parent = normalized_url(parent)
                parent_id = stable_id("page", parent)
                register_site(parent, False)
            except ValueError:
                pass
        results.append({
            "id": oid, "legacy_document_id": doc_id,
            "segment_id": segment_id,
            "url": url, "site_id": site_id,
            "discovered_from": parent or None,
            "source_page_id": parent_id,
            "source_id": row.get("source_id"),
            "first_seen": row.get("first_seen"),
            "last_observed_at": row.get("updated_at"),
            "fetch_status": row.get("status", "UNKNOWN"),
            "asset_id": asset_id,
            "classification": {
                "competition_id": meta["competition_id"],
                "subject_id": meta["subject_id"],
                "season": meta["season"], "stage_id": meta["stage_id"],
                "grade_band": meta["grade_band"],
                "document_role": meta["role"],
                "assertion": "legacy_source_or_filename_rule",
            },
        })

    results.sort(key=lambda x: (x["url"], x["id"]))
    assets_sorted = sorted(assets.values(), key=lambda x: x["id"])
    for asset in assets_sorted:
        asset["observation_ids"].sort()
        asset["mirror_count"] = len(asset["observation_ids"])
    unresolved = [
        row["id"] for row in results
        if any(row["classification"].get(k) is None for k in
               ("competition_id", "subject_id", "season", "stage_id"))
    ]
    statuses = Counter(x["fetch_status"] for x in results)
    return {
        "schema_version": "discovery.network.v1",
        "generated_at": timestamp or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "segment": segment,
        "origin": origin,
        "summary": {
            "url_observations": len(results),
            "unique_observation_ids": len(seen_urls),
            "unique_raw_hashes": len(assets_sorted),
            "unresolved_observations": len(unresolved),
            "statuses": dict(sorted(statuses.items())),
        },
        "approved_competitions": sorted(approved, key=lambda x: x["name"]),
        "sites": sorted(sites.values(), key=lambda x: x["hostname"]),
        "archives": sorted(archives.values(), key=lambda x: x["url"]),
        "observations": results,
        "raw_assets": assets_sorted,
        "unresolved_observation_ids": unresolved,
        "notes": {
            "ru": "RU — контур обнаружения, а не язык файла/страна хостинга.",
            "classification": "Отсутствие атрибута — неизвестно, а не отсутствие оригинала.",
            "competitions": "Справочник подтверждённых legacy-сущностей, не автоматически найденные новые олимпиады.",
            "archives": "Known archive URL из реестра не доказывает успешный обход.",
            "privacy": "Dropbox пути и токены не публикуются; публичные URL исходников сохраняются.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Discovery Network read-only RU snapshot")
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--checkpoint", type=Path, default=STATE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--segment", default="RU")
    parser.add_argument("--refresh-dropbox", action="store_true")
    args = parser.parse_args()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    content = None
    origin = str(args.checkpoint)
    if args.refresh_dropbox:
        try:
            content = dropbox_checkpoint()
            if content:
                origin = "Dropbox /OlympiadCorpus/state/checkpoint.jsonl"
        except Exception as exc:
            print(f"WARNING: Dropbox snapshot refresh failed: {exc}")
    if content is None:
        if args.checkpoint.exists() and args.checkpoint.stat().st_size:
            content = args.checkpoint.read_bytes()
        elif args.output.exists():
            print("WARNING: no live checkpoint. Retaining previous dated network snapshot.")
            return
        else:
            raise SystemExit("No checkpoint and no existing network snapshot; refusing fake zero inventory")
    # Dropbox can be full while GitHub's crawler state keeps collecting links.
    # Never let a stale Dropbox checkpoint hide these newly discovered URLs.
    rows = merge_checkpoint_rows(read_jsonl(args.checkpoint), read_jsonl_bytes(content))
    if not rows:
        raise SystemExit("Empty checkpoint: refusing to overwrite previous network view")
    if args.checkpoint.exists() and args.checkpoint.stat().st_size:
        origin += " + GitHub crawler discoveries (latest wins)"
    out = build_network(registry, rows, args.segment, origin)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Discovery {args.segment}: {len(out['observations'])} URL observations, "
          f"{len(out['raw_assets'])} SHA-256 assets, "
          f"{len(out['archives'])} known archive links, "
          f"{len(out['unresolved_observation_ids'])} unresolved")


if __name__ == "__main__":
    main()
