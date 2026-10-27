"""Regression tests for 200-file hard stop, backup, and binary MIME precision."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from rift_downloader.db import connect,import_resources,completed,summary
from rift_downloader.cli import run_pilot
from rift_downloader.http import kind,PoliteHttp,RateLimiter

class Response:
    def __init__(self,code,body=b'',headers=None):
        self.status_code=code
        self.body=body
        self.headers={'Content-Type':'application/pdf','Content-Length':str(len(body)),
                      **(headers or {})}
    def iter_content(self,chunk_size=65536):
        for i in range(0,len(self.body),chunk_size):
            yield self.body[i:i+chunk_size]
    def close(self):pass
    def __enter__(self):return self
    def __exit__(self,*args):self.close()

class Session:
    def __init__(self,answers):
        self.answers=list(answers)
        self.headers={}
        self.trust_env=True
    def get(self,*args,**kwargs):
        return self.answers.pop(0)

class Worker:
    def __init__(self):self.calls=0
    def fetch(self,url,spool):
        self.calls+=1
        data=('%PDF-1.6\n'+url).encode()
        digest=hashlib.sha256(data).hexdigest()
        path=Path(spool)/digest
        path.write_bytes(data)
        return {'outcome':'staged','sha256':digest,'path':str(path),
                'filename':'task.pdf','mime':'application/pdf',
                'bytes_received':len(data),'http_status':200,
                'elapsed_ms':7,'wait_ms':0}

class FakeDrive:
    def __init__(self):self.raw={};self.snapshots=[]
    def upload(self,sha,path,mime,filename,*,category='raw'):
        data=Path(path).read_bytes()
        assert hashlib.sha256(data).hexdigest()==sha
        if category=='index':
            self.snapshots.append((sha,data))
        else:self.raw[sha]=data
        return 'drive-test-'+sha[:16]

class HardeningTests(unittest.TestCase):
    def test_mime_signatures_override_misleading_headers(self):
        self.assertEqual(kind('text/html','https://example.org/download',b'%PDF-1.7\n')[1],'application/pdf')
        cases={'.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
               '.xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
               '.pptx':'application/vnd.openxmlformats-officedocument.presentationml.presentation',
               '.epub':'application/epub+zip'}
        for extension,mime in cases.items():
            with self.subTest(extension=extension):
                self.assertEqual(kind('application/zip','https://example.org/file'+extension,b'PK\x03\x04')[1],mime)
    def test_compressed_transfer_length_does_not_corrupt_original(self):
        with tempfile.TemporaryDirectory() as root:
            expected=b'%PDF-1.5\nPDF transported with Content-Encoding gzip'
            session=Session([Response(404,headers={'Content-Type':'text/plain'}),
                             Response(200,body=expected,
                                      headers={'Content-Encoding':'gzip','Content-Length':'12'})])
            worker=PoliteHttp(session=session,limiter=RateLimiter(0,sleep=lambda _:None),dns_check=False)
            result=worker.fetch('https://example.org/123.pdf',root)
            self.assertEqual(result['outcome'],'staged')
            self.assertEqual(Path(result['path']).read_bytes(),expected)
            self.assertEqual(result['bytes_received'],len(expected))
    def test_exactly_200_unique_drive_objects_and_eight_backups(self):
        with tempfile.TemporaryDirectory() as d:
            db=connect(Path(d)/'state.db')
            rows=[{'resource_id':f'r{i:04d}','url':f'https://example.org/{i}.pdf',
                   'file_candidate':True} for i in range(205)]
            self.assertEqual(import_resources(db,rows),205)
            args=SimpleNamespace(min_delay=10,max_file_mb=100,spool=str(Path(d)/'spool'),
                                 limit_success=200,max_checks=205,spool_max_gb=10,
                                 max_retries=4,backup_every=25)
            uploader=FakeDrive();worker=Worker()
            self.assertEqual(run_pilot(db,args,uploader,worker),'limit_reached')
            self.assertEqual(completed(db),200)
            self.assertEqual(worker.calls,200)
            self.assertEqual(len(uploader.raw),200)
            self.assertEqual(len(uploader.snapshots),8)
            self.assertEqual(summary(db)['resource_statuses']['pending'],5)
            self.assertEqual(db.execute("SELECT value FROM settings WHERE key='last_index_backup_count'").fetchone()[0],'200')
            self.assertEqual(run_pilot(db,args,uploader,worker),'limit_reached')
            self.assertEqual(worker.calls,200)
            self.assertEqual(summary(db)['uploaded_files'],200)

if __name__=='__main__':
    unittest.main()
