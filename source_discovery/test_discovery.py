#!/usr/bin/env python3
"""Regression tests: exact URL preservation, discovery dedupe, and no file downloads."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crawl_links import Links, decode_href, normalize
from merge_sources import merge_sources


class CrawlHtmlTests(unittest.TestCase):
    def test_unescaped_ampersand_must_survive_html_parser(self):
        parser = Links()
        parser.feed('<a href="https://example.org/?item=problems&section=2026">2026 problems</a>')
        self.assertEqual(
            parser.links[0]["href"],
            "https://example.org/?item=problems&section=2026"
        )

    def test_amp_encoded_attribute(self):
        parser = Links()
        parser.feed('<a href="https://example.org/?a=1&amp;b=2">Archive</a>')
        self.assertEqual(parser.links[0]["href"], "https://example.org/?a=1&b=2")

    def test_single_quoted_query(self):
        parser = Links()
        parser.feed("<a href='?year=2019&section=2'>tasks</a>")
        self.assertEqual(parser.links[0]["href"], "?year=2019&section=2")

    def test_numeric_html_entities_decode(self):
        self.assertEqual(decode_href("/?a=1&#38;b=2"), "/?a=1&b=2")

    def test_fragment_only_is_removed(self):
        self.assertEqual(normalize("https://example.org/?year=2019&stage=1#top"),
                         "https://example.org/?year=2019&stage=1")


class MergeSourcesTests(unittest.TestCase):
    def test_preserves_existing_and_deduplicates_journals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "runs").mkdir()
            ledger = root / "sources.jsonl"
            seed = {"url": "https://example.org/archive", "status": "unverified"}
            ledger.write_text(json.dumps(seed) + "\n", encoding="utf-8")
            discovery = root / "runs" / "discovery_001.jsonl"
            addition = {"url": "https://example.org/new/", "status": "verified_source",
                        "origin": "web-discovery"}
            discovery.write_text(json.dumps(addition) + "\n" +
                                 json.dumps(addition) + "\n" +
                                 json.dumps({"url": "javascript:alert(1)"}) + "\n",
                                 encoding="utf-8")
            with patch("merge_sources.TARGET", ledger), patch("merge_sources.RUNS", root / "runs"):
                count, added = merge_sources()
                self.assertEqual((count, added), (2, 1))
                before = ledger.read_bytes()
                self.assertEqual(merge_sources(), (2, 0))
                self.assertEqual(before, ledger.read_bytes())
                actual = [json.loads(s) for s in ledger.read_text(encoding="utf-8").splitlines()]
                self.assertEqual(actual[0], seed)
                self.assertEqual(actual[1]["status"], "verified_source")


if __name__ == "__main__":
    unittest.main()
