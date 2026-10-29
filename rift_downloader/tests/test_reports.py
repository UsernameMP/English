import csv
import json
import tempfile
import unittest
from pathlib import Path
from rift_downloader.db import connect,import_resources,begin_attempt,finish_attempt,set_status
from rift_downloader.report import export_report

class ReportingTests(unittest.TestCase):
    def test_export_traceable_manifest_attempts_host_timing_and_failures(self):
        with tempfile.TemporaryDirectory() as td:
            db=connect(Path(td)/'data.sqlite3')
            import_resources(db,[
                {'resource_id':'pdf1','url':'https://math.example.org/task.pdf',
                 'first_source_url':'https://math.example.org/archive/'},
                {'resource_id':'x2','url':'https://math.example.org/private.pdf'},
            ])
            with db:
                db.execute('''INSERT INTO objects(sha256,size_bytes,mime_type,drive_file_id,verified_at)
                              VALUES (?,?,?,?,?)''',('a'*64,100,'application/pdf','drive-123',12345.))
            set_status(db,'pdf1','completed',sha='a'*64)
            set_status(db,'x2','blocked',error='robots disallow')
            id1=begin_attempt(db,'pdf1','math.example.org')
            finish_attempt(db,id1,elapsed_ms=120,wait_ms=10000,code=200,size=100,outcome='staged')
            id2=begin_attempt(db,'x2','math.example.org')
            finish_attempt(db,id2,elapsed_ms=500,wait_ms=0,code=429,outcome='retry',error='HTTP 429')
            report=export_report(db,Path(td)/'pilot.json')
            self.assertEqual(len(report),8)
            self.assertIn('url_ledger_csv',report)
            result=json.loads(Path(report['summary_json']).read_text())
            self.assertEqual(result['host_count'],1)
            self.assertEqual(result['hosts_with_429'],1)
            with open(report['manifest_csv'],newline='',encoding='utf-8') as f:
                records=list(csv.DictReader(f))
            self.assertEqual(len(records),1)
            self.assertEqual(records[0]['resource_id'],'pdf1')
            self.assertEqual(records[0]['drive_file_id'],'drive-123')
            self.assertEqual(records[0]['source_url'],'https://math.example.org/archive/')
            with open(report['attempts_csv'],newline='',encoding='utf-8') as f:
                attempts=list(csv.DictReader(f))
            self.assertEqual([x['http_status'] for x in attempts],['200','429'])
            with open(report['hosts_csv'],newline='',encoding='utf-8') as f:
                hosts=list(csv.DictReader(f))
            self.assertEqual(hosts[0]['avg_latency_ms'],'310')
            self.assertEqual(hosts[0]['http_429'],'1')
            self.assertTrue(Path(report['http_events_csv']).is_file())
            self.assertTrue(Path(report['http_hosts_csv']).is_file())
            with open(report['noncompleted_csv'],newline='',encoding='utf-8') as f:
                failures=list(csv.DictReader(f))
            self.assertEqual(failures[0]['status'],'blocked')

if __name__=='__main__':
    unittest.main()
