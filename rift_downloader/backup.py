"""Consistent SQLite snapshots uploaded into RIFT/index on Google Drive."""
import hashlib
import json
import os
import sqlite3
import tempfile
import time
from pathlib import Path
from .db import completed,event

def backup_index(db,uploader,spool):
    """Create SQLite online backup, verify through Drive uploader, then delete local snapshot."""
    directory=Path(spool)
    directory.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix='.index-backup-',suffix='.sqlite3',dir=directory)
    os.close(fd)
    try:
        target=sqlite3.connect(temp)
        try:
            db.backup(target,pages=500,sleep=0.05)
            target.commit()
        finally:
            target.close()
        sha=hashlib.sha256()
        with open(temp,'rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):
                sha.update(chunk)
        digest=sha.hexdigest()
        file_id=uploader.upload(digest,temp,'application/vnd.sqlite3','rift-index.sqlite3',
                                category='index')
        count=completed(db)
        event(db,None,'index_backup',json.dumps({'sha256':digest,'drive_file_id':file_id,
                                                 'verified_files':count,'created_at':time.time()}))
        return {'drive_file_id':file_id,'sha256':digest,'verified_files':count}
    finally:
        Path(temp).unlink(missing_ok=True)
