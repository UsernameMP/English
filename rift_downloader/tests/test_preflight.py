"""Preflight and CLI tests: no credentials or real HTTP required."""
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from rift_downloader.db import connect,import_resources
from rift_downloader.preflight import preflight
from rift_downloader.cli import main

class PreflightTests(unittest.TestCase):
    def test_checks_queue_and_missing_token_without_leaking_secrets(self):
        with tempfile.TemporaryDirectory() as root:
            db=connect(Path(root)/'sqlite.db')
            p=preflight(db,Path(root)/'missing.json',root)
            self.assertFalse(p['ready'])
            self.assertFalse(p['checks']['queue_imported']['ok'])
            self.assertFalse(p['checks']['drive_oauth']['ok'])
            import_resources(db,[{'resource_id':'x','url':'https://example.org/a.pdf',
                                  'file_candidate':True}])
            token=Path(root)/'token.json'
            secret='never-print-this-secret-8544'
            token.write_text(json.dumps({'refresh_token':secret,'client_id':'hidden',
                'scopes':['https://www.googleapis.com/auth/drive.file']}))
            token.chmod(0o600)
            okay=preflight(db,token,root)
            self.assertTrue(okay['ready'])
            self.assertNotIn(secret,str(okay))
            token.chmod(0o644)
            rejected=preflight(db,token,root)
            self.assertFalse(rejected['ready'])
            self.assertEqual(rejected['checks']['drive_oauth']['private_file'],False)
            token.chmod(0o600)
            token.write_text(json.dumps({'refresh_token':secret,'scopes':['https://www.googleapis.com/auth/drive.readonly']}))
            self.assertFalse(preflight(db,token,root)['ready'])
    def test_dry_run_needs_no_google_token(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'db.sqlite3'
            db=connect(path)
            import_resources(db,[{'resource_id':'p','url':'https://example.org/a.pdf'}])
            out=StringIO()
            with redirect_stdout(out):
                main(['--db',str(path),'run','--dry-run'])
            report=json.loads(out.getvalue())
            self.assertTrue(report['dry_run'])
            self.assertEqual(report['network_requests'],0)
            self.assertEqual(report['report']['uploaded_files'],0)

if __name__=='__main__':
    unittest.main()
