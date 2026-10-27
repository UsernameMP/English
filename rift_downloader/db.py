"""Durable SQLite queue and content-addressed object registry."""
import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS resources (
 resource_id TEXT PRIMARY KEY, url TEXT NOT NULL UNIQUE,
 source_url TEXT, mime_hint TEXT, file_candidate INTEGER NOT NULL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'pending',
 attempts INTEGER NOT NULL DEFAULT 0,
 next_attempt_at TEXT, object_sha256 TEXT, last_error TEXT,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS resources_status_idx ON resources(status,next_attempt_at);
CREATE TABLE IF NOT EXISTS objects (
 sha256 TEXT PRIMARY KEY, size_bytes INTEGER NOT NULL, mime_type TEXT,
 drive_file_id TEXT UNIQUE, verified_at TEXT
);
CREATE TABLE IF NOT EXISTS attempts (
 id INTEGER PRIMARY KEY AUTOINCREMENT, resource_id TEXT NOT NULL,
 started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 finished_at TEXT, http_status INTEGER, elapsed_ms INTEGER,
 bytes_received INTEGER, outcome TEXT, error TEXT
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, resource_id TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 kind TEXT NOT NULL, details TEXT
);
"""
def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db

def import_resources(db, rows):
    count = 0
    with db:
        for row in rows:
            if not row.get("resource_id") or not row.get("url"):
                continue
            cursor = db.execute(
                """INSERT OR IGNORE INTO resources
                (resource_id,url,source_url,mime_hint,file_candidate)
                VALUES (?,?,?,?,?)""",
                (row["resource_id"],row["url"],row.get("first_source_url"),
                 row.get("mime"),int(bool(row.get("file_candidate")))))
            count += cursor.rowcount
    return count

def claim(db):
    """Atomically lease one pending item; interrupted leases can be recovered."""
    with db:
        row = db.execute(
            "SELECT resource_id FROM resources WHERE status='pending' ORDER BY file_candidate DESC, resource_id LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        db.execute("UPDATE resources SET status='checking', attempts=attempts+1, updated_at=CURRENT_TIMESTAMP WHERE resource_id=? AND status='pending'", (row["resource_id"],))
        return db.execute("SELECT * FROM resources WHERE resource_id=?", (row["resource_id"],)).fetchone()

def recover(db):
    with db:
        return db.execute(
            "UPDATE resources SET status='pending',updated_at=CURRENT_TIMESTAMP WHERE status='checking'"
        ).rowcount

def stats(db):
    return {r["status"]:r["n"] for r in db.execute("SELECT status,COUNT(*) n FROM resources GROUP BY status")}
