"""Loopback HTTP fixture for end-to-end stream tests. Production SSRF checks remain enabled."""
import tempfile
import threading
import unittest
from http.server import HTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
import requests
from rift_downloader.db import connect,record_http_event
from rift_downloader.http import PoliteHttp,RateLimiter

PDF=b'%PDF-1.7\n1 0 obj\n<</Type /Catalog>>\nendobj\n%%EOF\n'

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        if self.path=='/robots.txt':
            data=b'User-agent: *\nDisallow: /private\n'
            code=200;mime='text/plain';extra={}
        elif self.path=='/task':
            data=PDF;code=200;mime='application/octet-stream';extra={}
        elif self.path=='/html':
            data=b'<html><body>Olympiad problem with a picture</body></html>'
            code=200;mime='text/html';extra={}
        elif self.path=='/redirect':
            data=b'';code=302;mime='text/plain';extra={'Location':'/task'}
        elif self.path=='/limited':
            data=b'';code=429;mime='text/plain';extra={'Retry-After':'30'}
        else:
            data=b'';code=404;mime='text/plain';extra={}
        self.send_response(code)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(data)))
        for k,v in extra.items():self.send_header(k,v)
        self.end_headers()
        if data:self.wfile.write(data)

class RewritingSession(requests.Session):
    """Explicit TEST-ONLY fake DNS mapping; never used by downloader production code."""
    def __init__(self,base):
        super().__init__()
        self.base=base
    def get(self,url,**kwargs):
        path=urlsplit(url)
        assert path.hostname=='archive.example.org',url
        assert path.scheme=='https',url
        return super().get(self.base+path.path,**kwargs)

class LocalHTTPFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=HTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
    def test_real_socket_pdf_html_redirect_robots_and_http429(self):
        with tempfile.TemporaryDirectory() as d:
            db=connect(Path(d)/'ledger.db')
            session=RewritingSession('http://127.0.0.1:'+str(self.server.server_port))
            limiter=RateLimiter(delay=0,state=db)
            seen=lambda url,host,purpose,code,elapsed,wait:record_http_event(db,url,host,purpose,code,elapsed,wait)
            worker=PoliteHttp(session=session,limiter=limiter,dns_check=False,on_response=seen)
            spool=Path(d)/'spool'
            url='https://archive.example.org'
            first=worker.fetch(url+'/task',spool)
            self.assertEqual(first['outcome'],'staged')
            self.assertEqual(first['mime'],'application/pdf')
            self.assertEqual(Path(first['path']).read_bytes(),PDF)
            second=worker.fetch(url+'/html',spool)
            self.assertEqual(second['outcome'],'html_deferred')
            redirect=worker.fetch(url+'/redirect',spool)
            self.assertEqual(redirect['outcome'],'staged')
            denied=worker.fetch(url+'/private/data.pdf',spool)
            self.assertEqual(denied['outcome'],'blocked')
            limited=worker.fetch(url+'/limited',spool)
            self.assertEqual(limited['outcome'],'retry')
            self.assertEqual(limited['retry_after'],30)
            rows=db.execute('SELECT purpose,http_status,url FROM http_events ORDER BY id').fetchall()
            codes=[r['http_status'] for r in rows]
            self.assertEqual(codes,[200,200,200,302,200,429])
            self.assertEqual(rows[0]['purpose'],'robots')
            self.assertFalse(any('/private/data.pdf' in r['url'] for r in rows))

if __name__=='__main__':
    unittest.main()
