"""Portable JSON and CSV reports for RIFT's first 200-file pilot.

No network requests. Reports are generated directly from the durable SQLite
ledger; source URL provenance, per-attempt response and server pacing survive.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path
from .db import summary

def _safe(value):
    if value is None:return ''
    result=str(value)
    if result.lstrip().startswith(('=','+','-','@','\t','\r')):
        return "'"+result
    return result

def _write_csv(path,columns,rows):
    with path.open('w',encoding='utf-8',newline='') as file:
        writer=csv.writer(file)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([_safe(row[col]) for col in columns])
    return str(path)

def export_report(db,output):
    """Export summary JSON plus complete per-object/per-host request ledgers."""
    target=Path(output)
    target.parent.mkdir(parents=True,exist_ok=True)
    report=summary(db)
    data=defaultdict(list)
    for row in db.execute('''SELECT domain,elapsed_ms,wait_ms,http_status,outcome
                             FROM attempts WHERE domain IS NOT NULL ORDER BY id'''):
        data[row['domain']].append(row)
    hosts=[]
    for domain,items in sorted(data.items(),key=lambda x:(-len(x[1]),x[0])):
        elapsed=sorted(int(row['elapsed_ms'] or 0) for row in items)
        waits=[int(row['wait_ms'] or 0) for row in items]
        n=len(items)
        hosts.append({
            'domain':domain,'requests':n,
            'avg_latency_ms':round(sum(elapsed)/n),
            'p95_latency_ms':elapsed[int((n-1)*0.95)],
            'max_latency_ms':elapsed[-1],
            'avg_wait_ms':round(sum(waits)/n),
            'max_wait_ms':max(waits),
            'http_403':sum(row['http_status']==403 for row in items),
            'http_429':sum(row['http_status']==429 for row in items),
            'http_503':sum(row['http_status']==503 for row in items),
            'blocked':sum(row['outcome']=='blocked' for row in items),
            'retry':sum(row['outcome']=='retry' for row in items),
        })
    report['host_count']=len(hosts)
    report['hosts_with_429']=sum(h['http_429']>0 for h in hosts)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    stem=target.with_suffix('')
    manifest_columns=['resource_id','url','source_url','status','attempts',
                      'object_sha256','size_bytes','mime_type','drive_file_id','verified_at']
    manifest=db.execute('''SELECT r.resource_id,r.url,r.source_url,r.status,r.attempts,
         r.object_sha256,o.size_bytes,o.mime_type,o.drive_file_id,o.verified_at
         FROM resources r INNER JOIN objects o ON r.object_sha256=o.sha256
         WHERE r.status='completed' AND o.verified_at IS NOT NULL ORDER BY r.resource_id''')
    attempts_columns=['id','resource_id','domain','started_at','elapsed_ms','wait_ms',
                      'http_status','bytes_received','outcome','error']
    attempts=db.execute('''SELECT id,resource_id,domain,started_at,elapsed_ms,wait_ms,
                               http_status,bytes_received,outcome,error
                               FROM attempts ORDER BY id''')
    failures_columns=['resource_id','url','source_url','status','attempts','last_error']
    failures=db.execute('''SELECT resource_id,url,source_url,status,attempts,last_error
                           FROM resources WHERE status IN ('failed','blocked','retry','skipped','html_deferred')
                           ORDER BY status,resource_id''')
    hosts_columns=['domain','requests','avg_latency_ms','p95_latency_ms','max_latency_ms',
                   'avg_wait_ms','max_wait_ms','http_403','http_429','http_503','blocked','retry']
    return {
        'summary_json':str(target),
        'manifest_csv':_write_csv(stem.with_name(stem.name+'_manifest.csv'),manifest_columns,manifest),
        'attempts_csv':_write_csv(stem.with_name(stem.name+'_attempts.csv'),attempts_columns,attempts),
        'hosts_csv':_write_csv(stem.with_name(stem.name+'_hosts.csv'),hosts_columns,hosts),
        'noncompleted_csv':_write_csv(stem.with_name(stem.name+'_noncompleted.csv'),failures_columns,failures),
    }
