"""Crash-tolerant SQLite ledger for the independent RIFT 200-file pilot."""
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

DDL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS resources (
 resource_id TEXT PRIMARY KEY, url TEXT NOT NULL UNIQUE,
 source_url TEXT, mime_hint TEXT, file_candidate INTEGER NOT NULL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
 next_attempt_at REAL NOT NULL DEFAULT 0, object_sha256 TEXT,
 staged_path TEXT, filename TEXT, last_error TEXT, updated_at REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS objects (
 sha256 TEXT PRIMARY KEY, size_bytes INTEGER NOT NULL, mime_type TEXT,
 drive_file_id TEXT UNIQUE, verified_at REAL
);
CREATE TABLE IF NOT EXISTS attempts (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 resource_id TEXT NOT NULL, domain TEXT, started_at REAL NOT NULL,
 elapsed_ms INTEGER, wait_ms INTEGER, http_status INTEGER, bytes_received INTEGER,
 outcome TEXT, error TEXT
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, resource_id TEXT,
 at REAL NOT NULL, kind TEXT NOT NULL, details TEXT
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS host_pacing (
  host TEXT PRIMARY KEY,
  last_request_at REAL NOT NULL DEFAULT 0,
  next_allowed_at REAL NOT NULL DEFAULT 0,
  last_updated_at REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS http_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at REAL NOT NULL,
  url TEXT NOT NULL,
  domain TEXT NOT NULL,
  purpose TEXT NOT NULL,
  http_status INTEGER,
  elapsed_ms INTEGER,
  wait_ms INTEGER
);
CREATE INDEX IF NOT EXISTS http_events_domain_idx ON http_events(domain,id);
"""

def connect(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=30,isolation_level=None)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA busy_timeout=30000')
    db.executescript(DDL)
    for table,columns in {
        'resources': {'next_attempt_at':'REAL NOT NULL DEFAULT 0','staged_path':'TEXT',
                      'filename':'TEXT','updated_at':'REAL NOT NULL DEFAULT 0',
                      'pilot_rank':'INTEGER'},
        'attempts': {'domain':'TEXT','wait_ms':'INTEGER','elapsed_ms':'INTEGER',
                    'bytes_received':'INTEGER','outcome':'TEXT','error':'TEXT'},
    }.items():
        existing={row[1] for row in db.execute(f'PRAGMA table_info({table})')}
        for col,definition in columns.items():
            if col not in existing:
                db.execute(f'ALTER TABLE {table} ADD COLUMN {col} {definition}')
    db.execute('CREATE INDEX IF NOT EXISTS resources_queue ON resources(status,next_attempt_at,file_candidate)')
    db.execute("""CREATE INDEX IF NOT EXISTS resources_pilot_pick ON resources(file_candidate DESC,resource_id)
                  WHERE status IN ('pending','retry')""")
    db.execute("""CREATE INDEX IF NOT EXISTS resources_rank_queue ON resources(pilot_rank)
                  WHERE pilot_rank IS NOT NULL AND status IN ('pending','retry')""")
    return db

def import_resources(db,rows):
    inserted=0
    db.execute('BEGIN IMMEDIATE')
    try:
        for row in rows:
            if not isinstance(row,dict) or not row.get('url') or not row.get('resource_id'):
                continue
            cursor=db.execute('''INSERT OR IGNORE INTO resources
                (resource_id,url,source_url,mime_hint,file_candidate)
                VALUES (?,?,?,?,?)''',
                (row['resource_id'],row['url'],row.get('first_source_url'),
                 row.get('mime'),int(bool(row.get('file_candidate')))))
            inserted+=cursor.rowcount
        db.execute('COMMIT')
    except BaseException:
        db.execute('ROLLBACK')
        raise
    return inserted

def claim(db,now=None):
    now=time.time() if now is None else now
    db.execute('BEGIN IMMEDIATE')
    try:
        # Prefer a prepared, domain-diversified pilot sample; unranked
        # candidates remain available if all ranked records are exhausted or
        # waiting on Retry-After. An interrupted pilot keeps the same ranks.
        row=db.execute('''SELECT resource_id FROM resources
            WHERE pilot_rank IS NOT NULL AND status IN ('pending','retry')
            AND next_attempt_at<=? ORDER BY pilot_rank LIMIT 1''',(now,)).fetchone()
        if row is None:
            row=db.execute('''SELECT resource_id FROM resources WHERE status IN ('pending','retry')
                AND next_attempt_at<=? ORDER BY file_candidate DESC,resource_id LIMIT 1''',
                (now,)).fetchone()
        if row is None:
            db.execute('COMMIT')
            return None
        db.execute('''UPDATE resources SET status='checking',attempts=attempts+1,
            updated_at=? WHERE resource_id=?''',(now,row['resource_id']))
        result=db.execute('SELECT * FROM resources WHERE resource_id=?',(row['resource_id'],)).fetchone()
        db.execute('COMMIT')
        return result
    except BaseException:
        db.execute('ROLLBACK')
        raise

def set_status(db,rid,status,*,error=None,delay=0,sha=None,path=None,filename=None):
    with db:
        db.execute('''UPDATE resources SET status=?,last_error=?,next_attempt_at=?,
            object_sha256=COALESCE(?,object_sha256),staged_path=COALESCE(?,staged_path),
            filename=COALESCE(?,filename),updated_at=? WHERE resource_id=?''',
            (status,error,time.time()+delay if delay else 0,sha,path,filename,time.time(),rid))

def begin_attempt(db,rid,domain):
    with db:
        return db.execute('INSERT INTO attempts(resource_id,domain,started_at) VALUES (?,?,?)',
                          (rid,domain,time.time())).lastrowid

def finish_attempt(db,attempt_id,*,elapsed_ms=0,wait_ms=0,code=None,size=0,outcome='',error=None):
    with db:
        db.execute('''UPDATE attempts SET elapsed_ms=?,wait_ms=?,http_status=?,bytes_received=?,
                     outcome=?,error=? WHERE id=?''',
                   (elapsed_ms,wait_ms,code,size,outcome,error,attempt_id))

def event(db,rid,kind,details=''):
    with db:
        db.execute('INSERT INTO events(resource_id,at,kind,details) VALUES (?,?,?,?)',
                   (rid,time.time(),kind,str(details)[:2000]))

def completed(db):
    return db.execute('SELECT COUNT(*) FROM objects WHERE verified_at IS NOT NULL').fetchone()[0]

def staged(db):
    return db.execute("SELECT * FROM resources WHERE status='staged' ORDER BY updated_at LIMIT 1").fetchone()

def recover(db):
    with db:
        a=db.execute("UPDATE resources SET status='pending' WHERE status IN ('checking','downloading')").rowcount
        b=db.execute("UPDATE resources SET status='staged' WHERE status='uploading'").rowcount
    return {'requeued':a,'uploads_requeued':b}

def pause(db,active):
    with db:
        db.execute("INSERT INTO settings(key,value) VALUES ('paused',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                   ('1' if active else '0',))

def is_paused(db):
    row=db.execute("SELECT value FROM settings WHERE key='paused'").fetchone()
    return row is not None and row[0]=='1'

def summary(db):
    status={r['status']:r['n'] for r in db.execute('SELECT status,COUNT(*) n FROM resources GROUP BY status')}
    http={str(r['http_status']):r['n'] for r in db.execute('SELECT http_status,COUNT(*) n FROM attempts WHERE http_status IS NOT NULL GROUP BY http_status')}
    outcomes={r['outcome']:r['n'] for r in db.execute('SELECT outcome,COUNT(*) n FROM attempts WHERE outcome IS NOT NULL GROUP BY outcome')}
    mime={r['mime_type'] or 'unknown':r['n'] for r in db.execute('SELECT mime_type,COUNT(*) n FROM objects WHERE verified_at IS NOT NULL GROUP BY mime_type')}
    domains=[dict(r) for r in db.execute('''SELECT domain,COUNT(*) requests,
      ROUND(AVG(elapsed_ms)) avg_latency_ms,ROUND(AVG(wait_ms)) avg_wait_ms,
      SUM(CASE WHEN http_status=429 THEN 1 ELSE 0 END) http_429
      FROM attempts WHERE domain IS NOT NULL GROUP BY domain ORDER BY requests DESC LIMIT 30''')]
    uploaded=db.execute('SELECT COUNT(*) n,COALESCE(SUM(size_bytes),0) bytes FROM objects WHERE verified_at IS NOT NULL').fetchone()
    physical_http=db.execute('SELECT COUNT(*) FROM http_events').fetchone()[0]
    physical_codes={str(r['http_status']):r['n'] for r in db.execute('''SELECT http_status,COUNT(*) n
        FROM http_events WHERE http_status IS NOT NULL GROUP BY http_status''')}
    robots_requests=db.execute("SELECT COUNT(*) FROM http_events WHERE purpose='robots'").fetchone()[0]
    return {'http_requests':physical_http,'http_response_codes':physical_codes,
            'robots_requests':robots_requests,
            'resource_statuses':status,'attempt_outcomes':outcomes,'http_codes':http,
            'stored_mime':mime,'top_domains':domains,'uploaded_files':uploaded['n'],
            'uploaded_bytes':uploaded['bytes'],
            'requests_attempted':db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0],
            'duplicate_links':db.execute("SELECT COUNT(*) FROM events WHERE kind='deduplicated'").fetchone()[0]}


@contextmanager
def exclusive_runner(db_path):
    """Linux VPS process-wide lock: two pilots cannot cross the 200-file cap."""
    import fcntl
    lock_path=Path(str(db_path)+'.runner.lock')
    lock_path.parent.mkdir(parents=True,exist_ok=True)
    with lock_path.open('a+') as handle:
        try:
            fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('A RIFT pilot worker is already active for this SQLite database') from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(),fcntl.LOCK_UN)

def record_http_event(db,url,domain,purpose,code,elapsed_ms,wait_ms):
    """Record each actual HTTP response, including robots.txt and redirects."""
    with db:
        db.execute('''INSERT INTO http_events
            (at,url,domain,purpose,http_status,elapsed_ms,wait_ms)
            VALUES (?,?,?,?,?,?,?)''',
            (time.time(),url,domain,purpose,code,elapsed_ms,wait_ms))
