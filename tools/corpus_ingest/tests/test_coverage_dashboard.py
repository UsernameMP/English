"""Regression tests for Corpus Coverage and provenance-safe statuses."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import coverage_dashboard as coverage

REGISTRY = json.loads(coverage.REGISTRY.read_text(encoding="utf-8"))


class CoverageDashboardTests(unittest.TestCase):
    def test_registry_unique_ids_and_own_stages(self):
        coverage.validate_registry(REGISTRY)
        kmo = next(c for c in REGISTRY["competitions"] if c["id"] == "kmo")
        vsosh = next(c for c in REGISTRY["competitions"] if c["id"] == "vsosh")
        self.assertEqual([x["id"] for x in kmo["stages"]], ["qualifier", "final"])
        self.assertEqual([x["id"] for x in vsosh["stages"]],
                         ["school", "municipal", "regional", "final"])

    def test_english_school_document_classification(self):
        row = {"url": "https://vos.olimpiada.ru/upload/files/Arhive_tasks/2025-26/school/engl/tasks-engl-7-8-sch-msk-25-26.pdf",
               "source_id": "vosh_2025_school_7_8_tasks", "status": "DOWNLOADED"}
        m = coverage.identify(row, REGISTRY)
        self.assertEqual(m["competition_id"], "vsosh")
        self.assertEqual(m["subject_id"], "english")
        self.assertEqual(m["season"], 2025)
        self.assertEqual(m["stage_id"], "school")
        self.assertEqual(m["grade_band"], "7–8")
        self.assertEqual(m["role"], "tasks")

    def test_math_and_informatics_school_documents_are_classified(self):
        cases = [
            ("https://tasks.olimpiada.ru/upload/files/tasks/72/2024/taskssol-math-11-gr1-sch-sirius-24-25_pdf.pdf",
             "vosh_2024_math_school_sirius_11", "mathematics", "11"),
            ("https://tasks.olimpiada.ru/upload/files/tasks/73/2024/tasks-iikt-10-11-gr1-sch-sirius-24-25.pdf",
             "vosh_2024_inf_school_sirius_10_11", "informatics", "10–11"),
        ]
        for url, source_id, subject, grade in cases:
            with self.subTest(source_id=source_id):
                meta = coverage.identify({"url": url, "source_id": source_id, "status": "DOWNLOADED"}, REGISTRY)
                self.assertEqual(meta["competition_id"], "vsosh")
                self.assertEqual(meta["subject_id"], subject)
                self.assertEqual(meta["season"], 2024)
                self.assertEqual(meta["stage_id"], "school")
                self.assertEqual(meta["grade_band"], grade)
                self.assertEqual(meta["role"], "tasks")

    def test_school_adapter_source_sets_school_when_filename_omits_stage(self):
        meta = coverage.identify({
            "url": "https://tasks.olimpiada.ru/upload/files/tasks/72/2024/tasks-math-5-6-24-25.pdf",
            "source_id": "olimpiada_ru_math_school_archive",
            "status": "PENDING",
        }, REGISTRY)
        self.assertEqual(meta["stage_id"], "school")
        self.assertEqual(meta["grade_band"], "5–6")
        self.assertEqual(meta["subject_id"], "mathematics")

    def test_competition_does_not_guess_missing_metadata(self):
        m = coverage.identify({"url": "https://somehost.ru/unknown.pdf",
                               "source_id": "external", "status": "PENDING"}, REGISTRY)
        self.assertIsNone(m["competition_id"])
        self.assertIsNone(m["season"])
        self.assertIsNone(m["stage_id"])

    def test_statuses_and_unknowns_are_counted_not_imputed(self):
        docs = [
            {"url": "https://tasks.olimpiada.ru/upload/files/tasks/88/2025/tasks-engl-9-11-mun-tat-25-26.pdf",
             "source_id": "olimpiada_ru_engl_archive", "status": "DOWNLOADED", "sha256": "abc"},
            {"url": "https://example.org/document.pdf", "source_id": "other", "status": "PENDING"}
        ]
        parsed = [{"document_sha256": "abc", "status": "PARSED"}]
        d = coverage.generate(REGISTRY, docs, parsed)
        self.assertEqual(d["summary"]["urls"], 2)
        self.assertEqual(d["summary"]["identified_urls"], 1)
        self.assertEqual(d["summary"]["unclassified_urls"], 1)
        self.assertEqual(d["summary"]["parsed_document_hashes"], 1)
        self.assertEqual(d["cells"][0]["parse_statuses"]["PARSED"], 1)

    def test_committed_snapshot_is_real_not_placeholder(self):
        saved = json.loads(coverage.OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(saved["schema_version"], "corpus_coverage.v1")
        self.assertEqual(saved["summary"]["urls"], sum(saved["summary"]["statuses"].values()))
        self.assertEqual(saved["summary"]["urls"],
                         saved["summary"]["identified_urls"]+saved["summary"]["unclassified_urls"])
        self.assertGreater(saved["summary"]["urls"], 2500)


if __name__ == "__main__":
    unittest.main()
