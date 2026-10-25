"""Regression checks: an audited type correction must not block later checkpoint merges."""
import unittest

from merge_review_checkpoints import audited_type_corrections, is_audited_type_override


class AuditedTypeCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.overrides = audited_type_corrections()
        self.raw_id = "869f6211fb1370425d826cbd"
        self.patch = self.overrides[self.raw_id]
        self.original = {
            "raw_occurrence_id": self.raw_id,
            "resource_id": self.patch["resource_id"],
            "url": self.patch["url"],
            "type": self.patch["previous_type"],
        }
        self.canonical = {
            **self.original,
            "type": self.patch["corrected_type"],
            "correction_checkpoint": self.patch["correction_checkpoint"],
        }

    def test_audited_correction_is_allowed(self):
        self.assertTrue(is_audited_type_override(self.canonical, self.original, self.overrides))

    def test_unpinned_correction_is_rejected(self):
        self.canonical.pop("correction_checkpoint")
        self.assertFalse(is_audited_type_override(self.canonical, self.original, self.overrides))

    def test_wrong_resource_or_url_is_rejected(self):
        self.original["resource_id"] = "wrong"
        self.assertFalse(is_audited_type_override(self.canonical, self.original, self.overrides))
        self.original["resource_id"] = self.patch["resource_id"]
        self.original["url"] = "https://example.org/wrong"
        self.assertFalse(is_audited_type_override(self.canonical, self.original, self.overrides))

    def test_arbitrary_type_change_is_rejected(self):
        self.canonical["type"] = "task"
        self.assertFalse(is_audited_type_override(self.canonical, self.original, self.overrides))

    def test_second_corrected_occurrence_is_present(self):
        self.assertIn("ce2bdb57a0acd1b217bfc4a5", self.overrides)


if __name__ == "__main__":
    unittest.main()
