"""End-to-end 200-file Colab backend pilot without internet or OAuth."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from rift_downloader.db import connect,import_resources,completed
from rift_downloader.cli import run_pilot
from rift_downloader.mounted_drive import MountedDriveUploader,reconcile_receipts,restore_index_snapshot

class DeterministicWorker:
    def fetch(self,url,spool):
        data=b'%PDF-1.7\n'+url.encode('utf-8')
        sha=hashlib.sha256(data).hexdigest()
        target=Path(spool)/sha
        target.write_bytes(data)
        return {'outcome':'staged','sha256':sha,'path':str(target),
                'filename':'olympiad.pdf','mime':'application/pdf',
                'http_status':200,'bytes_received':len(data),
                'elapsed_ms':15,'wait_ms':10000}

class ColabEndToEndTests(unittest.TestCase):
    def test_200_original_files_200_receipts_and_resume_without_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            top=Path(tmp)
            root=top/'MyDrive'/'RIFT';root.parent.mkdir()
            db_path=top/'run.sqlite3'
            db=connect(db_path)
            data=[{'resource_id':f'{i:05d}',
                   'url':f'https://school{i}.example.org/problems/{i}.pdf',
                   'first_source_url':f'https://school{i}.example.org/problems/',
                   'file_candidate':True} for i in range(205)]
            import_resources(db,data)
            uploader=MountedDriveUploader(root)
            args=SimpleNamespace(min_delay=10,max_file_mb=50,spool=str(top/'spool'),
                                 limit_success=200,max_checks=205,spool_max_gb=5,
                                 max_retries=4,backup_every=25,seed_limit=5000)
            self.assertEqual(run_pilot(db,args,uploader,worker=DeterministicWorker()),'limit_reached')
            self.assertEqual(completed(db),200)
            self.assertEqual(len(list(root.glob('raw/*/*.pdf'))),200)
            self.assertEqual(len(list(root.glob('receipts/*.json'))),200)
            self.assertEqual(len(list(root.glob('index/*.sqlite3'))),8)
            db.close()
            # An entirely new Colab runtime has no local working SQLite file.
            db_path.unlink()
            restored=restore_index_snapshot(root,db_path)
            self.assertTrue(restored['restored'])
            db=connect(db_path)
            self.assertEqual(completed(db),200)
            self.assertEqual(reconcile_receipts(db,root)['verified_receipts'],200)
            self.assertEqual(run_pilot(db,args,MountedDriveUploader(root),worker=DeterministicWorker()),'limit_reached')
            self.assertEqual(len(list(root.glob('raw/*/*.pdf'))),200)
            self.assertEqual(completed(db),200)

if __name__=='__main__':
    unittest.main()
