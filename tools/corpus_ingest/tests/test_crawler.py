from crawler import (
    DropboxClient,
    build_quota_report,
    allowed_by_patterns,
    guess_extension,
    merge_states,
    normalize_refresh_token,
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


def test_normalize_refresh_token_accepts_common_copy_formats():
    assert normalize_refresh_token('  "abc123"  ') == "abc123"
    assert normalize_refresh_token("refresh_token=abc123") == "abc123"
    assert normalize_refresh_token('{"access_token":"short","refresh_token":"abc123"}') == "abc123"


def test_missing_dropbox_checkpoint_is_valid_first_run():
    dbx = object.__new__(DropboxClient)
    dbx.root = "/OlympiadCorpus"
    dbx.exists = lambda path: False

    def should_not_download(_path):
        raise AssertionError("download must not be called when checkpoint does not exist")

    dbx.download_bytes = should_not_download
    assert dbx.load_checkpoint() == {}


def test_quota_guard_stops_at_95_percent_and_before_crossing():
    quota = 2 * 1024 * 1024 * 1024
    below = build_quota_report(int(quota * 0.90), quota, quota, 0.95, 0)
    assert below["stop"] is False

    exact = build_quota_report(int(quota * 0.95), quota, quota, 0.95, 0)
    assert exact["stop"] is True

    crossing = build_quota_report(int(quota * 0.94), quota, quota, 0.95, int(quota * 0.02))
    assert crossing["stop"] is True


def test_configured_two_gib_limit_wins_over_larger_account_allocation():
    two_gib = 2 * 1024 * 1024 * 1024
    report = build_quota_report(0, 10 * two_gib, two_gib, 0.95, 0)
    assert report["effective_quota"] == two_gib
