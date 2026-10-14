from crawler import (
    DropboxClient,
    build_quota_report,
    allowed_by_patterns,
    guess_extension,
    merge_states,
    normalize_refresh_token,
    parse_links,
    parse_school_stage_links,
    read_sources,
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


def test_school_stage_parser_excludes_municipal_and_regional_links():
    html = """
    <h3>Школьный этап</h3>
    <h4>Группа 1</h4>
    <a href="tasks-iikt-10-11-gr1-sch-sirius-24-25.pdf">Задания</a>
    <a href="/files/solutions-without-stage-name.pdf">Решения</a>
    <h3>Муниципальный этап</h3>
    <a href="tasks-iikt-10-11-mun-msk-24-25.pdf">Задания</a>
    <h3>Региональный этап</h3>
    <a href="/reg-tasks.pdf">Задания</a>
    """
    found = parse_school_stage_links(html, "https://olimpiada.ru/activity/73/tasks/2024")
    assert found == [
        "https://olimpiada.ru/activity/73/tasks/tasks-iikt-10-11-gr1-sch-sirius-24-25.pdf",
        "https://olimpiada.ru/files/solutions-without-stage-name.pdf",
    ]


def test_school_stage_filename_fallback_and_no_section():
    html = """
    <a href="/media/tasks-math-7-8-sch-msk-23-24.pdf">School file</a>
    <a href="/media/tasks-math-7-8-mun-msk-23-24.pdf">Municipal file</a>
    """
    assert parse_school_stage_links(html, "https://olimpiada.ru/activity/72/tasks") == [
        "https://olimpiada.ru/media/tasks-math-7-8-sch-msk-23-24.pdf",
    ]


def test_math_and_informatics_school_archive_registry(tmp_path):
    csv = tmp_path / "sources.csv"
    from pathlib import Path
    original = Path(__file__).resolve().parents[1] / "registry" / "sources.csv"
    sources = read_sources(original)
    by_id = {s.source_id: s for s in sources}
    for source_id, subject, activity in [
        ("olimpiada_ru_math_school_archive", "mathematics", "72"),
        ("olimpiada_ru_inf_school_archive", "informatics", "73"),
    ]:
        source = by_id[source_id]
        assert source.adapter == "school_section"
        assert source.subject == subject and source.stage == "school"
        assert source.is_enabled is True
        assert source.priority_int > 120
        assert f"/activity/{activity}/tasks" in source.url
        assert source.max_depth_int >= 2
    assert by_id["vosh_2024_math_school_sirius_11"].source_type == "document"
    assert by_id["vosh_2024_inf_school_sirius_10_11"].source_type == "document"


def test_grade5_school_math_informatics_official_pdf_seeds():
    """5th-grade prep means 5th grade only, with shared 5-6 informatics packs."""
    from pathlib import Path
    sources = read_sources(Path(__file__).resolve().parents[1] / "registry" / "sources.csv")
    by_id = {s.source_id: s for s in sources}
    expected = {
        ("math", year, role) for year in (2023, 2024, 2025)
        for role in ("tasks", "sol") if year != 2023 or role == "tasks"
    } | {
        ("iikt", year, role) for year in (2023, 2024, 2025)
        for role in ("tasks", "sol")
    }
    assert len(expected) == 11
    for subject_tag, year, role in expected:
        short = "math" if subject_tag == "math" else "inf"
        source = by_id[f"vosh_{short}5_school_{year}_{'tasks' if role == 'tasks' else 'solutions'}"]
        grade_band = "5" if subject_tag == "math" else "5-6"
        yy, next_yy = str(year)[-2:], str(year + 1)[-2:]
        filename = f"{role}-{subject_tag}-{grade_band}-sch-msk-{yy}-{next_yy}.pdf"
        assert source.url == (f"https://vos.olimpiada.ru/upload/files/Arhive_tasks/"
                              f"{year}-{next_yy}/school/{subject_tag}/{filename}")
        assert source.grades == grade_band
        assert source.stage == "school"
        assert source.source_type == "document" and source.adapter == "direct"
        assert source.priority_int >= 230
        assert source.is_enabled
    assert all("2026-27" not in by_id[s.source_id].url for s in sources
               if s.source_id.startswith("vosh_math5_") or s.source_id.startswith("vosh_inf5_"))


def test_link_only_mode_disables_automatic_dropbox_jobs_and_requires_explicit_opt_in():
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    workflows = [
        root / ".github/workflows/corpus-crawler.yml",
        root / ".github/workflows/corpus-parser.yml",
    ]
    for workflow in workflows:
        body = workflow.read_text(encoding="utf-8")
        assert "schedule:" not in body, workflow
        assert "gh workflow run" not in body, workflow
        assert "  push:" not in body, workflow
        assert "enable_raw_pipeline == true" in body, workflow
        assert "vars.RIFT_ENABLE_RAW_PIPELINE == 'true'" in body, workflow
        assert 'RIFT_ALLOW_RAW_INGEST: "true"' in body, workflow
    for py in (root / "tools/corpus_ingest/crawler.py",
               root / "tools/corpus_ingest/parser.py"):
        code = py.read_text(encoding="utf-8")
        assert 'os.getenv("RIFT_ALLOW_RAW_INGEST", "")' in code
        assert code.index('os.getenv("RIFT_ALLOW_RAW_INGEST", "")', code.index("def main()")) < code.index(
            "dbx = DropboxClient(", code.index("def main()")
        ), py
    links = (root / ".github/workflows/rift-link-enumeration.yml").read_text(encoding="utf-8")
    assert 'schedule:' in links and 'source_discovery/crawl_links.py' in links
