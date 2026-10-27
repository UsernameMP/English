import unittest
from rift_downloader.deploy_service import render_unit

class DeployServiceTests(unittest.TestCase):
    def test_service_is_explicit_manual_one_shot_with_200_cap_and_reporting(self):
        data=render_unit(repo='/opt/rift/English',python='/opt/rift/English/.venv/bin/python',
                         token='/home/rift/.private/drive-token.json',state_dir='/home/rift/.local/share/rift')
        self.assertIn('Type=oneshot',data)
        self.assertIn('--limit-success 200',data)
        self.assertIn('--backup-every 25',data)
        self.assertIn('export-report',data)
        self.assertIn('Restart=no',data)
        self.assertNotIn('OnCalendar=',data)
        self.assertNotIn('Restart=always',data)
        self.assertNotIn('client_secret',data)

if __name__=='__main__':
    unittest.main()
