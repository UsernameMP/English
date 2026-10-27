"""Offline and live commands for the separate RIFT downloader pilot."""
import argparse
import glob
import json
import random
import shutil
import time
from pathlib import Path
from urllib.parse import urlparse
from .db import (connect,import_resources,claim,recover,set_status,begin_attempt,
                 finish_attempt,event,completed,staged,pause,is_paused,summary)
from .http import PoliteHttp

def records(patterns):
    for pattern in patterns:
        for filename in sorted(glob.glob(pattern)):
            with open(filename,encoding='utf-8') as stream:
                for number,line in enumerate(stream,1):
                    if line.strip():
                        try:yield json.loads(line)
                        except json.JSONDecodeError as exc:
                            raise ValueError(f'{filename}:{number}: {exc}') from exc

def upload_one(db,uploader,row):
    sha=row['object_sha256'];path=Path(row['staged_path'] or '')
    obj=db.execute('SELECT * FROM objects WHERE sha256=? AND verified_at IS NOT NULL',(sha,)).fetchone()
    if obj:
        set_status(db,row['resource_id'],'completed')
        event(db,row['resource_id'],'deduplicated',sha)
        if path.is_file():path.unlink(missing_ok=True)
        return True
    if not sha or not path.is_file():
        set_status(db,row['resource_id'],'failed',error='staged body missing; kept record for investigation')
        return False
    set_status(db,row['resource_id'],'uploading')
    try:
        file_id=uploader.upload(sha,path,row['mime_hint'] or 'application/octet-stream',row['filename'])
        with db:
            db.execute('''INSERT INTO objects(sha256,size_bytes,mime_type,drive_file_id,verified_at)
                VALUES (?,?,?,?,?) ON CONFLICT(sha256) DO UPDATE SET
                drive_file_id=excluded.drive_file_id,verified_at=excluded.verified_at''',
                (sha,path.stat().st_size,row['mime_hint'],file_id,time.time()))
        set_status(db,row['resource_id'],'completed')
        event(db,row['resource_id'],'drive_verified',file_id)
        path.unlink(missing_ok=True)
        return True
    except Exception as exc:
        set_status(db,row['resource_id'],'staged',error=str(exc)[:300])
        event(db,row['resource_id'],'upload_error',str(exc))
        return False

def run_pilot(db,args,uploader,worker=None):
    recover(db)
    worker=worker or PoliteHttp(delay=args.min_delay,max_bytes=args.max_file_mb*1024*1024)
    spool=Path(args.spool);spool.mkdir(parents=True,exist_ok=True)
    checks=0
    while completed(db)<args.limit_success:
        if is_paused(db):return 'paused'
        row=staged(db)
        if row:
            if not upload_one(db,uploader,row):return 'upload_error'
            continue
        if checks>=args.max_checks:return 'max_checks'
        used=sum(p.stat().st_size for p in spool.iterdir() if p.is_file())
        if used>=args.spool_max_gb*1024**3 or shutil.disk_usage(spool).free<max(1024**3,args.max_file_mb*1024**2):
            return 'spool_capacity'
        row=claim(db)
        if row is None:return 'queue_empty_or_retry_later'
        checks+=1
        rid=row['resource_id'];domain=urlparse(row['url']).hostname
        attempt=begin_attempt(db,rid,domain)
        result=worker.fetch(row['url'],spool)
        outcome=result['outcome']
        finish_attempt(db,attempt,elapsed_ms=result.get('elapsed_ms',0),
                       wait_ms=result.get('wait_ms',0),code=result.get('http_status'),
                       size=result.get('bytes_received',0),outcome=outcome,error=result.get('error'))
        if outcome=='staged':
            with db:
                db.execute('UPDATE resources SET mime_hint=? WHERE resource_id=?',(result['mime'],rid))
            set_status(db,rid,'staged',sha=result['sha256'],path=result['path'],filename=result['filename'])
        elif outcome=='retry':
            count=row['attempts']
            if count>=args.max_retries:set_status(db,rid,'failed',error=result.get('error'))
            else:
                seconds=max(float(result.get('retry_after') or 0),min(3600,2**min(count,10)+random.uniform(0,1)))
                set_status(db,rid,'retry',delay=seconds,error=result.get('error'))
        else:set_status(db,rid,outcome,error=result.get('error'))
    return 'limit_reached'

def main(argv=None):
    parser=argparse.ArgumentParser(description='RIFT file pilot: exactly 200 verified unique Drive objects')
    parser.add_argument('--db',default='state/rift.sqlite3')
    sub=parser.add_subparsers(dest='command',required=True)
    imp=sub.add_parser('import');imp.add_argument('shards',nargs='+')
    sub.add_parser('status');sub.add_parser('recover');sub.add_parser('pause');sub.add_parser('resume')
    report=sub.add_parser('export-report');report.add_argument('--output',required=True)
    run=sub.add_parser('run');run.add_argument('--token',required=True)
    run.add_argument('--spool',default='state/spool');run.add_argument('--limit-success',type=int,default=200)
    run.add_argument('--max-checks',type=int,default=3000)
    run.add_argument('--min-delay',type=float,default=10.0)
    run.add_argument('--max-file-mb',type=int,default=100)
    run.add_argument('--spool-max-gb',type=int,default=10)
    run.add_argument('--max-retries',type=int,default=4)
    run.add_argument('--dry-run',action='store_true')
    args=parser.parse_args(argv)
    db=connect(args.db)
    if args.command=='import':result={'imported':import_resources(db,records(args.shards)),'report':summary(db)}
    elif args.command=='status':result=summary(db)
    elif args.command=='recover':result=recover(db)
    elif args.command in ('pause','resume'):
        pause(db,args.command=='pause');result={'paused':is_paused(db)}
    elif args.command=='export-report':
        result=summary(db);Path(args.output).parent.mkdir(parents=True,exist_ok=True)
        Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    else:
        if args.limit_success<=0 or args.max_checks<1 or args.min_delay<10 or args.max_file_mb<1:
            parser.error('Pilot requires limit>0, max_checks>0, min_delay>=10 sec, max_file_mb>=1')
        if args.dry_run:result={'dry_run':True,'network_requests':0,'report':summary(db)}
        else:
            from .drive import DriveUploader,build_service
            uploader=DriveUploader(build_service(args.token))
            result={'stop_reason':run_pilot(db,args,uploader),'report':summary(db)}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
