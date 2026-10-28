"""Google Drive original-binary uploader with hash idempotency and verification."""
import hashlib
import mimetypes
import os
import random
import time
from pathlib import Path

SCOPES=['https://www.googleapis.com/auth/drive.file']
class DriveError(RuntimeError):pass

def build_service(token_file):
    """OAuth credential belongs to the user and stays on their machine/VPS."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise DriveError('Install requirements.txt before using Google Drive') from exc
    token_file=Path(token_file)
    if not token_file.is_file():raise DriveError(f'Missing OAuth token: {token_file}; see README')
    import stat
    if stat.S_IMODE(token_file.stat().st_mode) & (stat.S_IRWXG|stat.S_IRWXO):
        raise DriveError('OAuth token file is not private; run chmod 600 on the VPS token')
    creds=Credentials.from_authorized_user_file(str(token_file),SCOPES)
    if not creds.valid:
        if not creds.refresh_token:raise DriveError('OAuth refresh token missing; authorize again')
        creds.refresh(Request())
        temporary=token_file.with_suffix(token_file.suffix+'.tmp')
        temporary.write_text(creds.to_json(),encoding='utf-8')
        os.chmod(temporary,0o600)
        os.replace(temporary,token_file)
    return build('drive','v3',credentials=creds,cache_discovery=False)

def file_md5(path):
    md5=hashlib.md5()
    with open(path,'rb') as stream:
        for piece in iter(lambda:stream.read(1024*1024),b''):md5.update(piece)
    return md5.hexdigest()

class DriveUploader:
    def __init__(self,service):
        self.service=service
        self.folder_cache={}
    def _folder(self,name,parent=None):
        key=(name,parent)
        if key in self.folder_cache:return self.folder_cache[key]
        safe=name.replace("'","\\'")
        parent_clause=f" and '{parent}' in parents" if parent else " and 'root' in parents"
        q=f"mimeType='application/vnd.google-apps.folder' and name='{safe}' and trashed=false{parent_clause}"
        found=self.service.files().list(q=q,spaces='drive',fields='files(id,name),nextPageToken',page_size=100).execute().get('files',[])
        if found:identifier=found[0]['id']
        else:
            obj={'name':name,'mimeType':'application/vnd.google-apps.folder','parents':[parent or 'root']}
            identifier=self.service.files().create(body=obj,fields='id').execute()['id']
        self.folder_cache[key]=identifier
        return identifier
    def _hash_remote(self,sha):
        q=f"appProperties has {{ key='rift_sha256' and value='{sha}' }} and trashed=false"
        return self.service.files().list(q=q,spaces='drive',
            fields='nextPageToken,files(id,name,size,md5Checksum)',page_size=100).execute().get('files',[])
    def _verified(self,file_id,size,md5):
        obj=self.service.files().get(fileId=file_id,fields='id,size,md5Checksum').execute()
        if int(obj.get('size',-1))!=int(size) or obj.get('md5Checksum','').lower()!=md5.lower():
            raise DriveError(f'Verification mismatch for Drive object {file_id}')
        return file_id
    def upload(self,sha,path,mime,filename,*,category='raw'):
        """Idempotent across crashes, including completed upload before SQLite commit."""
        try:
            from googleapiclient.http import MediaFileUpload
            from googleapiclient.errors import HttpError
        except ImportError as exc:raise DriveError('google-api-python-client is required') from exc
        path=Path(path)
        if not path.is_file():raise DriveError(f'Staged file missing: {path}')
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
        if digest.hexdigest()!=sha:raise DriveError('Staged file SHA-256 mismatch')
        size=path.stat().st_size
        md5=file_md5(path)
        try:
            for obj in self._hash_remote(sha):
                if int(obj.get('size',-1))==size and obj.get('md5Checksum')==md5:
                    return self._verified(obj['id'],size,md5)
            root=self._folder('RIFT')
            if category not in ('raw','index'):
                raise DriveError('Unsupported Drive storage category')
            folder=self._folder(category,root)
            bucket=self._folder(sha[:2],folder) if category=='raw' else folder
            suffix=Path(filename or '').suffix.lower()
            if not suffix or len(suffix)>12:suffix=mimetypes.guess_extension(mime or '') or '.bin'
            media=MediaFileUpload(str(path),mimetype=mime or 'application/octet-stream',
                                  resumable=True,chunksize=8*1024*1024)
            body={'name':sha+suffix,'parents':[bucket],
                  'appProperties':{'rift_sha256':sha,'rift_format':category+'-v1'}}
            request=self.service.files().create(body=body,media_body=media,fields='id,size,md5Checksum')
            response=None
            for attempt in range(7):
                try:
                    while response is None:
                        _,response=request.next_chunk(num_retries=2)
                    break
                except HttpError as exc:
                    status=int(getattr(exc.resp,'status',0))
                    reason=str(exc)
                    retriable=status in (429,500,502,503,504) or (status==403 and any(x in reason for x in ('rateLimitExceeded','userRateLimitExceeded')))
                    if not retriable or attempt==6:raise
                    time.sleep(min(120,2**attempt+random.random()))
            if not response or not response.get('id'):raise DriveError('Drive did not return a file ID')
            return self._verified(response['id'],size,md5)
        except DriveError:raise
        except Exception as exc:raise DriveError(f'Drive upload failed: {exc}') from exc
