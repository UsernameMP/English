from corpus_graph import Asset, bundle_similarity, problemset_id_for, propose_problemsets


def task_asset() -> Asset:
    return Asset(
        sha256="a" * 64,
        filename="tasks-engl-9-11-pism-mun-kamchat-22-23.pdf",
        role="TASK_SET",
        subject="english",
        academic_year="2022/23",
        stage="municipal",
        grades="9-11",
        region="kamchat",
        tour="written",
    )


def answer_asset() -> Asset:
    return Asset(
        sha256="b" * 64,
        filename="ans-engl-9-11-pism-mun-kamchat-22-23.pdf",
        role="ANSWER_KEY",
        subject="english",
        academic_year="2022/23",
        stage="municipal",
        grades="9-11",
        region="kamchat",
        tour="written",
    )


def test_problemset_id_is_stable_across_complementary_assets():
    task = task_asset()
    answer = answer_asset()
    assert problemset_id_for(task) == problemset_id_for(answer)


def test_bundle_linker_proposes_high_confidence_pair():
    task = task_asset()
    answer = answer_asset()
    score, provenance = bundle_similarity(task, answer)
    assert score >= 0.9
    assert provenance["complementary_roles"] is True

    graph = propose_problemsets([task, answer], threshold=0.7)
    assert graph["schema_version"] == "corpus-graph.v1"
    assert len(graph["problemsets"]) == 1
    assert graph["edge_proposals"]
