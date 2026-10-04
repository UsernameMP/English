from crawler import (
    allowed_by_patterns,
    guess_extension,
    merge_states,
    parse_links,
    raw_dropbox_path,
    stable_document_id,
)


def test_document_id_is_stable_and_ignores_fragment():
    assert stable_document_id("https://example.org/a.pdf#page=2") == stable_document_id("https://example.org/a.pdf")


def test_raw_path_is_content_addressed():
    digest = "ab" + "c" * 62
    assert raw_dropbox_path("/OlympiadCorpus", digest, ".pdf") == f"/OlympiadCorpus/raw/ab/{digest}.pdf"


def test_parse_links_resolves_relative_and_deduplicates():
    html = '<a href="files/a.pdf">A</a><a href="files/a.pdf#p=2">A2</a><a href="/year/2024">Y</a>'
    links = parse_links(html, "https://example.org/archive/")
    assert links == [
        "https://example.org/archive/files/a.pdf",
        "https://example.org/year/2024",
    ]


def test_patterns():
    assert allowed_by_patterns("https://x/a.pdf", r"\.pdf$", "")
    assert not allowed_by_patterns("https://x/a.zip", r"\.pdf$", "")


def test_guess_extension_from_content_type():
    assert guess_extension("https://x/download?id=1", "application/pdf") == ".pdf"


def test_merge_prefers_newer_record():
    a = {"1": {"document_id": "1", "updated_at": "2026-01-01T00:00:00+00:00", "status": "PENDING"}}
    b = {"1": {"document_id": "1", "updated_at": "2026-01-02T00:00:00+00:00", "status": "DOWNLOADED"}}
    assert merge_states(a, b)["1"]["status"] == "DOWNLOADED"
