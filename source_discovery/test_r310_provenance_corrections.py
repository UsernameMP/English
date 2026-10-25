"""Regression checks for SHA-pinned Thai POSN provenance metadata patches."""
import unittest
from pathlib import Path
from apply_review_corrections import ROOT, CORRECTIONS, blob_sha, load_jsonl


class PosnProvenanceCorrectionTests(unittest.TestCase):
    def test_pinned_checkpoint_and_expected_original_metadata(self):
        name = "r310_r309_posn_provenance_corrections.jsonl"
        pinned = [sha for filename, sha, kind in CORRECTIONS
                  if filename == name and kind == "metadata"]
        self.assertEqual(len(pinned), 1)
        data = (ROOT / "runs" / name).read_bytes()
        self.assertEqual(blob_sha(data), pinned[0])
        patches = load_jsonl(data, name)
        self.assertEqual(len(patches), 2)
        self.assertEqual(len({p["raw_occurrence_id"] for p in patches}), 2)
        self.assertEqual(len({p["resource_id"] for p in patches}), 2)
        for patch in patches:
            self.assertTrue(patch["url"].startswith("https://www.posn.or.th/en/privacy-policy"))
            self.assertEqual(patch["type"], "unrelated")
            self.assertEqual(patch["previous_country"], "KR")
            self.assertEqual(patch["corrected_country"], "TH")
            self.assertIsNone(patch["corrected_competition"])
            self.assertIsNone(patch["corrected_subject"])
            self.assertIsNone(patch["corrected_level"])


if __name__ == "__main__":
    unittest.main()
