"""GitHub Actions runner: Drive checkpoint restore, bounded URL batch and metrics.

Requires a user-owned OAuth credential in GitHub repository secrets.
No network requests to original source sites in the report-only mode.
"""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace

from .backup import backup_index
from .cli import records,run_pilot
from .db import connect,exclusive_runner,import_resources
from .drive import DriveUploader,build_service
from .ops_metrics import build_metrics,write_dashboard
from .report import export_report

SHA_BACKUP=re.compile(r'^[a-f0-9]{64}\.sqlite3$')
CURRENT_RIFT_ROOT='1uyPU91NHIfIf-wGXO5UAAnNCG9CqQD1o'

class CloudRunError(RuntimeError):
    pass

def existing_root(service,folder_id):
    item=service.files().get(fileId=folder_id,fields='id,name,mimeType').execute()
    if item.get('name')!='RIFT' or item.get('mimeType')!='application/vnd.google-apps.folder':
        raise CloudRunError('RIFT folder ID does not point to the expected original archive')
    return folder_id

def existing_folder(service,parent,name):
    safe=name.replace('\\','\\\\').replace("'","\\'")
    query=("mimeType = 'application/vnd.google-apps.folder' "
           f"and name = '{safe}' and '{parent}' in parents and trashed = false")
    result=service.files().list(q=query,fields='nextPageToken,files(id,name)',
                               page_size=100).execute()
    items=result.get('files',[])
    if len(items)!=1:
        raise CloudRunError(f'Expected one RIFT/{name} folder, found {len(items)}')
    return items[0]['id']

def candidates(service,index_folder):
    files=[]
    page_token=None
    while True:
        params={'q':f"'{index_folder}' in parents and trashed = false",
                'fields':'nextPageToken,files(id,name,modifiedTime,size)','page_size':100}
        if page_token:params['page_token']=page_token
        page=service.files().list(**params).execute()
        files.extend(item for item in page.get('files',[])
                     if SHA_BACKUP.fullmatch(item.get('name',''))
                     and 0<int(item.get('size',0))<=512*1024*1024)
        page_token=page.get('nextPageToken')
        if not page_token:break
    return sorted(files,key=lambda x:(x.get('modifiedTime',''),x['name']),reverse=True)

def verify_snapshot(path,filename):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            digest.update(chunk)
    if digest.hexdigest()!=filename.split('.')[0]:
        raise CloudRunError('Drive SQLite backup SHA-256 mismatch')
    db=sqlite3.connect(path)
    try:
        if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':
            raise CloudRunError('Drive SQLite backup quick_check failed')
        count=db.execute('SELECT COUNT(*) FROM resources').fetchone()[0]
        if count<1:raise CloudRunError('Drive snapshot is empty')
    finally:db.close()
    return count

def restore_latest(service,root_id,db_path):
    """Download most recent valid checkpoint to a LOCAL SQLite database."""
    existing_root(service,root_id)
    index=existing_folder(service,root_id,'index')
    snapshots=candidates(service,index)
    if not snapshots:return {'restored':False,'reason':'no_existing_checkpoint'}
    from googleapiclient.http import MediaIoBaseDownload
    db_path=Path(db_path)
    db_path.parent.mkdir(parents=True,exist_ok=True)
    errors=[]
    for item in snapshots:
        fd,temp=tempfile.mkstemp(prefix='.rift-restore-',suffix='.sqlite3',dir=db_path.parent)
        try:
            with os.fdopen(fd,'wb') as output:
                downloader=MediaIoBaseDownload(
                    output,service.files().get_media(fileId=item['id']),
                    chunksize=8*1024*1024)
                finished=False
                while not finished:
                    _,finished=downloader.next_chunk(num_retries=3)
                output.flush();os.fsync(output.fileno())
            count=verify_snapshot(temp,item['name'])
            os.replace(temp,db_path)
            return {'restored':True,'snapshot':item['name'],'resource_count':count}
        except Exception as exc:
            errors.append(type(exc).__name__)
        finally:
            Path(temp).unlink(missing_ok=True)
    raise CloudRunError(f'All {len(snapshots)} Drive snapshots failed verification ({sorted(set(errors))})')

def verify_token_scopes(path):
    item=json.loads(Path(path).read_text(encoding='utf-8'))
    scopes=item.get('scopes') or []
    if isinstance(scopes,str):scopes=scopes.split()
    if 'https://www.googleapis.com/auth/drive' not in scopes:
        raise CloudRunError('Existing Colab RIFT folder requires Drive OAuth scope; drive.file cannot read other apps files. Prefer a dedicated Google account.')
    return scopes

