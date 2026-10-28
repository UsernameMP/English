import csv
import tempfile
import unittest
from pathlib import Path
from rift_downloader.review_catalog import classify,catalog,review_rows

class CatalogTests(unittest.TestCase):
    def test_preserve_provenance_and_flag_semantically_obvious_negatives(self):
        cases={
          'https://bitsavers.org/1971_Fairchild_Linear_Integrated_Circuits_Data_Catalog.pdf':'likely_unrelated',
          'https://www.ynu.ac.jp/access/pdf/YNU_MAP_J.pdf':'likely_unrelated',
          'https://scoala22galati.ro/REZULTATE-FINALE-7.pdf':'results_or_rankings',
          'https://mos-ecol.olimpiada.ru/upload/files/kriteri.docx':'grading_and_criteria',
          'https://boi.cses.fi/files/boi1996_solutions.zip':'solutions_and_answers',
          'https://ioai-official.org/wp-content/uploads/At-home-problems.zip':'problem_or_task_candidate',
          'https://example.org/bare.pdf':'uncertain'
        }
        for url,expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(classify(url)[0],expected)
    def test_rows_keep_every_unique_sha_and_require_content_review(self):
        data=[
          {'resource_id':'a','url':'https://math.example.org/tasks.zip',
           'source_url':'https://math.example.org/','object_sha256':'a'*64,
           'size_bytes':'1234','mime_type':'application/zip','drive_file_id':'drivefs:raw/aa/a.zip'},
          {'resource_id':'b','url':'https://mirror.example.org/another.zip',
           'source_url':'https://mirror.example.org/','object_sha256':'a'*64,
           'size_bytes':'1234','mime_type':'application/zip','drive_file_id':'drivefs:raw/aa/a.zip'},
          {'resource_id':'c','url':'https://example.org/YNU_MAP_J.pdf',
           'source_url':'https://example.org/','object_sha256':'b'*64,
           'size_bytes':'700','mime_type':'application/pdf','drive_file_id':'drivefs:raw/bb/b.pdf'}]
        rows=list(review_rows(data))
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['suggested_group'],'problem_or_task_candidate')
        self.assertEqual(rows[1]['review_priority'],'high')
        self.assertTrue(all(r['review_status']=='pending_content_review' for r in rows))
        self.assertEqual(rows[0]['source_url'],data[0]['source_url'])
        self.assertEqual(rows[1]['drive_file_id'],data[2]['drive_file_id'])
    def test_csv_format_safe_and_separate_originals(self):
        with tempfile.TemporaryDirectory() as d:
            inp=Path(d)/'manifest.csv'
            with inp.open('w',encoding='utf-8',newline='') as stream:
                w=csv.DictWriter(stream,fieldnames=['resource_id','url','source_url','object_sha256','mime_type','size_bytes','drive_file_id'])
                w.writeheader()
                w.writerow({'resource_id':'a','url':'https://example.org/problem1.pdf',
                            'source_url':'https://example.org/','object_sha256':'1'*64,
                            'mime_type':'application/pdf','size_bytes':100,'drive_file_id':'drivefs:raw/11/file.pdf'})
            output=Path(d)/'catalog.csv'
            data=catalog(inp,output)
            self.assertEqual(data['rows'],1)
            with output.open(encoding='utf-8',newline='') as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['classification_basis'].split(';')[0],'URL and filename heuristic only')
            self.assertTrue(inp.exists())

if __name__=='__main__':
    unittest.main()
