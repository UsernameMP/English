import tempfile
import unittest
from pathlib import Path
from rift_downloader.db import connect,import_resources
from rift_downloader.inventory import inventory,predicted_type

class InventoryTests(unittest.TestCase):
    def test_known_mime_wins_over_extension_and_extensionless_file_counted(self):
        self.assertEqual(predicted_type('https://example.org/file?id=123','application/pdf'),'pdf')
        self.assertEqual(predicted_type('https://example.org/report.docx',None),'word')
        self.assertEqual(predicted_type('https://example.org/report','text/html'),'html_likely')
        with tempfile.TemporaryDirectory() as tmp:
            db=connect(Path(tmp)/'state.sqlite3')
            import_resources(db,[
                {'resource_id':'a','url':'https://archive.example.org/123?download=true',
                 'mime':'application/pdf','file_candidate':True},
                {'resource_id':'b','url':'https://archive.example.org/batch.zip',
                 'file_candidate':True},
                {'resource_id':'c','url':'https://else.example.org/archive.html'},
                {'resource_id':'d','url':'https://else.example.org/nonsense'}])
            result=inventory(db,sample=3)
            self.assertEqual(result['total_urls'],4)
            self.assertEqual(result['estimated_file_urls'],2)
            self.assertEqual(result['by_prediction']['pdf'],1)
            self.assertEqual(result['by_prediction']['archive'],1)
            self.assertEqual(result['prior_flagged_file_candidates'],2)
            self.assertEqual(result['candidate_hosts'],1)
            self.assertEqual(result['total_hosts'],2)
            self.assertEqual(len(result['sample_candidate_urls']),2)

if __name__=='__main__':
    unittest.main()
