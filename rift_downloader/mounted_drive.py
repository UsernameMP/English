"""RIFT pilot backend for an explicitly mounted Google Drive in Google Colab.

No Google Cloud project, OAuth token export, or VPS access required.
Stores original bytes in RIFT/raw/xx/<sha256>.<ext>. Index receipts make an
interrupted session recoverable even if its latest SQLite backup is stale.
"""
import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path

SHA=re.compile(r'^[a-f0-9]{64}$')
RID=re.compile(r'^[a-zA-Z0-9_-]{1,128}$')
EXT=re.compile(r'^\.[a-z0-9]{1,10}$')
BUFFER=1024*1024

class MountedDriveError(RuntimeError):
    pass

def hash_file(path):
    digest=hashlib.sha256()
    size=0
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(BUFFER),b''):
            digest.update(chunk)
            size+=len(chunk)
    return digest.hexdigest(),size

def atomic_json(path,data):
    """Temp file + replace, never leave a partially written receipt."""
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.partial-',suffix='.json',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as handle:
            json.dump(data,handle,ensure_ascii=False,sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

class MountedDriveUploader:
    """Drop-in uploader for run_pilot, using Colab's user-authorized Drive mount.

    Returned drive_file_id uses 'drivefs:' as an explicit pseudo-locator;
    it is NOT a Google Drive API file ID.
    """
    def __init__(self,root):
        self.root=Path(root).expanduser().resolve()
        if not self.root.parent.is_dir():
            raise MountedDriveError('Mount the user Google Drive in Colab first')
        self.root.mkdir(parents=True,exist_ok=True)
        self.context=None
    def set_context(self,row):
        self.context={'resource_id':row['resource_id'],'url':row['url'],
                      'source_url':row['source_url'] if 'source_url' in row.keys() else None}
    def _destination(self,sha,filename,category):
        if category not in ('raw','index'):
            raise MountedDriveError('Unknown archive category')
        if not SHA.fullmatch(sha):
            raise MountedDriveError('Invalid SHA-256')
        ext=Path(filename or '').suffix.lower()
        if not EXT.fullmatch(ext):
            ext='.bin' if category=='raw' else '.sqlite3'
        base=self.root/category
        folder=base/sha[:2] if category=='raw' else base
        if category=='raw' and folder.is_dir():
            # Deduplicate by digest, NOT by extension: the same PDF may appear
            # as task.pdf, task.zip, download?id=123 on different sites.
            existing=sorted(folder.glob(sha+'.*'))
            if existing:return existing[0]
        return folder/(sha+ext)
    def record_existing(self,row,sha,locator):
        """Persist a receipt for an additional URL to an already stored blob."""
        if not locator.startswith('drivefs:'):
            raise MountedDriveError('Unexpected mounted Drive object locator')
        rid=row['resource_id']
        if not RID.fullmatch(rid) or not SHA.fullmatch(sha):
            raise MountedDriveError('Unsafe receipt identifier')
        rel=locator.removeprefix('drivefs:')
        target=(self.root/rel).resolve()
        if not target.is_relative_to((self.root/'raw').resolve()):
            raise MountedDriveError('Invalid raw blob location')
        if not target.is_file():
            raise MountedDriveError('Missing previously archived raw object')
        digest,size=hash_file(target)
        if digest!=sha:
            raise MountedDriveError('Previously archived raw file corrupted')
        atomic_json(self.root/'receipts'/(rid+'.json'),{
            'resource_id':rid,'url':row['url'],
            'source_url':row['source_url'],'sha256':sha,
            'size_bytes':size,'mime_type':row['mime_hint'],
            'file_name':row['filename'],
            'relative_path':target.relative_to(self.root).as_posix(),
            'archive_state':'verified','verified_at':time.time()
        })

    def upload(self,sha,path,mime,filename,*,category='raw'):
        original=Path(path)
        if not original.is_file():
            raise MountedDriveError('Staged input missing')
        real_hash,size=hash_file(original)
        if real_hash!=sha:
            raise MountedDriveError('Local SHA-256 mismatch')
        dest=self._destination(sha,filename,category)
        dest.parent.mkdir(parents=True,exist_ok=True)
        ctx=self.context if category=='raw' else None
        try:
            receipt=None
            if ctx:
                rid=ctx['resource_id']
                if not RID.fullmatch(rid):
                    raise MountedDriveError('Unsafe resource ID')
                receipt_path=self.root/'receipts'/(rid+'.json')
                receipt={
                    'resource_id':rid,'source_url':ctx.get('source_url'),
                    'url':ctx['url'],'sha256':sha,'size_bytes':size,
                    'mime_type':mime,'file_name':filename,
                    'relative_path':dest.relative_to(self.root).as_posix(),
                    'archive_state':'copying','written_at':time.time()
                }
                atomic_json(receipt_path,receipt)
            if dest.exists():
                existing_hash,existing_size=hash_file(dest)
                if existing_hash!=sha or existing_size!=size:
                    raise MountedDriveError(
                        'Destination name already exists with different content; refusing overwrite')
            else:
                fd,tmp=tempfile.mkstemp(prefix='.partial-',dir=dest.parent)
                try:
                    with os.fdopen(fd,'wb') as writer,original.open('rb') as reader:
                        shutil.copyfileobj(reader,writer,length=BUFFER)
                        writer.flush()
                        os.fsync(writer.fileno())
                    os.replace(tmp,dest)
                finally:
                    if os.path.exists(tmp):os.unlink(tmp)
            verified_hash,verified_size=hash_file(dest)
            if verified_hash!=sha or verified_size!=size:
                raise MountedDriveError('Mounted Drive readback failed; original retained')
            if receipt is not None:
                receipt.update(archive_state='verified',verified_at=time.time())
                atomic_json(receipt_path,receipt)
            # Locator is not a Google Drive API ID.
            return 'drivefs:'+dest.relative_to(self.root).as_posix()
        finally:
            self.context=None

def reconcile_receipts(db,root):
    """Restore index records for verified files after an interrupted Colab runtime.

    Raw files are always written *after* a receipt containing the source URL.
    A crash between Drive write and SQLite backup is therefore recoverable.
    Does not overwrite existing verified object records or delete any files.
    """
    root=Path(root)
    folder=root/'receipts'
    if not folder.is_dir():return {'verified_receipts':0,'restored_links':0}
    inspected=0;restored=0;corrupt=0
    for file in folder.glob('*.json'):
        try:
            data=json.loads(file.read_text(encoding='utf-8'))
            rid=data['resource_id'];sha=data['sha256'];rel=data['relative_path']
            if not RID.fullmatch(rid) or not SHA.fullmatch(sha):
                corrupt+=1
                continue
            dest=(root/rel).resolve()
            if not dest.is_relative_to((root/'raw').resolve()) or not dest.is_file():
                continue
            record=db.execute('SELECT resource_id,url,status FROM resources WHERE resource_id=?',(rid,)).fetchone()
            if record is None or record['url']!=data['url']:
                corrupt+=1
                continue
            verified_hash,verified_size=hash_file(dest)
            if verified_hash!=sha or verified_size!=int(data['size_bytes']):
                corrupt+=1
                continue
            inspected+=1
            identifier='drivefs:'+rel
            with db:
                db.execute('''INSERT INTO objects (sha256,size_bytes,mime_type,drive_file_id,verified_at)
                    VALUES (?,?,?,?,?)
                    ON CONFLICT(sha256) DO NOTHING''',
                    (sha,verified_size,data.get('mime_type'),identifier,time.time()))
                db.execute('''UPDATE resources SET object_sha256=?,status='completed',
                    staged_path=NULL,last_error=NULL,updated_at=?
                    WHERE resource_id=? AND status!='completed' ''',
                    (sha,time.time(),rid))
                restored+=db.execute('SELECT changes()').fetchone()[0]
        except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):
            corrupt+=1
            continue
    return {'verified_receipts':inspected,'restored_links':restored,'invalid_receipts':corrupt}

