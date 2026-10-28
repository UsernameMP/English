"""Offline and live commands for the separate RIFT downloader pilot."""
import argparse
import glob
import json
import random
import re
import shutil
import time
from pathlib import Path
from urllib.parse import urlparse
from .db import (connect,import_resources,claim,recover,set_status,begin_attempt,
                 exclusive_runner,record_http_event,
                 finish_attempt,event,completed,staged,pause,is_paused,summary)
from .http import PoliteHttp,RateLimiter
from .backup import backup_index,last_backup_count
from .report import export_report
from .inventory import inventory
from .pilot_sample import seed_pilot
from .preflight import preflight

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
        # Mounted Drive receipts preserve the provenance of each duplicate URL
        # even if SQLite crashes before its next cloud checkpoint.
        if hasattr(uploader,'record_existing'):
            try:
                uploader.record_existing(row,sha,obj['drive_file_id'])
            except Exception as exc:
                set_status(db,row['resource_id'],'staged',error=str(exc)[:300])
                event(db,row['resource_id'],'duplicate_receipt_error',str(exc))
                return False
        set_status(db,row['resource_id'],'completed')
        event(db,row['resource_id'],'deduplicated',sha)
        if path.is_file():path.unlink(missing_ok=True)
        return True
    if not sha or not path.is_file():
        set_status(db,row['resource_id'],'failed',error='staged body missing; kept record for investigation')
        return False
    set_status(db,row['resource_id'],'uploading')
    try:
        # The Colab backend writes per-resource recovery receipts to Drive
        # before storing original bytes; API backend remains unchanged.
        if hasattr(uploader,'set_context'):
            uploader.set_context(row)
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

def cleanup_orphans(db,spool):
    """Remove incomplete transfer files after crashes, never referenced staged originals."""
    spool=Path(spool)
    removed=0
    for item in spool.iterdir():
        if not item.is_file():
            continue
        temporary=item.name.startswith(('.downloading-','.index-backup-'))
        content_addressed=bool(re.fullmatch(r'[0-9a-f]{64}',item.name))
        if not temporary and not content_addressed:
            continue
        if content_addressed and db.execute(
             "SELECT 1 FROM resources WHERE staged_path=? AND status IN ('staged','uploading') LIMIT 1",
             (str(item),)).fetchone():
            continue
        try:
            item.unlink()
            removed+=1
        except OSError as exc:
            event(db,None,'orphan_cleanup_error',str(exc))
    if removed:event(db,None,'orphan_cleanup',str(removed))
    return removed

def run_pilot(db,args,uploader,worker=None):
    recover(db)
    seed_pilot(db,limit=getattr(args,'seed_limit',5000))
    if worker is None:
        # Durable request-level pacing across VPS restarts, including robots.txt
        # and redirects; see host_pacing and http_events in SQLite.
        limiter=RateLimiter(delay=args.min_delay,state=db)
        worker=PoliteHttp(delay=args.min_delay,max_bytes=args.max_file_mb*1024*1024,
            limiter=limiter,on_response=lambda url,host,purpose,code,elapsed,wait:
                record_http_event(db,url,host,purpose,code,elapsed,wait))
    spool=Path(args.spool);spool.mkdir(parents=True,exist_ok=True)
    cleanup_orphans(db,spool)
    checks=0
    while completed(db)<args.limit_success:
        if is_paused(db):return 'paused'
        row=staged(db)
        if row:
            before=completed(db)
            if not upload_one(db,uploader,row):return 'upload_error'
            after=completed(db)
            interval=getattr(args,'backup_every',0)
            if interval and after>before and after%interval==0:
                try:backup_index(db,uploader,spool)
                except Exception as exc:
                    event(db,None,'index_backup_error',str(exc))
                    return 'index_backup_error'
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
    plan=sub.add_parser('plan');plan.add_argument('--sample',type=int,default=12)
    seed=sub.add_parser('seed');seed.add_argument('--limit',type=int,default=5000)
    doctor=sub.add_parser('doctor');doctor.add_argument('--token');doctor.add_argument('--spool',default='state/spool');doctor.add_argument('--check-drive',action='store_true')
    report=sub.add_parser('export-report');report.add_argument('--output',required=True)
    run=sub.add_parser('run');run.add_argument('--token')
    run.add_argument('--spool',default='state/spool');run.add_argument('--limit-success',type=int,default=200)
    run.add_argument('--max-checks',type=int,default=3000)
    run.add_argument('--min-delay',type=float,default=10.0)
    run.add_argument('--max-file-mb',type=int,default=100)
    run.add_argument('--spool-max-gb',type=int,default=10)
    run.add_argument('--max-retries',type=int,default=4)
    run.add_argument('--backup-every',type=int,default=25)
    run.add_argument('--seed-limit',type=int,default=5000)
    run.add_argument('--dry-run',action='store_true')
    args=parser.parse_args(argv)
    db=connect(args.db)
    if args.command=='import':result={'imported':import_resources(db,records(args.shards)),'report':summary(db)}
    elif args.command=='status':result=summary(db)
    elif args.command=='plan':result=inventory(db,sample=max(0,min(100,args.sample)))
    elif args.command=='seed':
        with exclusive_runner(args.db):result=seed_pilot(db,limit=args.limit)
    elif args.command=='doctor':result=preflight(db,args.token,args.spool,args.check_drive)
    elif args.command=='recover':result=recover(db)
    elif args.command in ('pause','resume'):
        pause(db,args.command=='pause');result={'paused':is_paused(db)}
    elif args.command=='export-report':
        result={'exported':export_report(db,args.output),'report':summary(db)}
    else:
        if args.limit_success<=0 or args.max_checks<1 or args.min_delay<10 or args.max_file_mb<1 or args.backup_every<1 or args.seed_limit<1:
            parser.error('Pilot requires limit>0, max_checks>0, min_delay>=10 sec, max_file_mb>=1')
        if args.dry_run:result={'dry_run':True,'network_requests':0,'report':summary(db)}
        else:
            if not args.token:
                parser.error('Live pilot requires --token; run doctor to diagnose OAuth readiness')
            # A second accidental service start cannot overshoot the hard cap.
            with exclusive_runner(args.db):
                from .drive import DriveUploader,build_service
                uploader=DriveUploader(build_service(args.token))
                stop_reason=run_pilot(db,args,uploader)
                checkpoint=None
                if completed(db)>last_backup_count(db):
                    try:checkpoint=backup_index(db,uploader,args.spool)
                    except Exception as exc:
                        event(db,None,'index_backup_error',str(exc))
                        stop_reason='index_backup_error'
                result={'stop_reason':stop_reason,'index_checkpoint':checkpoint,'report':summary(db)}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
