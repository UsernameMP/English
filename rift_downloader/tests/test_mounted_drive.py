"""No-network tests for mounted Google Drive data and index recovery."""
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from rift_downloader.backup import backup_index
from rift_downloader.db import connect,import_resources,completed
from rift_downloader.mounted_drive import (
    MountedDriveUploader, MountedDriveError,
    hash_file, reconcile_receipts, restore_index_snapshot)

class MountedDriveTests(unittest.TestCase):
    def test_original_bytes_and_receipt_recover_index_after_interruption(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'MyDrive'/'RIFT'
            root.parent.mkdir(parents=True)
            work=Path(td)/'work';work.mkdir()
            staged=work/'source.pdf';data=b'%PDF-1.7\nGeometry diagram\n'*10
            staged.write_bytes(data)
            sha=hashlib.sha256(data).hexdigest()
            db=connect(work/'state.db')
            record={'resource_id':'abc123','url':'https://math.example.org/geometry.pdf',
                    'first_source_url':'https://math.example.org/contests/'}
            import_resources(db,[record])
            row=db.execute('SELECT * FROM resources WHERE resource_id=?',('abc123',)).fetchone()
            uploader=MountedDriveUploader(root)
            uploader.set_context(row)
            ref=uploader.upload(sha,staged,'application/pdf','geometry.pdf')
            self.assertEqual(ref,'drivefs:raw/'+sha[:2]+'/'+sha+'.pdf')
            self.assertEqual(hash_file(root/'raw'/sha[:2]/(sha+'.pdf')),(sha,len(data)))
            receipt=json.loads((root/'receipts'/'abc123.json').read_text())
            self.assertEqual(receipt['url'],record['url'])
            self.assertEqual(receipt['source_url'],record['first_source_url'])
            self.assertEqual(receipt['archive_state'],'verified')
            # VPS/Colab process was killed after remote file verified and BEFORE
            # local SQLite commit. New local index should recover from receipts.
            db.close()
            other=connect(work/'new-state.db')
            import_resources(other,[record])
            recovery=reconcile_receipts(other,root)
            self.assertEqual(recovery['verified_receipts'],1)
            self.assertEqual(recovery['restored_links'],1)
            self.assertEqual(completed(other),1)
            self.assertEqual(other.execute('SELECT status FROM resources').fetchone()[0],'completed')
            uploader2=MountedDriveUploader(root)
            uploader2.set_context(row)
            self.assertEqual(uploader2.upload(sha,staged,'application/pdf','geometry.pdf'),ref)
            self.assertEqual(len(list((root/'raw'/sha[:2]).iterdir())),1)
    def test_existing_mismatched_content_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'RIFT';root.mkdir()
            source=Path(td)/'paper.zip';source.write_bytes(b'PK\x03\x04original')
            sha=hashlib.sha256(source.read_bytes()).hexdigest()
            remote=root/'raw'/sha[:2]/(sha+'.zip')
            remote.parent.mkdir(parents=True)
            remote.write_bytes(b'wrong file content')
            with self.assertRaises(MountedDriveError):
                MountedDriveUploader(root).upload(sha,source,'application/zip','paper.zip')
            self.assertEqual(remote.read_bytes(),b'wrong file content')
            self.assertEqual(source.read_bytes(),b'PK\x03\x04original')
    def test_same_file_different_extensions_uses_one_blob_and_two_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'RIFT';root.mkdir()
            source=Path(td)/'pdf';data=b'%PDF-1.5\nSame problem'
            source.write_bytes(data);sha=hashlib.sha256(data).hexdigest()
            db=connect(Path(td)/'state.db')
            import_resources(db,[
                {'resource_id':'first','url':'https://math.example.org/file.pdf',
                 'first_source_url':'https://math.example.org/archive'},
                {'resource_id':'second','url':'https://other.example.org/download',
                 'first_source_url':'https://other.example.org/index'}])
            uploader=MountedDriveUploader(root)
            first=db.execute("SELECT * FROM resources WHERE resource_id='first'").fetchone()
            uploader.set_context(first)
            ref=uploader.upload(sha,source,'application/pdf','source.pdf')
            second=db.execute("SELECT * FROM resources WHERE resource_id='second'").fetchone()
            uploader.set_context(second)
            again=uploader.upload(sha,source,'application/pdf','download.zip')
            self.assertEqual(again,ref)
            uploader.record_existing(second,sha,ref)
            self.assertEqual(len(list((root/'raw'/sha[:2]).iterdir())),1)
            self.assertEqual(len(list((root/'receipts').glob('*.json'))),2)
            self.assertEqual(json.loads((root/'receipts'/'second.json').read_text())['url'],
                             'https://other.example.org/download')
    def test_index_snapshot_can_be_restored_to_local_sqlite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'RIFT';root.mkdir()
            local=Path(td)/'local.db'
            db=connect(local)
            import_resources(db,[{'resource_id':'a','url':'https://math.example.org/task.pdf'}])
            uploader=MountedDriveUploader(root)
            snap=backup_index(db,uploader,Path(td)/'spool')
            self.assertTrue(snap['drive_file_id'].startswith('drivefs:index/'))
            db.close()
            local.unlink()
            restored=restore_index_snapshot(root,local)
            self.assertTrue(restored['restored'])
            self.assertEqual(connect(local).execute('SELECT COUNT(*) FROM resources').fetchone()[0],1)
    def test_unsafe_resource_id_and_sha_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'RIFT';root.mkdir()
            file=Path(td)/'file';file.write_bytes(b'abc')
            sha=hashlib.sha256(file.read_bytes()).hexdigest()
            uploader=MountedDriveUploader(root)
            uploader.set_context({'resource_id':'../evil','url':'https://example.org'})
            with self.assertRaises(MountedDriveError):
                uploader.upload(sha,file,'application/pdf','task.pdf')
            with self.assertRaises(MountedDriveError):
                uploader.upload('unsafe',file,'application/pdf','task.pdf')

if __name__=='__main__':
    unittest.main()
