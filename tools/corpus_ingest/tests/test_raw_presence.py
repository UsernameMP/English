"""Presence heatmap: tests for minimum evidence, not fictional completeness."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raw_presence import compute_presence, expand_school_grades, score_document, GRADES
from coverage_dashboard import REGISTRY
from discovery_network import build_network

REG = json.loads(REGISTRY.read_text(encoding="utf-8"))
HASH = "a" * 64
HASH2 = "b" * 64


def record(url: str, doc_id: str, *, status: str = "DOWNLOADED",
           sha: str = HASH, source_id: str = "olimpiada_ru_engl_archive") -> dict:
    return {
        "url": url, "source_id": source_id, "document_id": doc_id,
        "status": status, "sha256": sha if status in ("DOWNLOADED", "DUPLICATE") else "",
        "content_type": "application/pdf", "bytes": 1234,
        "discovered_from": "https://olimpiada.ru/activity/88/tasks",
    }


def generated(records):
    return compute_presence(REG, build_network(REG, records, timestamp="fixed"),
                            timestamp="fixed")


def cell(view, subject, season, grade, level="school"):
    matches = [x for x in view["cells"] if
               x["subject_id"] == subject and x["season"] == season
               and x["grade"] == str(grade)
               and x["education_level"] == level]
    assert len(matches) <= 1
    return matches[0] if matches else None


class RawPresenceTest(unittest.TestCase):
    def test_grade_parsing_is_strict(self):
        self.assertEqual(expand_school_grades("7–8"), (7, 8))
        self.assertEqual(expand_school_grades("1"), (1,))
        for bad in ("не указан", "1–12", "2025", "7–5", "", "1,2", None):
            self.assertEqual(expand_school_grades(bad), ())

    def test_downloaded_task_covers_7_and_8_not_6(self):
        url = "https://tasks.olimpiada.ru/upload/files/tasks/88/2025/tasks-engl-7-8-mun-msk-25-26.pdf"
        view = generated([record(url, "a")])
        for grade in (7, 8):
            c = cell(view, "english", 2025, grade)
            self.assertEqual(c["state"], "raw")
            self.assertEqual(c["raw_task_count_unique"], 1)
            self.assertEqual(len(c["raw_evidence"]), 1)
        self.assertEqual(cell(view, "english", 2025, 6)["state"], "catalogued")

    def test_same_sha_on_two_urls_is_one_raw(self):
        a = record("https://tasks.olimpiada.ru/upload/files/tasks/88/2025/tasks-engl-7-8-mun-msk-25-26.pdf", "a")
        b = record("https://cdn.example.org/tasks-engl-7-8-mun-msk-25-26.pdf", "b", status="DUPLICATE")
        view = generated([a, b])
        c = cell(view, "english", 2025, 7)
        self.assertEqual(c["raw_task_count_unique"], 1)
        self.assertEqual(c["task_urls"], 2)

    def test_pending_task_yellow(self):
        url = "https://tasks.olimpiada.ru/upload/files/tasks/88/2024/tasks-engl-5-6-mun-msk-24-25.pdf"
        c = cell(generated([record(url, "a", status="PENDING")]), "english", 2024, 5)
        self.assertEqual(c["state"], "located")
        self.assertEqual(c["raw_task_count_unique"], 0)

    def test_answers_only_cannot_turn_green(self):
        url = "https://tasks.olimpiada.ru/upload/files/tasks/88/2024/ans-engl-7-8-mun-msk-24-25.pdf"
        c = cell(generated([record(url, "a")]), "english", 2024, 7)
        self.assertEqual(c["state"], "catalogued")
        self.assertEqual(c["other_material_urls"], 1)

    def test_unknown_grade_does_not_fill_any_school_grade(self):
        url = "https://tasks.olimpiada.ru/upload/files/tasks/88/2024/tasks-engl-mun-msk-24-25.pdf"
        view = generated([record(url, "a")])
        self.assertEqual(view["unplaced_observation_count"], 1)
        self.assertTrue(all(cell(view, "english", 2024, g)["state"] == "catalogued"
                            for g in (4, 5, 6, 7, 8, 9, 10, 11)))

    def test_university_is_independent_education_level(self):
        r = copy.deepcopy(REG)
        r["competitions"].append({
            "id": "university_test", "name": "Студенческий тур",
            "subject_ids": ["mathematics"], "education_level": "university",
            "grade_min": None, "grade_max": None,
            "from": 2020, "to": 2026, "stages": [{"id": "event", "name": "Тур"}],
            "discovery_segment_ids": ["RU"], "archive_links": [],
        })
        n = build_network(r, [], timestamp="fixed")
        view = compute_presence(r, n, timestamp="fixed")
        self.assertEqual(cell(view, "mathematics", 2025, "university", "university")["state"], "catalogued")
        self.assertIsNone(cell(view, "mathematics", 2025, "12", "school"))
        self.assertEqual(len(GRADES), 11)

    def test_catalogue_window_only_is_weak_signal(self):
        view = generated([])
        self.assertEqual(cell(view, "english", 2025, 8)["state"], "catalogued")
        self.assertIsNone(cell(view, "biology", 2010, 8))
        self.assertEqual(view["semantics"]["not_progress_percent"].startswith("Цвет"), True)

    def test_deterministic_view_after_same_observations(self):
        docs = [record("https://tasks.olimpiada.ru/upload/files/tasks/88/2024/tasks-engl-7-8-mun-msk-24-25.pdf", "a"),
                record("https://tasks.olimpiada.ru/upload/files/tasks/88/2025/ans-engl-5-6-mun-msk-25-26.pdf", "b", sha=HASH2)]
        self.assertEqual(generated(docs), generated(list(reversed(docs))))


if __name__ == "__main__":
    unittest.main()
