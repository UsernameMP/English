"""The ordered index is authoritative, even after a prior 200-file pilot.

All tests are offline; they verify that newly PREPENDED source URLs win over
the original pilot ranks and that historical SHA-256/Drive records survive.
"""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from rift_downloader.db import connect,import_resources,claim
from rift_downloader.ordered_master import (
    MasterError,iter_master,sync_ordered_master,lookup_resource,resolve_sources)
from rift_downloader.cli import main
from rift_downloader.report import export_report

def lines(path,objects):
    with path.open('w',encoding='utf-8') as output:
        for item in objects:
            output.write(json.dumps(item,ensure_ascii=False)+'\n')

def sample(url,resource_id=None):
    value={'url':url,'file_candidate':True,'first_source_url':'https://archive.org/index'}
    if resource_id:value['resource_id']=resource_id
    return value

class MasterOrderTests(unittest.TestCase):
    def test_new_links_prepended_take_absolute_priority_and_preserve_old_200(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            db=connect(base/'master.sqlite3')
            u1='https://example.org/old_1.pdf'
            u2='https://example.org/old_2.pdf'
            new1='https://new.example.org/a.pdf'
            new2='https://new.example.org/b.pdf'
            import_resources(db,[sample(u1,'original1'),sample(u2,'original2')])
            # Old pilot had a high-priority pilot_rank, but new order must win.
            db.execute("UPDATE resources SET pilot_rank=1 WHERE resource_id='original2'")
            sha=hashlib.sha256(b'%PDF-1.7 saved').hexdigest()
            db.execute("""INSERT INTO objects(sha256,size_bytes,mime_type,drive_file_id,verified_at)
                VALUES (?,?,?,?,?)""",(sha,14,'application/pdf','drivefs:raw/aa/legacy.pdf',999))
            db.execute("UPDATE resources SET status='completed',object_sha256=?,attempts=1 WHERE resource_id='original1'",(sha,))
            master=base/'master.jsonl'
            lines(master,[sample(u1,'changed-id'),sample(u2,'original2')])
            self.assertEqual(sync_ordered_master(db,str(master))['master_rows'],2)
            lines(master,[sample(new1),sample(new2),sample(u1,'changed-id'),sample(u2,'original2')])
            outcome=sync_ordered_master(db,str(master))
            self.assertEqual(outcome['master_rows'],4)
            self.assertEqual([r['url'] for r in outcome['first_five']],[new1,new2,u1,u2])
            self.assertEqual(db.execute("SELECT status FROM resources WHERE url=?",(u1,)).fetchone()[0],'completed')
            self.assertEqual(db.execute("SELECT resource_id FROM resources WHERE url=?",(u1,)).fetchone()[0],'original1')
            self.assertEqual(db.execute("SELECT COUNT(*) FROM objects").fetchone()[0],1)
            self.assertEqual(claim(db,mode='ordered_new')['url'],new1)
            self.assertEqual(claim(db,mode='ordered_new')['url'],new2)
            self.assertEqual(claim(db,mode='ordered_new')['url'],u2)
            self.assertIsNone(claim(db,mode='ordered_new'))
            self.assertEqual(lookup_resource(db,position=3)[0]['object_sha256'],sha)
            self.assertEqual(lookup_resource(db,url=u1)[0]['source_position'],3)
            self.assertEqual(lookup_resource(db,sha=sha)[0]['url'],u1)
            exported=export_report(db,base/'report.json')
            ledger=Path(exported['url_ledger_csv']).read_text()
            self.assertIn(new1,ledger)
            self.assertIn('source_position',ledger.splitlines()[0])
            manifest=Path(exported['manifest_csv']).read_text()
            self.assertIn('original1',manifest)
            self.assertIn('source_position',manifest.splitlines()[0])

    def test_strict_order_survives_prepend_in_new_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            path=folder/'all.txt'
            path.write_text('https://x.example/a.pdf\nhttps://x.example/b.pdf\n')
            db=connect(folder/'db.sqlite3')
            first=sync_ordered_master(db,str(path))
            self.assertEqual(first['master_rows'],2)
            db.close()
            db=connect(folder/'db.sqlite3')
            path.write_text('https://fresh.example/critical.pdf\n'
                            'https://x.example/a.pdf\n'
                            'https://x.example/b.pdf\n')
            second=sync_ordered_master(db,str(path))
            self.assertEqual(second['master_rows'],3)
            self.assertEqual(claim(db,mode='ordered_new')['url'],
                             'https://fresh.example/critical.pdf')
            self.assertEqual(claim(db,mode='ordered_new')['url'],'https://x.example/a.pdf')

    def test_csv_and_earliest_duplicate_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'master.csv'
            with path.open('w',newline='',encoding='utf-8') as output:
                writer=csv.DictWriter(output,fieldnames=['url','file_candidate'])
                writer.writeheader()
                writer.writerow({'url':'https://first.org/x.pdf','file_candidate':'1'})
                writer.writerow({'url':'https://first.org/x.pdf','file_candidate':'1'})
                writer.writerow({'url':'https://second.org/y.pdf','file_candidate':'0'})
            db=connect(Path(tmp)/'db.sqlite3')
            r=sync_ordered_master(db,str(path))
            self.assertEqual(r['master_rows'],2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM resources WHERE source_position IS NOT NULL").fetchone()[0],2)
            self.assertEqual(claim(db,mode='ordered_new')['url'],'https://first.org/x.pdf')

    def test_missing_or_broken_master_rolls_back_preserving_existing_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            path=folder/'master.jsonl'
            lines(path,[sample('https://archive.org/file.pdf')])
            db=connect(folder/'db.sqlite3')
            sync_ordered_master(db,str(path))
            before=db.execute("SELECT source_position,url FROM resources").fetchone()
            path.write_text(json.dumps(sample('https://new.org/a.pdf'))+'\nNOT JSON\n')
            with self.assertRaises(MasterError):
                sync_ordered_master(db,str(path))
            after=db.execute("SELECT source_position,url FROM resources").fetchone()
            self.assertEqual(tuple(before),tuple(after))
            with self.assertRaises(MasterError):
                sync_ordered_master(db,str(folder/'missing.jsonl'))

    def test_removed_links_keep_history_but_are_not_scheduled(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            path=folder/'list.txt'
            path.write_text('https://a.org/removed.pdf\nhttps://b.org/active.pdf\n')
            db=connect(folder/'db.sqlite3')
            sync_ordered_master(db,str(path))
            path.write_text('https://b.org/active.pdf\n')
            sync_ordered_master(db,str(path))
            self.assertIsNone(lookup_resource(db,url='https://a.org/removed.pdf')[0]['source_position'])
            self.assertEqual(claim(db,mode='ordered_new')['url'],'https://b.org/active.pdf')
            self.assertIsNone(claim(db,mode='ordered_new'))

if __name__=='__main__':
    unittest.main()
