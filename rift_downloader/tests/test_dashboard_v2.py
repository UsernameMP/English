"""Dashboard v2 regression: real daily SQL, historical truth and safe embedding."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from rift_downloader.db import connect,import_resources,begin_attempt,finish_attempt
from rift_downloader.ops_metrics import build_metrics,make_baseline,render_html,write_dashboard

class DashboardV2Tests(unittest.TestCase):
    def test_histogram_and_donut_from_real_historical_pilot_no_fabricated_daily(self):
        data=make_baseline()
        self.assertEqual(data['metrics']['unique_urls_checked'],328)
        self.assertEqual(data['metrics']['unique_files'],200)
        self.assertEqual(sum(data['file_groups'].values()),200)
        self.assertEqual(data['daily'],[])
        html=render_html(data)
        for needle in ('id="daily-chart"','id="http-histogram"','id="donut"',
                       'id="master-head"','7 дней','14 дней','30 дней',
                       'id="hosts-table"','RIFT / Downloader Control'):
            self.assertIn(needle,html)
        self.assertIn('Исторический пилот',html)
        self.assertEqual(html.count('<script'),2)
    def test_daily_bars_and_ru_master_health_are_sql_derived(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=connect(Path(tmp)/'index.sqlite3')
            import_resources(db,[
                {'resource_id':'ru1','url':'https://olimpiada.ru/tasks.pdf'},
                {'resource_id':'ru2','url':'https://math.ru/archive.zip'},
                {'resource_id':'uk','url':'https://www.imc-math.org.uk/paper.pdf'}])
            for position,rid in enumerate(('ru1','ru2','uk'),1):
                db.execute('UPDATE resources SET source_position=? WHERE resource_id=?',(position,rid))
            db.execute("INSERT INTO settings(key,value) VALUES ('master_rows','3')")
            first=begin_attempt(db,'ru1','olimpiada.ru')
            db.execute('UPDATE attempts SET started_at=? WHERE id=?',(1782633600,first))
            finish_attempt(db,first,code=200,outcome='staged')
            second=begin_attempt(db,'ru2','math.ru')
            db.execute('UPDATE attempts SET started_at=? WHERE id=?',(1782720000,second))
            finish_attempt(db,second,code=404,outcome='skipped')
            db.execute("UPDATE resources SET status='completed',object_sha256=? WHERE resource_id='ru1'",('f'*64,))
            db.execute("""INSERT INTO objects(sha256,size_bytes,mime_type,drive_file_id,verified_at)
                     VALUES(?,?,?,?,?)""",('f'*64,400,'application/pdf','drive-file-id',1782720000))
            data=build_metrics(db,run_state='snapshot')
            self.assertEqual(data['master']['first_domain'],'olimpiada.ru')
            self.assertTrue(data['master']['head_ru_expected'])
            self.assertEqual(data['master']['head_ru_count'],2)
            self.assertEqual(data['master']['rows'],3)
            self.assertEqual(sum(row['urls'] for row in data['daily']),2)
            self.assertEqual(sum(row['files'] for row in data['daily']),1)
            self.assertEqual(data['metrics']['unique_urls_checked'],2)
            self.assertEqual(data['file_groups'],{'PDF':1})
            self.assertIn('Панель загрузки',render_html(data))
    def test_xss_strings_are_escaped_in_data_script(self):
        data=make_baseline()
        data['source']='</script><script>alert(1)</script>&'
        html=render_html(data)
        self.assertEqual(html.count('<script'),2)
        self.assertNotIn('alert(1)</script>',html)
        self.assertIn(r'\u003c/script\u003e',html)
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'index.html'
            write_dashboard(data,output,Path(tmp)/'status.json')
            self.assertTrue(output.stat().st_size>10000)
            self.assertEqual(json.loads((Path(tmp)/'status.json').read_text())['metrics']['unique_files'],200)

if __name__=='__main__':unittest.main()
