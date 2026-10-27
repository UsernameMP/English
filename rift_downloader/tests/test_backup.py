import sqlite3
import tempfile
import unittest
from pathlib import Path
from rift_downloader.db import connect,import_resources
from rift_downloader.backup import backup_index,last_backup_count

class IndexBackupTests(unittest.TestCase):
    def test_online_snapshot_contains_queue_and_has_verifiable_drive_id(self):
        class FakeDrive:
            def __init__(self):self.calls=[]
            def upload(self,sha,path,mime,filename,*,category='raw'):
                self.calls.append((sha,mime,filename,category))
                source=sqlite3.connect(path)
                try:
                    assert source.execute('SELECT COUNT(*) FROM resources').fetchone()[0]==2
                finally:source.close()
                return 'drive-id-for-sqlite'
        with tempfile.TemporaryDirectory() as tmp:
            db=connect(Path(tmp)/'state.sqlite3')
            import_resources(db,[{'resource_id':'a','url':'https://example.org/a.pdf'},
                                 {'resource_id':'b','url':'https://example.org/b.zip'}])
            drive=FakeDrive()
            result=backup_index(db,drive,Path(tmp)/'spool')
            self.assertEqual(result['drive_file_id'],'drive-id-for-sqlite')
            self.assertEqual(drive.calls[0][3],'index')
            self.assertEqual(last_backup_count(db),0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events WHERE kind='index_backup'").fetchone()[0],1)
            self.assertFalse(list((Path(tmp)/'spool').glob('.index-backup-*')))
    def test_failed_backup_preserves_db_and_cleans_temp_snapshot(self):
        class FailingDrive:
            def upload(self,*args,**kwargs):raise RuntimeError('quota exceeded')
        with tempfile.TemporaryDirectory() as tmp:
            db=connect(Path(tmp)/'state.sqlite3')
            with self.assertRaises(RuntimeError):
                backup_index(db,FailingDrive(),Path(tmp)/'spool')
            self.assertFalse(list((Path(tmp)/'spool').glob('.index-backup-*')))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM resources').fetchone()[0],0)
if __name__=='__main__':unittest.main()
