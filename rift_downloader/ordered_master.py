"""Ordered RIFT URL master: preserve its source order across process restarts.

This importer is intentionally separate from the Discovery crawler and from
the legacy domain-diverse 200-file pilot. On EVERY GitHub Actions batch it
synchronizes the current master into the persistent SQLite ledger, preserving
previous attempts, SHA-256 objects and all previous Drive uploads by URL.
"""
import csv
import glob
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_SHARDS='source_discovery/resources_shards/resource_*.jsonl'
PREFERRED_SINGLE='source_discovery/download_master.jsonl'
PREFERRED_NAMES=(
    'source_discovery/download_master.jsonl',
    'source_discovery/download_master.csv',
    'source_discovery/download_master.txt',
)

class MasterError(ValueError):
    pass

def resolve_sources(pattern='auto'):
    """Prefer a new canonical ordered master; otherwise read the existing shards.

    A caller may override the single path/pattern explicitly. An explicit
    missing file FAILS rather than silently falling back to stale shards.
    """
    if pattern=='auto':
        for candidate in PREFERRED_NAMES:
            if Path(candidate).is_file():
                return [candidate]
        pattern=DEFAULT_SHARDS
    paths=sorted(glob.glob(pattern))
    if not paths:
        raise MasterError('Ordered URL master not found: '+str(pattern))
    if any(not Path(p).is_file() for p in paths):
        raise MasterError('Master source is not a regular file')
    return paths

def _url_row(value):
    if isinstance(value,str):
        return {'url':value}
    if isinstance(value,dict):
        key=next((name for name in ('url','URL','link','href') if isinstance(value.get(name),str)),None)
        if key is None:raise MasterError('Master record lacks URL field')
        item=dict(value)
        item['url']=item[key]
        return item
    raise MasterError('Master record must be a JSON object or URL string')

def iter_master(pattern='auto'):
    """Read JSONL, one-URL-per-line TXT, or CSV with URL header in file order."""
    for filename in resolve_sources(pattern):
        path=Path(filename)
        with path.open('r',encoding='utf-8-sig',newline='') as stream:
            if path.suffix.lower()=='.csv':
                reader=csv.DictReader(stream)
                if not reader.fieldnames or not ({'url','URL','link','href'} & set(reader.fieldnames)):
                    raise MasterError('CSV requires url, URL, link or href column: '+filename)
                for number,row in enumerate(reader,2):
                    yield number,_url_row(row)
            else:
                for number,line in enumerate(stream,1):
                    line=line.strip()
                    if not line or line.startswith('#'):continue
                    if path.suffix.lower() in ('.jsonl','.json'):
                        try: item=json.loads(line)
                        except json.JSONDecodeError as exc:
                            raise MasterError(f'{filename}:{number}: invalid JSON') from exc
                        yield number,_url_row(item)
                    else:
                        yield number,_url_row(line)

def _valid(url):
    parts=urlsplit(url)
    if parts.scheme not in ('http','https') or not parts.hostname:
        raise MasterError('Expected absolute HTTP(S) URL in master file')
    if parts.username or parts.password:
        raise MasterError('Master URL contains credentials')
    return url

