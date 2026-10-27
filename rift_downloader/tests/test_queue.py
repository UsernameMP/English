import tempfile
import unittest
from pathlib import Path
from rift_downloader.db import connect, import_resources, claim, recover, stats

class QueueTests(unittest.TestCase):
    def test_import_deduplicates_and_recovers(self):
        with tempfile.TemporaryDirectory() as directory:
            db = connect(Path(directory)/"queue.db")
            sample = {"resource_id":"r1","url":"https://example.org/file.pdf","file_candidate":True}
            self.assertEqual(import_resources(db,[sample,sample]),1)
            self.assertEqual(claim(db)["resource_id"],"r1")
            self.assertIsNone(claim(db))
            self.assertEqual(recover(db),1)
            self.assertEqual(stats(db),{"pending":1})
            db.close()
            reopened = connect(Path(directory)/"queue.db")
            self.assertEqual(claim(reopened)["resource_id"],"r1")

if __name__ == "__main__":
    unittest.main()