def actions_summary(metrics,folder_id,checkpoint):
    m=metrics['metrics']
    lines=[
      '## RIFT Downloader: workflow result','',
      'Run status: '+str(metrics['state'])+'; stop reason: '+str(metrics['stop_reason']),'',
      '| Metric | Count |','|---|---:|',
      '| Unique URLs checked | '+str(m['unique_urls_checked'])+' |',
      '| HTTP/URL attempts | '+str(m['total_url_attempts'])+' |',
      '| Unique saved files | '+str(m['unique_files'])+' |',
      '| Bytes stored | '+str(m['stored_bytes'])+' |',
      '| HTTP requests incl robots | '+str(m['http_requests'])+' |',
      '| HTTP 403 / 429 | '+str(m['http_403'])+' / '+str(m['http_429'])+' |',
      '| HTTP 404 | '+str(m['http_404'])+' |','',
      '[Open the existing RIFT Google Drive folder](https://drive.google.com/drive/folders/'+folder_id+')','',
      'The count of URLs checked is intentionally independent of saved files.','',
    ]
    if checkpoint:
        lines.append('Verified SQLite checkpoint SHA-256: '+checkpoint['sha256'])
    return '\n'.join(lines)

def run(argv=None):
    p=argparse.ArgumentParser(description='RIFT Actions bounded source URL batch')
    p.add_argument('--mode',choices=['report','batch'],required=True)
    p.add_argument('--token',required=True)
    p.add_argument('--workdir',default='state/actions')
    p.add_argument('--output-dir',default='rift_ops_output')
    p.add_argument('--source-glob',default='source_discovery/resources_shards/resource_*.jsonl')
    p.add_argument('--drive-root-id',default=os.getenv('RIFT_DRIVE_ROOT_ID',CURRENT_RIFT_ROOT))
    p.add_argument('--limit-urls',type=int,default=200)
    p.add_argument('--max-checks',type=int,default=500)
    p.add_argument('--min-delay',type=float,default=10.0)
    p.add_argument('--max-file-mb',type=int,default=100)
    p.add_argument('--run-id')
    args=p.parse_args(argv)
    if args.limit_urls<1 or args.limit_urls>1000 or args.max_checks<args.limit_urls:
        p.error('1 <= limit-urls <= 1000 and max-checks >= limit-urls')
    if args.min_delay<10:p.error('min-delay must be >= 10 seconds')
    token=Path(args.token)
    if not token.is_file():raise CloudRunError('OAuth token file missing')
    verify_token_scopes(token)
    service=build_service(token)
    work=Path(args.workdir).resolve()
    out=Path(args.output_dir).resolve()
    work.mkdir(parents=True,exist_ok=True)
    out.mkdir(parents=True,exist_ok=True)
    database=work/'rift.sqlite3'
    uploader=DriveUploader(service)
    checkpoint=None
    err=None
    with exclusive_runner(database):
        recovered=restore_latest(service,args.drive_root_id,database)
        db=connect(database)
        if not recovered['restored']:
            added=import_resources(db,records([args.source_glob]))
            if added<1000:raise CloudRunError(f'Original RIFT index unavailable ({added} URLs)')
        state='report_only' if args.mode=='report' else 'running'
        stop='no_source_requests' if args.mode=='report' else 'not_started'
        try:
            if args.mode=='batch':
                settings=SimpleNamespace(limit_success=1000000000,limit_urls=args.limit_urls,
                    max_checks=args.max_checks,min_delay=args.min_delay,
                    max_file_mb=args.max_file_mb,spool=str(work/'spool'),
                    spool_max_gb=10,max_retries=4,backup_every=25,
                    seed_limit=5000,progress_every=10)
                stop=run_pilot(db,settings,uploader)
                state='completed' if stop=='url_limit_reached' else 'stopped'
        except Exception as exc:
            err=type(exc).__name__+': '+str(exc)[:240]
            state='failed';stop='unexpected_exception'
        finally:
            try:
                # Always persist the URL ledger, even if all fetched URLs were
                # 403/404: a file-only checkpoint would lose those attempts.
                if args.mode=='batch':
                    checkpoint=backup_index(db,uploader,work/'spool')
            except Exception as exc:
                state='checkpoint_failed';stop='checkpoint_error'
                err=type(exc).__name__+': '+str(exc)[:240]
            metrics=build_metrics(db,run_state=state,stop_reason=stop,
                                  limit_new_urls=args.limit_urls if args.mode=='batch' else None,
                                  run_id=args.run_id)
            export_report(db,out/'pilot_report.json')
            write_dashboard(metrics,out/'index.html',out/'status.json')
            (out/'github_step_summary.md').write_text(
                actions_summary(metrics,args.drive_root_id,checkpoint),encoding='utf-8')
            (out/'run_result.json').write_text(json.dumps({
                'state':state,'stop_reason':stop,'restored':recovered,
                'checkpoint':checkpoint,'error':err,
                'urls_total':metrics['metrics']['unique_urls_checked'],
                'unique_files':metrics['metrics']['unique_files']},
                ensure_ascii=False,indent=2),encoding='utf-8')
            db.close()
    if err:raise CloudRunError(err)
    return state

if __name__=='__main__':run()