def restore_index_snapshot(root,local_db):
    """Find latest valid RIFT/index SHA-addressed SQLite backup.

    The Colab database runs on local disk, not over Drive FUSE (SQLite locking
    over a remote filesystem is unsafe). Only snapshots live in Google Drive.
    """
    root=Path(root)
    db_path=Path(local_db)
    if db_path.exists():return {'restored':False,'reason':'local database already exists'}
    candidates=[]
    for file in (root/'index').glob('*.sqlite3'):
        if SHA.fullmatch(file.stem):
            candidates.append(file)
    candidates.sort(key=lambda path:path.stat().st_mtime,reverse=True)
    for backup in candidates:
        temp=db_path.with_suffix('.restore.tmp')
        try:
            # SQLite must never open a database directly on mounted Drive.
            db_path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(backup,temp)
            sha,_=hash_file(temp)
            if sha!=backup.stem:continue
            conn=sqlite3.connect(temp)
            try:
                ok=conn.execute('PRAGMA quick_check').fetchone()[0]
                if ok!='ok':continue
                n=conn.execute('SELECT COUNT(*) FROM resources').fetchone()[0]
                if not n:continue
            finally:conn.close()
            os.replace(temp,db_path)
            return {'restored':True,'snapshot':backup.name,'resources':n}
        except (OSError,sqlite3.Error,ValueError):
            continue
        finally:
            temp.unlink(missing_ok=True)
    return {'restored':False,'reason':'no verified index snapshot'}
