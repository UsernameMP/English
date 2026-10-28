import tempfile
import unittest
from pathlib import Path
from rift_downloader.http import kind,PoliteHttp,RateLimiter
from rift_downloader.tests.test_integration import FakeResponse,FakeSession

class ImageDeferralTests(unittest.TestCase):
    def test_images_are_deferred_even_if_server_claims_pdf(self):
        png=b'\x89PNG\r\n\x1a\n'+b'ABC'*50
        self.assertEqual(kind('application/pdf','https://example.org/data.pdf',png)[0],'image')
        self.assertEqual(kind('image/png','https://example.org/download',png)[0],'image')
        with tempfile.TemporaryDirectory() as d:
            session=FakeSession([FakeResponse(404,mime='text/plain'),
                                 FakeResponse(200,png,mime='application/pdf')])
            worker=PoliteHttp(session=session,limiter=RateLimiter(0,sleep=lambda _:None),dns_check=False)
            result=worker.fetch('https://example.org/data.pdf',d)
            self.assertEqual(result['outcome'],'image_deferred')
            self.assertFalse(list(Path(d).iterdir()))
    def test_real_pdf_magic_wins_over_misleading_image_header(self):
        payload=b'%PDF-1.7\n'+b'test'
        self.assertEqual(kind('image/png','https://example.org/document.png',payload),
                         ('file','application/pdf'))
    def test_webp_vs_riff_audio(self):
        self.assertEqual(kind('application/octet-stream','https://example.org/a',b'RIFFabcdWEBPVP8 ')[0],'image')
        self.assertNotEqual(kind('application/octet-stream','https://example.org/a',b'RIFFabcdWAVEfmt ')[0],'image')

if __name__=='__main__':
    unittest.main()
