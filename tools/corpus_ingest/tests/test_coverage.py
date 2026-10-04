import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from coverage import analyze


class CoverageTest(unittest.TestCase):
    def setUp(self):
        self.taxonomy = {"single_choice": "supported", "map_point": "planned"}

    def test_runnable_requires_structure_atlas_and_supported_interaction(self):
        task = {"id": "g1", "subject": "geography", "interaction": "single_choice",
                "prompt": "Where?", "knowledge": [{"id": "GEO.MAP.LOCATION"}], "prerequisites": []}
        report = analyze([task], self.taxonomy)
        self.assertEqual(1, report["counts"]["runnable"])
        self.assertEqual(1.0, report["ratios"]["atlas_mapped"])

    def test_planned_primitive_is_clustered_not_counted_as_runnable(self):
        task = {"id": "g2", "subject": "geography", "interaction": "map_point",
                "prompt": "Point", "knowledge": [{"id": "GEO.MAP.LOCATION"}], "prerequisites": []}
        report = analyze([task], self.taxonomy)
        self.assertEqual(0, report["counts"]["runnable"])
        self.assertEqual(1, report["uncovered_clusters"]["interaction:map_point"])

    def test_missing_atlas_mapping_is_visible(self):
        task = {"id": "x", "subject": "english", "interaction": "single_choice", "prompt": "?"}
        report = analyze([task], self.taxonomy)
        self.assertEqual(1, report["uncovered_clusters"]["missing:atlas_mapping"])


if __name__ == "__main__":
    unittest.main()