def sync_ordered_master(db,pattern='auto',minimum=1):
    """Atomic full resync; earliest duplicate wins, never reset resource state.

    The raw master line order is the sole scheduling priority. Historical
    records missing from a later master are retained with position=NULL.
    The caller must hold the singleton worker lock.
    """
    files=resolve_sources(pattern)
    h=hashlib.sha256()
    seen=0
    db.execute('BEGIN IMMEDIATE')
    try:
        db.execute('''CREATE TEMP TABLE IF NOT EXISTS rift_master_stage (
              position INTEGER PRIMARY KEY,
              url TEXT NOT NULL UNIQUE,
              resource_id TEXT NOT NULL,
              source_url TEXT,
              mime_hint TEXT,
              file_candidate INTEGER NOT NULL DEFAULT 0
        )''')
        db.execute('DELETE FROM rift_master_stage')
        for line,row in iter_master(pattern):
            url=_valid(row['url'].strip())
            # For bare TXT/CSV links this ID is stable on every reordering.
            rid=row.get('resource_id') or 'url-'+hashlib.sha256(url.encode('utf-8')).hexdigest()[:32]
            if not isinstance(rid,str) or not rid:
                raise MasterError('Invalid resource_id in master')
            src=row.get('first_source_url') or row.get('source_url')
            mime=row.get('mime') or row.get('mime_hint')
            hint=bool(row.get('file_candidate'))
            cur=db.execute('''INSERT OR IGNORE INTO rift_master_stage
                (position,url,resource_id,source_url,mime_hint,file_candidate)
                VALUES (?,?,?,?,?,?)''',
                (seen+1,url,rid,src,mime,int(hint)))
            if cur.rowcount:
                seen+=1
                h.update(url.encode('utf-8'))
                h.update(b'\n')
        if seen<minimum:
            raise MasterError('Master has only '+str(seen)+' unique HTTP(S) URLs')
        # Do not overwrite history or change resource_id, even if the source
        # JSONL was regenerated with different IDs for the same URL.
        db.execute('''INSERT OR IGNORE INTO resources
              (resource_id,url,source_url,mime_hint,file_candidate)
              SELECT resource_id,url,source_url,mime_hint,file_candidate
              FROM rift_master_stage''')
        missing=db.execute('''SELECT COUNT(*) FROM rift_master_stage s
             WHERE NOT EXISTS (SELECT 1 FROM resources r WHERE r.url=s.url)''').fetchone()[0]
        if missing:
            raise MasterError(f'{missing} master URLs had conflicting resource IDs; aborting')
        db.execute('UPDATE resources SET source_position=NULL WHERE source_position IS NOT NULL')
        db.execute('''UPDATE resources
          SET source_position=(SELECT position FROM rift_master_stage WHERE url=resources.url),
              source_url=COALESCE(source_url,(SELECT source_url FROM rift_master_stage WHERE url=resources.url)),
              mime_hint=COALESCE(mime_hint,(SELECT mime_hint FROM rift_master_stage WHERE url=resources.url)),
              file_candidate=MAX(file_candidate,COALESCE((SELECT file_candidate FROM rift_master_stage WHERE url=resources.url),0))
          WHERE url IN (SELECT url FROM rift_master_stage)''')
        digest=h.hexdigest()
        db.execute('''INSERT INTO settings(key,value) VALUES ('master_sha256',?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value''',(digest,))
        db.execute('''INSERT INTO settings(key,value) VALUES ('master_rows',?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value''',(str(seen),))
        db.execute('''INSERT INTO settings(key,value) VALUES ('master_files',?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value''',(json.dumps(files),))
        db.execute('COMMIT')
    except BaseException:
        db.execute('ROLLBACK')
        raise
    first=[dict(row) for row in db.execute('''SELECT source_position,url,status,attempts
       FROM resources WHERE source_position IS NOT NULL
       ORDER BY source_position LIMIT 5''')]
    return {'master_rows':seen,'master_sha256':digest,'files':files,'first_five':first}

def lookup_resource(db,*,position=None,url=None,sha=None):
    """User-facing addressability by master line, source URL or content hash."""
    given=sum(x is not None for x in (position,url,sha))
    if given!=1:raise ValueError('Supply one of position, URL, SHA-256')
    fields='''r.resource_id,r.source_position,r.url,r.source_url,r.status,
              r.attempts,r.last_error,r.object_sha256,r.mime_hint,r.filename,
              o.size_bytes,o.mime_type,o.drive_file_id,o.verified_at'''
    join=' LEFT JOIN objects o ON r.object_sha256=o.sha256 '
    if position is not None:
        q='SELECT '+fields+' FROM resources r'+join+' WHERE r.source_position=?'
        rows=db.execute(q,(int(position),))
    elif url is not None:
        q='SELECT '+fields+' FROM resources r'+join+' WHERE r.url=?'
        rows=db.execute(q,(url,))
    else:
        q='SELECT '+fields+' FROM resources r'+join+' WHERE r.object_sha256=? ORDER BY r.source_position LIMIT 100'
        rows=db.execute(q,(sha,))
    return [dict(r) for r in rows]
