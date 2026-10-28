"""Deterministic, domain-diversified selection of file URL candidates.

Only existing RIFT index metadata is read: no HTTP calls or model judgments.
The first pass picks one likely document per host before taking any second
file from a host, so a 200-file pilot tests different servers and formats.
"""
import hashlib
from collections import defaultdict, deque
from urllib.parse import urlparse

from .inventory import predicted_type

FILE_GROUPS = frozenset(('pdf','word','archive','presentation','spreadsheet','other_document'))
KIND_ORDER = {'archive':0,'word':1,'spreadsheet':2,'presentation':3,
              'other_document':4,'pdf':5,'unknown':6}

def _host_order(host):
    # Stable across Python restarts (unlike randomized built-in hash).
    return hashlib.blake2b(host.encode('utf-8'),digest_size=8).hexdigest()

def seed_pilot(db,limit=5000):
    """Assign permanent ranks for up to limit candidate URLs.

    Idempotent: existing non-empty assignments are never overwritten on
    restart. Domain rotation is deterministic and does not require loading
    document bodies or visiting websites.
    """
    if limit<1:raise ValueError('pilot seed limit must be positive')
    existing=db.execute('SELECT COUNT(*) FROM resources WHERE pilot_rank IS NOT NULL').fetchone()[0]
    if existing:
        return {'seeded':existing,'existing':True}
    groups=defaultdict(list)
    for row in db.execute("""SELECT resource_id,url,mime_hint,file_candidate
                             FROM resources WHERE status IN ('pending','retry')"""):
        host=urlparse(row['url']).hostname
        if not host:continue
        group=predicted_type(row['url'],row['mime_hint'])
        if not row['file_candidate'] and group not in FILE_GROUPS:
            continue
        score=(0 if row['mime_hint'] and group in FILE_GROUPS else 1,
               KIND_ORDER.get(group,7),row['resource_id'])
        groups[host.lower()].append((score,row['resource_id']))
    if not groups:return {'seeded':0,'hosts':0,'existing':False}
    # Sort within each host so existing MIME evidence and diverse file formats
    # appear early, but do not suppress any original resource.
    queues={host:deque(rid for _,rid in sorted(rows))
            for host,rows in groups.items()}
    domain_order=sorted(queues,key=_host_order)
    ranks=[]
    while len(ranks)<limit:
        any_taken=False
        for host in domain_order:
            if len(ranks)>=limit:break
            if queues[host]:
                ranks.append(queues[host].popleft())
                any_taken=True
        if not any_taken:break
    db.execute('BEGIN IMMEDIATE')
    try:
        for index,rid in enumerate(ranks,1):
            db.execute('UPDATE resources SET pilot_rank=? WHERE resource_id=? AND pilot_rank IS NULL',
                       (index,rid))
        db.execute('COMMIT')
    except BaseException:
        db.execute('ROLLBACK')
        raise
    return {'seeded':len(ranks),'hosts':len(groups),
            'first_sweep_hosts':min(len(ranks),len(groups)), 'existing':False}
