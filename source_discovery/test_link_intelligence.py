#!/usr/bin/env python3
"""RIFT: no-binary-fetch, multilingual, provenance and frontier regressions."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from link_intelligence import canonical_resource_url, resource_id, likely_file, hint
from crawl_links import observe_mime, prioritize_queue
from build_resource_index import build


class MultilingualLinkTests(unittest.TestCase):
    def test_austrian_chemistry_exam_and_answer(self):
        questions = hint("https://oecho.at/assets/52-BW-2026-Theorie-Angabe.pdf",
                         "Bundeswettbewerb Theorie Angabe", heading="2026 - 52. ÖChO")
        solutions = hint("https://oecho.at/assets/52-BW-2026-Theorie-m-Losungen.pdf",
                         "Bundeswettbewerb Theorie Lösungen", heading="2026 - 52. ÖChO")
        self.assertEqual(questions["type_hint"], "task")
        self.assertEqual(solutions["type_hint"], "solution")
        self.assertEqual(questions["priority"], 3)

    def test_japanese_round_markers(self):
        self.assertEqual(hint("https://imojp.org/archive/mo2017/jmo2017/problems/jmo27mq.html",
                              "本選")["type_hint"], "task")

    def test_turkish_answer_russian_tasks(self):
        self.assertEqual(hint("https://example.org/doc.zip", "Sınav Soruları")["type_hint"], "task")
        self.assertEqual(hint("https://example.org/doc.zip", "Cevapları")["type_hint"], "solution")

    def test_context_not_enough_for_nav(self):
        case = hint("https://rsme.es/inscripcion-nuevo-socio/", "Registration",
                    heading="Math Olympiad Archives")
        self.assertEqual(case["priority"], 0)
        self.assertEqual(case["type_hint"], "review")

    def test_extensionless_binary_link(self):
        url = "https://www.jpho.jp/challenge/media-download/905/abcd/PDF/"
        self.assertTrue(likely_file(url))
        self.assertTrue(likely_file("https://x.org/api/file/42", "application/pdf"))
        self.assertFalse(likely_file("https://x.org/about", "text/html"))

    def test_resource_id_dedup_and_occurrence_context(self):
        url = "https://example.org/?year=2026&section=problems"
        self.assertEqual(resource_id(url), resource_id(url + "#next"))
        self.assertNotEqual(resource_id(url), resource_id(url.replace("2026", "2025")))
        self.assertEqual(canonical_resource_url(url + "#top"), url)

    def test_mime_kept_separate_from_errors(self):
        rows = []
        url = "https://example.org/archive/download/PDF/"
        observe_mime(rows, url, "application/pdf", "https://example.org/", "https://example.org/years")
        observe_mime(rows, url, "application/pdf")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["resource_id"], resource_id(url))
        self.assertTrue(rows[0]["file_candidate"])

    def test_archive_frontier_does_not_discard_other_pages(self):
        input_queue = [{"url": "https://x.org/contacts", "priority": 0},
                       *[{"url": f"https://x.org/archives/{i}", "priority": 2}
                         for i in range(9)]]
        out = prioritize_queue(input_queue)
        self.assertEqual(len(out), len(input_queue))
        self.assertEqual({o["url"] for o in out}, {o["url"] for o in input_queue})
        self.assertEqual(out[4]["url"], "https://x.org/contacts")


class ResourceIndexTests(unittest.TestCase):
    def test_one_resource_from_two_distinct_occurrences(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            raw = root / "raw"
            raw.mkdir()
            output = root / "resources"
            mimed = root / "mimes.jsonl"
            url = "https://example.org/2026.pdf"
            rows = [
                {"id": "a", "url": url, "parent_url": "https://example.org/a",
                 "source_url": "https://example.org/", "anchor_text": "Aufgaben"},
                {"id": "b", "url": url, "parent_url": "https://example.org/b",
                 "source_url": "https://example.org/", "anchor_text": "2026 Problems"},
            ]
            (raw / "batch_000001.jsonl").write_text(
                "".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8"
            )
            with patch("build_resource_index.RAW_SHARDS", raw), \
                    patch("build_resource_index.RESOURCE_SHARDS", output), \
                    patch("build_resource_index.OBSERVATIONS", mimed):
                build()
                files = sorted(output.glob("resource_*.jsonl"))
                self.assertEqual(len(files), 1)
                indexed = [json.loads(l) for l in files[0].read_text().splitlines()]
                self.assertEqual(len(indexed), 1)
                self.assertEqual(indexed[0]["first_occurrence_id"], "a")
                before = files[0].read_bytes()
                build()
                self.assertEqual(files[0].read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
