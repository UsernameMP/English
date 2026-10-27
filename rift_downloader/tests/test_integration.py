import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from rift_downloader.db import connect,import_resources,claim,recover,summary,set_status,completed
from rift_downloader.http import kind,safe_url,retry_after,RateLimiter,PoliteHttp,UnsafeURL
from rift_downloader.cli import upload_one,run_pilot

class FakeResponse:
    def __init__(self,status=200,body=b'',mime='application/pdf',headers=None):
        self.status_code=status
        self.body=body
        self.headers={'Content-Type':mime,'Content-Length':str(len(body)),**(headers or {})}
    def iter_content(self,chunk_size=65536):
        for i in range(0,len(self.body),chunk_size):yield self.body[i:i+chunk_size]
    def close(self):pass
    def __enter__(self):return self
    def __exit__(self,*args):self.close()

class FakeSession:
    def __init__(self,responses):
        self.responses=responses
        self.headers={}
        self.trust_env=True
        self.calls=[]
    def get(self,url,**kwargs):
        self.calls.append(url)
        return self.responses.pop(0)

class FakeUploader:
    def __init__(self):self.objects={}
    def upload(self,sha,path,mime,filename):
        self.objects[sha]=Path(path).read_bytes()
        return 'drive-'+sha[:12]

class PilotTests(unittest.TestCase):
    def test_import_lease_and_recovery(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'db.sqlite'
            db=connect(path)
            row={'resource_id':'r1','url':'https://example.org/file.pdf','file_candidate':True}
            self.assertEqual(import_resources(db,[row,row]),1)
            self.assertEqual(claim(db)['resource_id'],'r1')
            self.assertIsNone(claim(db))
            self.assertEqual(recover(db)['requeued'],1)
            db.close()
            db=connect(path)
            self.assertEqual(claim(db)['resource_id'],'r1')
            self.assertEqual(summary(db)['resource_statuses'],{'checking':1})
    def test_old_schema_upgrade(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'old.sqlite'
            raw=sqlite3.connect(path)
            raw.execute("CREATE TABLE resources(resource_id TEXT PRIMARY KEY,url TEXT NOT NULL UNIQUE,source_url TEXT,mime_hint TEXT,file_candidate INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'pending',attempts INTEGER NOT NULL DEFAULT 0,next_attempt_at TEXT,object_sha256 TEXT,last_error TEXT,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            raw.commit();raw.close()
            db=connect(path)
            self.assertIn('staged_path',[r[1] for r in db.execute('PRAGMA table_info(resources)')])
    def test_formats_and_url_safety(self):
        self.assertEqual(kind('text/html','https://example.org/a.pdf',b'<!doctype html><html>')[0],'html')
        self.assertEqual(kind('application/octet-stream','https://example.org/download?id=12',b'%PDF-1.7\n')[0],'file')
        self.assertEqual(kind('application/octet-stream','https://example.org/a.zip',b'PK\x03\x04')[0],'file')
        self.assertEqual(retry_after('45'),45)
        for url in ['http://127.0.0.1/test','http://169.254.169.254/latest/meta-data/',
                    'file:///tmp/x','http://user:password@foo.com/']:
            with self.assertRaises(UnsafeURL):safe_url(url,resolve=False)
    def test_rate_limit(self):
        tick=[0.]
        def sleep(seconds):tick[0]+=seconds
        limiter=RateLimiter(10,clock=lambda:tick[0],sleep=sleep)
        self.assertEqual(limiter.wait('one.org'),0)
        self.assertEqual(limiter.wait('one.org'),10000)
        self.assertEqual(limiter.wait('two.org'),0)
    def test_http_file_and_html(self):
        with tempfile.TemporaryDirectory() as d:
            body=b'%PDF-1.4\n'+b'a'*500
            session=FakeSession([FakeResponse(404,mime='text/plain'),FakeResponse(200,body)])
            worker=PoliteHttp(session=session,limiter=RateLimiter(0,sleep=lambda _:None),dns_check=False)
            result=worker.fetch('https://example.org/file.pdf',d)
            self.assertEqual(result['outcome'],'staged')
            self.assertEqual(Path(result['path']).read_bytes(),body)
            self.assertEqual(len(session.calls),2)
        with tempfile.TemporaryDirectory() as d:
            session=FakeSession([FakeResponse(404),FakeResponse(200,b'<html>Hello</html>','text/html')])
            worker=PoliteHttp(session=session,limiter=RateLimiter(0,sleep=lambda _:None),dns_check=False)
            self.assertEqual(worker.fetch('https://example.org/page',d)['outcome'],'html_deferred')
            self.assertFalse(list(Path(d).iterdir()))
    def test_robots_deny_and_retry_after(self):
        with tempfile.TemporaryDirectory() as d:
            session=FakeSession([FakeResponse(200,b'User-agent: *\nDisallow: /private','text/plain')])
            worker=PoliteHttp(session=session,limiter=RateLimiter(0,sleep=lambda _:None),dns_check=False)
            self.assertEqual(worker.fetch('https://example.org/private/doc.pdf',d)['outcome'],'blocked')
            self.assertEqual(len(session.calls),1)
        with tempfile.TemporaryDirectory() as d:
            session=FakeSession([FakeResponse(404),FakeResponse(429,headers={'Retry-After':'60'})])
            worker=PoliteHttp(session=session,limiter=RateLimiter(0,sleep=lambda _:None),dns_check=False)
            result=worker.fetch('https://example.org/file.pdf',d)
            self.assertEqual(result['outcome'],'retry')
            self.assertEqual(result['retry_after'],60)
    def test_robots_retry_and_redirect(self):
        with tempfile.TemporaryDirectory() as d:
            session=FakeSession([FakeResponse(429,headers={'Retry-After':'90'})])
            worker=PoliteHttp(session=session,limiter=RateLimiter(0,sleep=lambda _:None),dns_check=False)
            result=worker.fetch('https://example.org/file.pdf',d)
            self.assertEqual(result['outcome'],'retry')
            self.assertEqual(result['http_status'],429)
            self.assertEqual(result['retry_after'],90)
        with tempfile.TemporaryDirectory() as d:
            body=b'%PDF-1.7\noriginal'
            session=FakeSession([
                FakeResponse(301,headers={'Location':'https://example.org/robots.txt'}),
                FakeResponse(404),
                FakeResponse(200,body)])
            worker=PoliteHttp(session=session,limiter=RateLimiter(0,sleep=lambda _:None),dns_check=False)
            self.assertEqual(worker.fetch('http://example.org/file.pdf',d)['outcome'],'staged')
    def test_upload_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            db=connect(Path(d)/'state.db');spool=Path(d)/'spool';spool.mkdir()
            body=b'%PDF-1.7\nhello';sha=hashlib.sha256(body).hexdigest()
            path=spool/sha;path.write_bytes(body)
            import_resources(db,[{'resource_id':'a','url':'https://example.org/a.pdf'},
                                 {'resource_id':'b','url':'https://example.org/b.pdf'}])
            for rid in ('a','b'):
                set_status(db,rid,'staged',sha=sha,path=str(path),filename='a.pdf')
            uploader=FakeUploader()
            self.assertTrue(upload_one(db,uploader,db.execute("SELECT * FROM resources WHERE resource_id='a'").fetchone()))
            self.assertTrue(upload_one(db,uploader,db.execute("SELECT * FROM resources WHERE resource_id='b'").fetchone()))
            self.assertEqual(completed(db),1)
            self.assertEqual(summary(db)['duplicate_links'],1)
    def test_exact_hard_stop(self):
        class FakeWorker:
            def fetch(self,url,spool):
                body=b'%PDF-'+url.encode();sha=hashlib.sha256(body).hexdigest()
                path=Path(spool)/sha;path.write_bytes(body)
                return {'outcome':'staged','sha256':sha,'path':str(path),'filename':'x.pdf',
                        'mime':'application/pdf','bytes_received':len(body)}
        with tempfile.TemporaryDirectory() as d:
            db=connect(Path(d)/'state.db')
            import_resources(db,[{'resource_id':str(i),'url':f'https://example.org/{i}.pdf','file_candidate':True} for i in range(10)])
            args=SimpleNamespace(min_delay=10,max_file_mb=100,spool=str(Path(d)/'spool'),
                                 limit_success=3,max_checks=10,spool_max_gb=10,max_retries=3)
            self.assertEqual(run_pilot(db,args,FakeUploader(),worker=FakeWorker()),'limit_reached')
            self.assertEqual(completed(db),3)
            self.assertEqual(summary(db)['resource_statuses']['pending'],7)

if __name__=='__main__':unittest.main()
