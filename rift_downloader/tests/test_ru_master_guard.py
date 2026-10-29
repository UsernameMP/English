"""Before downloading, verify the source file really has Russian URLs first."""
import unittest
from rift_downloader.cloud_runner import CloudRunError,require_russian_head

class RussianFirstGuardTests(unittest.TestCase):
    def test_old_imc_shard_is_blocked_before_requests(self):
        with self.assertRaisesRegex(CloudRunError,'imc-math.org.uk'):
            require_russian_head({'first_five':[{'url':'http://www.imc-math.org.uk'}]})
    def test_updated_ru_master_is_accepted(self):
        self.assertEqual(require_russian_head({'first_five':[{
            'url':'https://olimpiada.ru/archive/tasks.pdf'}]}),'olimpiada.ru')
    def test_explicit_override_is_possible_but_not_default(self):
        self.assertEqual(require_russian_head({'first_five':[{
            'url':'https://example.com/file.pdf'}]},allow_override=True),'example.com')
    def test_empty_source_is_not_accepted(self):
        with self.assertRaises(CloudRunError):
            require_russian_head({'first_five':[]})

if __name__=='__main__':unittest.main()
