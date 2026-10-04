#!/usr/bin/env python3
"""Verify or deterministically refresh catalog integrity metadata for shipping packs."""
import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSETS = ROOT / "app/src/main/assets"
CATALOG_PATH = ASSETS / "content/catalog.json"

def fail(message):
    print(f"PUBLISH ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", help="Pack ID; omit to check every catalog entry")
    parser.add_argument("--write", action="store_true", help="Update version/hash for the selected pack")
    args = parser.parse_args()
    if args.write and not args.pack:
        fail("--write requires --pack to avoid broad accidental rewrites")

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    matches = [row for row in catalog.get("packs", []) if not args.pack or row.get("id") == args.pack]
    if not matches:
        fail(f"unknown pack: {args.pack}")

    stale = []
    for row in matches:
        path = ASSETS / row.get("asset", "")
        if not path.is_file():
            fail(f"missing asset for {row.get('id')}: {path}")
        raw = path.read_bytes()
        bank = json.loads(raw.decode("utf-8"))
        if (bank.get("pack") or {}).get("id") != row.get("id"):
            fail(f"pack ID mismatch: {row.get('id')}")
        if not bank.get("content_version"):
            fail(f"content_version missing: {row.get('id')}")
        drafts = [q.get("id") for q in bank.get("questions", [])
                  if (q.get("review") or {}).get("status") != "published"]
        if drafts:
            fail(f"unpublished questions in {row.get('id')}: {', '.join(drafts[:5])}")
        digest = hashlib.sha256(raw).hexdigest()
        expected = (bank["content_version"], digest)
        actual = (row.get("content_version"), row.get("sha256"))
        if actual != expected:
            if args.write:
                row["content_version"], row["sha256"] = expected
            else:
                stale.append(row.get("id"))

    if stale:
        fail("stale catalog metadata: " + ", ".join(stale))
    if args.write:
        CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"UPDATED: {args.pack}")
    else:
        print(f"OK: {len(matches)} pack manifest(s)")

if __name__ == "__main__":
    main()
