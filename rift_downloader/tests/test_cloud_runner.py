"""Offline checks for the GitHub Actions Drive-resume architecture."""
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from rift_downloader.cloud_runner import (
    CloudRunError,candidates,verify_snapshot,verify_token_scopes,actions_summary)
from rift_downloader.db import connect,import_resources,claim
from rift_downloader.ops_metrics import make_baseline

class Response:
    def __init__(self,func):self.func=func
    def execute(self):return self.func()

class FakeFiles:
    def __init__(self):
        self.calls=0
    def list(self,**kwargs):
        self.calls+=1
        if self.calls==1:
            return Response(lambda:{
                'files':[
                   {'id':'a','name':'a'*64+'.sqlite3','modifiedTime':'2026-10-27T12:00:00Z','size':'128000'},
                   {'id':'x','name':'other-user-data.txt','modifiedTime':'2026-10-29T12:00:00Z','size':'2000'}],
                'nextPageToken':'more'})
        self.assert_second=kwargs.get('page_token')
        return Response(lambda:{'files':[
            {'id':'b','name':'b'*64+'.sqlite3','modifiedTime':'2026-10-28T12:00:00Z','size':'129000'},
            {'id':'oversized','name':'c'*64+'.sqlite3','modifiedTime':'2026-10-29T12:00:00Z','size':str(600*1024*1024)}]})

class FakeService:
    def __init__(self):self.f=FakeFiles()
    def files(self):return self.f

class ResumeTests(unittest.TestCase):
    def test_snapshot_discovery_excludes_other_files_and_paginates(self):
        service=FakeService()
        selected=candidates(service,'existing-index-id')
        self.assertEqual([x['id'] for x in selected],['b','a'])
        self.assertEqual(service.f.assert_second,'more')
    def test_sqlite_verified_only_after_sha_and_quick_check(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'state.sqlite3'
            db=connect(path)
            import_resources(db,[{'resource_id':'id','url':'https://example.org/task.pdf'}])
            db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            db.close()
            sha=hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(verify_snapshot(path,sha+'.sqlite3'),1)
            with self.assertRaises(CloudRunError):
                verify_snapshot(path,'0'*64+'.sqlite3')
    def test_requiring_existing_colab_access_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'token.json'
            path.write_text(json.dumps({'scopes':['https://www.googleapis.com/auth/drive.file']}))
            with self.assertRaises(CloudRunError):
                verify_token_scopes(path)
            path.write_text(json.dumps({'scopes':['https://www.googleapis.com/auth/drive']}))
            self.assertEqual(verify_token_scopes(path),['https://www.googleapis.com/auth/drive'])
    def test_queues_are_distinct_and_summary_never_contains_token(self):
        with tempfile.TemporaryDirectory() as directory:
            db=connect(Path(directory)/'db.sqlite3')
            import_resources(db,[
                {'resource_id':'a','url':'https://a.example.org/a.pdf'},
                {'resource_id':'b','url':'https://b.example.org/b.pdf'}])
            first=claim(db,mode='new')
            self.assertEqual(first['resource_id'],'a')
            self.assertIsNone(claim(db,mode='retry'))
            db.execute("UPDATE resources SET status='retry' WHERE resource_id='a'")
            self.assertEqual(claim(db,mode='new')['resource_id'],'b')
            self.assertEqual(claim(db,mode='retry')['resource_id'],'a')
        text=actions_summary(make_baseline(),'user-owned-folder',None)
        self.assertIn('328',text)
        self.assertIn('200',text)
        self.assertNotIn('refresh_token',text)

if __name__=='__main__':unittest.main()
