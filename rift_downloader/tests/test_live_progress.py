"""Live Colab progress survives interruption, with no external network."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from rift_downloader.db import connect,import_resources,completed
from rift_downloader.cli import run_pilot
from rift_downloader.progress import write_progress,progress_snapshot

class FakeWorker:
    def fetch(self,url,spool):
        data=b'%PDF-1.7\n'+url.encode()
        sha=hashlib.sha256(data).hexdigest()
        path=Path(spool)/sha
        path.write_bytes(data)
        return dict(outcome='staged',sha256=sha,path=str(path),filename='demo.pdf',
                    mime='application/pdf',bytes_received=len(data),http_status=200,
                    elapsed_ms=20,wait_ms=10000)

class FakeUploader:
    def __init__(self):self.count=0
    def upload(self,sha,path,mime,filename,*,category='raw'):
        self.count+=1
        return 'drive-'+sha[:20]

class ProgressTests(unittest.TestCase):
    def test_progress_file_is_compact_and_persistent(self):
        with tempfile.TemporaryDirectory() as d:
            db=connect(Path(d)/'index.db')
            import_resources(db,[{'resource_id':'r','url':'https://example.org/a.pdf'}])
            path=Path(d)/'reports'/'pilot_progress.json'
            data=write_progress(db,path,state='running',target=200)
            self.assertTrue(path.exists())
            stored=json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(stored['verified_unique_files'],0)
            self.assertEqual(stored['remaining_unique_files'],200)
            self.assertIn('queue_and_http',stored)
            self.assertEqual(data['state'],'running')
            self.assertEqual(progress_snapshot(db,state='stopped')['target_unique_files'],200)
    def test_periodic_progress_every_five_and_end(self):
        with tempfile.TemporaryDirectory() as d:
            db=connect(Path(d)/'index.db')
            import_resources(db,[{'resource_id':str(i),'url':f'https://demo{i}.example.org/a.pdf',
                                'file_candidate':True} for i in range(13)])
            args=SimpleNamespace(min_delay=10,max_file_mb=25,spool=str(Path(d)/'spool'),
                limit_success=12,max_checks=13,spool_max_gb=2,max_retries=3,
                seed_limit=50,backup_every=25,progress_every=5)
            seen=[]
            path=Path(d)/'reports'/'live.json'
            def callback(conn,state):
                data=write_progress(conn,path,state=state,target=12)
                seen.append((state,data['verified_unique_files']))
            uploader=FakeUploader()
            self.assertEqual(run_pilot(db,args,uploader,worker=FakeWorker(),progress_callback=callback),
                             'limit_reached')
            self.assertEqual(completed(db),12)
            self.assertEqual(seen,[('running',0),('running',5),('running',10),
                                  ('limit_reached',12)])
            self.assertEqual(json.loads(path.read_text())['verified_unique_files'],12)
            self.assertEqual(uploader.count,12)
    def test_progress_write_error_is_audited_and_not_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            db=connect(Path(d)/'index.db')
            import_resources(db,[{'resource_id':'x','url':'https://example.org/a.pdf',
                                  'file_candidate':True}])
            args=SimpleNamespace(min_delay=10,max_file_mb=25,spool=str(Path(d)/'spool'),
                limit_success=1,max_checks=2,spool_max_gb=2,max_retries=3,
                seed_limit=50,backup_every=25,progress_every=5)
            def bad_callback(conn,state):
                raise PermissionError('Drive temporarily offline')
            self.assertEqual(run_pilot(db,args,FakeUploader(),worker=FakeWorker(),
                                      progress_callback=bad_callback),'limit_reached')
            self.assertEqual(completed(db),1)
            count=db.execute("SELECT COUNT(*) FROM events WHERE kind='live_progress_error'").fetchone()[0]
            self.assertEqual(count,2)

if __name__=='__main__':
    unittest.main()
