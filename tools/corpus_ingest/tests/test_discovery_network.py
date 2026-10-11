"""Discovery RU graph regression tests; no network or Dropbox required."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import discovery_network as graph

REGISTRY = json.loads(graph.REGISTRY.read_text(encoding="utf-8"))

SHA = "a" * 64


def record(url: str, document_id: str, *, source_id: str = "olimpiada_ru_engl_archive",
           status: str = "DOWNLOADED", sha: str = SHA, parent: str = "https://olimpiada.ru/activity/88/tasks") -> dict:
    return {
        "url": url, "document_id": document_id, "source_id": source_id,
        "status": status, "sha256": sha,
        "discovered_from": parent, "first_seen": "2026-10-01T10:00:00Z",
        "updated_at": "2026-10-04T10:00:00Z", "bytes": 123, "content_type": "application/pdf",
    }


class DiscoveryNetworkTest(unittest.TestCase):
    def test_geography_is_discovery_segment_not_language_or_tld(self):
        rows = [record("https://drive.google.com/files/tasks-engl-7-8-mun-msk-25-26.pdf", "a")]
        out = graph.build_network(REGISTRY, rows, timestamp="test")
        self.assertEqual(out["segment"]["id"], "RU")
        self.assertEqual(out["observations"][0]["classification"]["subject_id"], "english")
        self.assertEqual(out["observations"][0]["classification"]["competition_id"], "vsosh")
        self.assertEqual(out["sites"][0]["hostname"], "drive.google.com")
        self.assertTrue(all(x["country_codes"] is None for x in out["approved_competitions"]))

    def test_unknown_classification_is_not_lost(self):
        unknown = record("https://archive.example.org/random-file.pdf", "b",
                         source_id="unclassified", status="PENDING", sha="",
                         parent="https://anokmc.ru/olymp")
        out = graph.build_network(REGISTRY, [unknown], timestamp="test")
        self.assertEqual(out["summary"]["url_observations"], 1)
        self.assertEqual(out["summary"]["unresolved_observations"], 1)
        self.assertIsNone(out["observations"][0]["classification"]["competition_id"])
        self.assertIsNone(out["observations"][0]["asset_id"])
        self.assertEqual(out["observations"][0]["discovered_from"], "https://anokmc.ru/olymp")

    def test_mirror_sha_dedup_keeps_both_urls(self):
        records = [
            record("https://tasks.olimpiada.ru/foo/tasks-engl-7-8-sch-msk-25-26.pdf", "a"),
            record("https://another-cdn.example/foo/tasks-engl-7-8-sch-msk-25-26.pdf", "b",
                   status="DUPLICATE"),
        ]
        out = graph.build_network(REGISTRY, records, timestamp="test")
        self.assertEqual(len(out["raw_assets"]), 1)
        self.assertEqual(out["raw_assets"][0]["mirror_count"], 2)
        self.assertEqual(out["summary"]["url_observations"], 2)
        self.assertNotEqual(out["observations"][0]["id"], out["observations"][1]["id"])

    def test_one_site_can_host_archives_for_multiple_competitions(self):
        source = copy.deepcopy(REGISTRY)
        both = [x for x in source["competitions"] if x["id"] in {"golden_fleece", "golden_path"}]
        for x in both:
            x["archive_links"] = [{"title": "Общий каталог", "url": "https://organizer.example/olymp/"}]
        out = graph.build_network(source, [], timestamp="test")
        archive = next(x for x in out["archives"] if x["url"] == "https://organizer.example/olymp/")
        self.assertEqual(sorted(archive["competition_ids"]), ["golden_fleece", "golden_path"])
        self.assertEqual(archive["state"], "known_link_not_verified_as_crawled_archive")

    def test_deterministic_when_input_order_changes(self):
        rows = [
            record("https://tasks.olimpiada.ru/foo/ans-engl-7-8-mun-msk-25-26.pdf", "a"),
            record("https://tasks.olimpiada.ru/foo/tasks-engl-7-8-mun-msk-25-26.pdf", "b", sha="b"*64),
        ]
        x = graph.build_network(REGISTRY, rows, timestamp="constant")
        y = graph.build_network(REGISTRY, list(reversed(rows)), timestamp="constant")
        self.assertEqual(json.dumps(x, sort_keys=True), json.dumps(y, sort_keys=True))

    def test_query_is_not_removed_when_identifying_source(self):
        a = graph.normalized_url("https://example.org/doc?id=1#paragraph")
        b = graph.normalized_url("https://example.org/doc?id=2#paragraph")
        self.assertEqual(a, "https://example.org/doc?id=1")
        self.assertNotEqual(a, b)

    def test_unconfigured_segment_is_explicitly_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown discovery segment"):
            graph.build_network(REGISTRY, [], segment_id="IN", timestamp="test")


if __name__ == "__main__":
    unittest.main()
