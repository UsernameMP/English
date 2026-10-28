"""Pilot seed tests: deterministic one-host-per-round scheduling and no re-seeding."""
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlparse

from rift_downloader.db import connect,import_resources,claim,recover
from rift_downloader.pilot_sample import seed_pilot

class PilotSamplingTests(unittest.TestCase):
    def _make(self, db, hosts=8, per_host=4):
        rows=[]
        for host_index in range(hosts):
            for i in range(per_host):
                rows.append({'resource_id':f'{host_index:03d}-{i:02d}',
                             'url':f'https://test{host_index}.example.org/paper{i}.pdf',
                             'file_candidate':True})
        rows.append({'resource_id':'html-only','url':'https://other.example.org/page.html',
                     'file_candidate':False})
        import_resources(db,rows)
    def test_first_round_uses_different_hosts(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'pilot.sqlite3'
            db=connect(path);self._make(db,hosts=8,per_host=4)
            result=seed_pilot(db,limit=20)
            self.assertEqual(result['seeded'],20)
            self.assertEqual(result['hosts'],8)
            self.assertFalse(result['existing'])
            seen=[]
            for _ in range(8):
                r=claim(db,now=9999999999)
                seen.append(urlparse(r['url']).hostname)
            self.assertEqual(len(set(seen)),8)
            self.assertEqual(seed_pilot(db,limit=22),{'seeded':20,'existing':True})
            db.close()
            db=connect(path)
            for _ in range(8):
                r=claim(db,now=9999999999)
                seen.append(urlparse(r['url']).hostname)
            self.assertEqual(len(set(seen[8:])),8)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM resources WHERE pilot_rank IS NOT NULL").fetchone()[0],20)
            self.assertIsNone(db.execute("SELECT pilot_rank FROM resources WHERE resource_id='html-only'").fetchone()[0])
    def test_candidates_from_known_mime_without_file_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            db=connect(Path(directory)/'state.sqlite3')
            import_resources(db,[
                {'resource_id':'doc','url':'https://abc.example.org/download?id=2',
                 'mime':'application/pdf','file_candidate':False},
                {'resource_id':'web','url':'https://abc.example.org/page',
                 'file_candidate':False},
            ])
            self.assertEqual(seed_pilot(db,limit=5)['seeded'],1)
            self.assertEqual(claim(db)['resource_id'],'doc')
    def test_no_documents_keeps_unranked_queue_available(self):
        with tempfile.TemporaryDirectory() as directory:
            db=connect(Path(directory)/'state.sqlite3')
            import_resources(db,[{'resource_id':'web','url':'https://abc.example.org/'}])
            self.assertEqual(seed_pilot(db)['seeded'],0)
            self.assertEqual(claim(db)['resource_id'],'web')

if __name__=='__main__':
    unittest.main()
