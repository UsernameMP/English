"""User-requested URL cap and privacy-safe dashboard regression tests."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from rift_downloader.db import connect,import_resources,completed,summary
from rift_downloader.cli import run_pilot
from rift_downloader.ops_metrics import build_metrics,render_html,make_baseline,write_dashboard

class FakeWorker:
    def __init__(self):self.urls=[]
    def fetch(self,url,spool):
        self.urls.append(url)
        if url.endswith('/not-found.pdf'):
            return {'outcome':'skipped','http_status':404,'error':'HTTP 404'}
        body=b'%PDF-1.5\n'+url.encode()
        digest=hashlib.sha256(body).hexdigest()
        target=Path(spool)/digest
        target.write_bytes(body)
        return {'outcome':'staged','sha256':digest,'path':str(target),
                'filename':'paper.pdf','mime':'application/pdf','bytes_received':len(body),
                'elapsed_ms':25,'wait_ms':0,'http_status':200}

class FakeDrive:
    def __init__(self):self.uploaded=set()
    def upload(self,sha,path,mime,filename,*,category='raw'):
        self.uploaded.add(sha)
        return 'test-drive-'+sha[:12]

class ControlCenterTests(unittest.TestCase):
    def args(self,path,limit_urls=None,success=200):
        return SimpleNamespace(min_delay=10,max_file_mb=1,spool=str(path/'spool'),
            limit_success=success,limit_urls=limit_urls,
            max_checks=100,spool_max_gb=2,max_retries=2,backup_every=0,seed_limit=5000,
            progress_every=1)
    def test_200_URLs_vs_200_files_are_different_semantics(self):
        with tempfile.TemporaryDirectory() as path:
            path=Path(path);db=connect(path/'state.db')
            resources=[{'resource_id':f'{i:04}', 'url':f'https://archive{i}.example.org/paper.pdf'
                        if i%3 else f'https://archive{i}.example.org/not-found.pdf',
                        'file_candidate':True} for i in range(20)]
            import_resources(db,resources)
            worker=FakeWorker()
            uploader=FakeDrive()
            status=run_pilot(db,self.args(path,limit_urls=7,success=1),uploader,worker=worker)
            self.assertEqual(status,'url_limit_reached')
            self.assertEqual(db.execute('SELECT COUNT(DISTINCT resource_id) FROM attempts').fetchone()[0],7)
            self.assertEqual(len(worker.urls),7)
            self.assertLess(completed(db),7)
            self.assertGreaterEqual(completed(db),1)
            again=run_pilot(db,self.args(path,limit_urls=5,success=1),uploader,worker=worker)
            self.assertEqual(again,'url_limit_reached')
            self.assertEqual(len(worker.urls),12)
            self.assertEqual(db.execute('SELECT COUNT(DISTINCT resource_id) FROM attempts').fetchone()[0],12)
    def test_live_metrics_have_distinct_attempts_sources_and_no_urls(self):
        with tempfile.TemporaryDirectory() as path:
            path=Path(path);db=connect(path/'state.db')
            url='https://private.example.org/never-publish-this.pdf'
            import_resources(db,[{'resource_id':'0','url':url,'file_candidate':True}])
            worker=FakeWorker()
            run_pilot(db,self.args(path,limit_urls=1),FakeDrive(),worker=worker)
            metrics=build_metrics(db,run_state='complete',limit_new_urls=1)
            self.assertEqual(metrics['metrics']['unique_urls_checked'],1)
            self.assertEqual(metrics['metrics']['total_url_attempts'],1)
            self.assertEqual(metrics['metrics']['unique_files'],1)
            self.assertNotIn(url,json.dumps(metrics))
            self.assertIn('http_404',metrics['metrics'])
            html_output=render_html(metrics)
            self.assertIn('<title>RIFT / Downloader Control</title>',html_output)
            self.assertNotIn(url,html_output)
    def test_baseline_matches_observed_200_file_pilot_and_safe_html(self):
        data=make_baseline()
        self.assertEqual(data['metrics']['unique_urls_checked'],328)
        self.assertEqual(data['metrics']['unique_files'],200)
        self.assertEqual(data['metrics']['http_requests'],817)
        self.assertEqual(sum(data['mime_types'].values()),200)
        data['source']='x</script><script>alert("oops")</script>'
        output=render_html(data)
        self.assertEqual(output.count('<script'),2) # JSON + app JS; injected tags are escaped.
        self.assertIn(r'\u003c/script\u003e',output)
        with tempfile.TemporaryDirectory() as path:
            html_path=Path(path)/'dashboard.html'
            json_path=Path(path)/'status.json'
            write_dashboard(data,html_path,json_path)
            self.assertTrue(html_path.is_file())
            self.assertEqual(json.loads(json_path.read_text())['metrics']['unique_files'],200)

if __name__=='__main__':unittest.main()
