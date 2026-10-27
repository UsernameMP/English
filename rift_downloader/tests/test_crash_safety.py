import tempfile
import unittest
from pathlib import Path
from rift_downloader.db import connect,import_resources,set_status,exclusive_runner
from rift_downloader.cli import cleanup_orphans

class CrashSafetyTests(unittest.TestCase):
    def test_single_runner_lock_rejects_overlapping_instances(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'state.sqlite3'
            with exclusive_runner(path):
                with self.assertRaisesRegex(RuntimeError,'already active'):
                    with exclusive_runner(path):
                        pass
            with exclusive_runner(path):
                pass
    def test_cleanup_preserves_staged_original_and_removes_abandoned_transfers(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=connect(Path(tmp)/'state.sqlite3')
            spool=Path(tmp)/'spool';spool.mkdir()
            good=spool/('a'*64)
            good.write_bytes(b'%PDF-1.7 preserved')
            for name in ('.downloading-1','.index-backup-2.sqlite3','b'*64):
                (spool/name).write_bytes(b'orphan')
            import_resources(db,[{'resource_id':'r1','url':'https://example.org/a.pdf'}])
            set_status(db,'r1','staged',sha='a'*64,path=str(good),filename='a.pdf')
            self.assertEqual(cleanup_orphans(db,spool),3)
            self.assertEqual(good.read_bytes(),b'%PDF-1.7 preserved')
            self.assertEqual(list(spool.iterdir()),[good])
            self.assertEqual(cleanup_orphans(db,spool),0)

if __name__=='__main__':
    unittest.main()
