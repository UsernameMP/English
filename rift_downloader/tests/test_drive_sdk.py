"""Exercise the real DriveUploader through a fake Drive v3 Files API.

No OAuth, network calls or Google Drive account mutation. We run the actual
MediaFileUpload object, SHA-256/MD5 verification, folder creation, duplicate
search and crash-recovery second upload.
"""
import hashlib
import re
import tempfile
import unittest
from pathlib import Path
from rift_downloader.drive import DriveUploader,DriveError

class FakeExecution:
    def __init__(self,func):self.func=func
    def execute(self):return self.func()

class FakeUpload:
    def __init__(self,files,body,media):
        self.files=files
        self.body=body
        self.media=media
        self.response=None
    def next_chunk(self,num_retries=2):
        if self.response is None:
            body=self.media.stream()
            position=body.tell()
            body.seek(0)
            data=body.read()
            body.seek(position)
            ident='id-'+str(self.files.sequence)
            self.files.sequence+=1
            self.files.entries[ident]={
                'id':ident,'name':self.body['name'],
                'parents':list(self.body.get('parents',[])),
                'appProperties':dict(self.body.get('appProperties',{})),
                'size':str(len(data)),
                'md5Checksum':hashlib.md5(data).hexdigest(),
                'bytes':data,'mimeType':self.media.mimetype()
            }
            self.response={'id':ident,'size':str(len(data))}
        return None,self.response

class FakeFiles:
    def __init__(self):
        self.entries={}
        self.sequence=1
        self.corrupt_metadata=False
    def list(self,q,spaces,fields,page_size=100):
        def find():
            if 'appProperties has' in q:
                matched=re.search(r"value='([0-9a-f]{64})'",q)
                if not matched:raise AssertionError('unexpected SHA-256 query '+q)
                files=[d for d in self.entries.values() if d.get('appProperties',{}).get('rift_sha256')==matched[1]]
            else:
                name=re.search(r"name='([^']*)'",q)[1]
                parent=re.search(r"'([^']+)' in parents",q)
                expected_parent=parent[1] if parent else 'root'
                files=[d for d in self.entries.values()
                    if d['mimeType']=='application/vnd.google-apps.folder'
                    and d['name']==name and expected_parent in d['parents']]
            return {'files':[{k:v for k,v in d.items() if k in ('id','name','size','md5Checksum')} for d in files]}
        return FakeExecution(find)
    def get(self,fileId,fields):
        def result():
            entry=dict(self.entries[fileId])
            if self.corrupt_metadata and entry['mimeType']!='application/vnd.google-apps.folder':
                entry['md5Checksum']='0'*32
            return {k:entry[k] for k in ('id','size','md5Checksum') if k in entry}
        return FakeExecution(result)
    def create(self,body,fields,media_body=None):
        if media_body is not None:
            return FakeUpload(self,body,media_body)
        def new_folder():
            ident='id-'+str(self.sequence)
            self.sequence+=1
            self.entries[ident]={
                'id':ident,'name':body['name'],
                'parents':list(body.get('parents',[])),
                'appProperties':{},'mimeType':'application/vnd.google-apps.folder'}
            return {'id':ident}
        return FakeExecution(new_folder)

class FakeDrive:
    def __init__(self):self._files=FakeFiles()
    def files(self):return self._files

class DriveSdkTests(unittest.TestCase):
    def test_upload_verifies_original_and_dedupes_after_new_process(self):
        with tempfile.TemporaryDirectory() as td:
            data=b'%PDF-1.7\n'+b'official contest archive\n'*12
            path=Path(td)/'paper.pdf'
            path.write_bytes(data)
            sha=hashlib.sha256(data).hexdigest()
            service=FakeDrive()
            first=DriveUploader(service).upload(sha,path,'application/pdf','paper.pdf')
            self.assertEqual(first,'id-4') # RIFT, raw, xx prefix folder, then PDF
            record=service.files().entries[first]
            self.assertEqual(record['bytes'],data)
            self.assertEqual(record['appProperties']['rift_sha256'],sha)
            self.assertEqual(record['md5Checksum'],hashlib.md5(data).hexdigest())
            self.assertEqual(record['name'],sha+'.pdf')
            # Simulate SQLite crash just after a successful remote upload. The
            # next process must find the object by appProperties, not re-upload.
            second=DriveUploader(service).upload(sha,path,'application/pdf','paper.pdf')
            self.assertEqual(second,first)
            self.assertEqual(len(service.files().entries),4)
            self.assertTrue(path.exists()) # uploader never removes staged body
    def test_checksum_mismatch_fails_closed_without_deleting_original(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'task.zip';path.write_bytes(b'PK\x03\x04archive demo')
            sha=hashlib.sha256(path.read_bytes()).hexdigest()
            service=FakeDrive()
            service.files().corrupt_metadata=True
            with self.assertRaises(DriveError):
                DriveUploader(service).upload(sha,path,'application/zip','task.zip')
            self.assertTrue(path.exists())
    def test_pinned_folder_never_creates_a_second_root(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'official.pdf';source.write_bytes(b'%PDF-1.7\nfile')
            sha=hashlib.sha256(source.read_bytes()).hexdigest()
            drive=FakeDrive()
            ref=DriveUploader(drive,root_folder_id='already-owned-RIFT-folder').upload(
                sha,source,'application/pdf','official.pdf')
            self.assertEqual(len(drive.files().entries),3)
            folders=[item for item in drive.files().entries.values()
                if item['mimeType']=='application/vnd.google-apps.folder']
            self.assertEqual({item['name'] for item in folders},{'raw',sha[:2]})
            self.assertTrue(any('already-owned-RIFT-folder' in item['parents'] for item in folders))

    def test_index_backups_go_to_separate_folder(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'index.sqlite3';path.write_bytes(b'SQLite format 3\x00temporary')
            sha=hashlib.sha256(path.read_bytes()).hexdigest()
            service=FakeDrive()
            file_id=DriveUploader(service).upload(sha,path,'application/vnd.sqlite3',
                                                   'index.sqlite3',category='index')
            obj=service.files().entries[file_id]
            folders=service.files().entries
            parent=folders[obj['parents'][0]]
            self.assertEqual(parent['name'],'index')
            self.assertEqual(obj['appProperties']['rift_format'],'index-v1')

if __name__=='__main__':
    unittest.main()
