"""Offline CLI: import existing RIFT resource shards, inspect queue, recover leases."""
import argparse
import glob
import json
from .db import connect, import_resources, recover, stats

def records(patterns):
    for pattern in patterns:
        for filename in sorted(glob.glob(pattern)):
            with open(filename, encoding="utf-8") as stream:
                for line in stream:
                    if line.strip():
                        yield json.loads(line)

def main():
    parser = argparse.ArgumentParser(description="RIFT downloader pilot — offline queue operations")
    parser.add_argument("--db", default="rift_downloader.sqlite3")
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import")
    imp.add_argument("shards", nargs="+", help="Local resource_*.jsonl paths or globs")
    sub.add_parser("status")
    sub.add_parser("recover")
    args = parser.parse_args()
    db = connect(args.db)
    if args.command == "import":
        print(json.dumps({"imported": import_resources(db,records(args.shards)), "statuses": stats(db)}))
    elif args.command == "recover":
        print(json.dumps({"recovered": recover(db)}))
    else:
        print(json.dumps({"statuses":stats(db)}))

if __name__ == "__main__":
    main()
