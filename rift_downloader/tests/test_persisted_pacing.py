"""Durable pacing and request telemetry, including after simulated process restart."""
import tempfile
import unittest
from pathlib import Path
from rift_downloader.db import connect,record_http_event
from rift_downloader.http import RateLimiter

class DurablePacingTests(unittest.TestCase):
    def test_restart_preserves_cooldown_and_full_robots_delay(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'queue.sqlite3'
            tick=[1000.]
            def sleep(t):tick[0]+=t
            make=lambda db:RateLimiter(10,clock=lambda:tick[0],wall_clock=lambda:tick[0],sleep=sleep,state=db)
            db=connect(path)
            self.assertEqual(make(db).wait('archive.example.org'),0)
            state=db.execute("SELECT next_allowed_at FROM host_pacing WHERE host='archive.example.org'").fetchone()
            self.assertEqual(state[0],1010.)
            db.close()
            tick[0]=1001.
            second=connect(path)
            self.assertEqual(make(second).wait('archive.example.org',minimum=20),19000)
            self.assertEqual(tick[0],1020.)
            limiter=make(second)
            limiter.postpone('archive.example.org',60)
            second.close()
            tick[0]=1030.
            third=connect(path)
            self.assertEqual(make(third).wait('archive.example.org'),50000)
            self.assertEqual(tick[0],1080.)
    def test_write_every_response_to_http_events(self):
        with tempfile.TemporaryDirectory() as directory:
            db=connect(Path(directory)/'queue.sqlite3')
            record_http_event(db,'https://example.org/robots.txt','example.org','robots',200,12,10000)
            record_http_event(db,'https://example.org/file.pdf','example.org','resource',429,52,10000)
            rows=db.execute('SELECT purpose,http_status,wait_ms FROM http_events ORDER BY id').fetchall()
            self.assertEqual([tuple(r) for r in rows],[('robots',200,10000),('resource',429,10000)])

if __name__=='__main__':
    unittest.main()
