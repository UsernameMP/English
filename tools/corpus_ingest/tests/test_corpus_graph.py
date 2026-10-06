from corpus_graph import Asset, GraphNode, bundle_similarity, entity_id, problemset_id_for, propose_problemsets


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


def test_full_entity_graph_ids_are_stable_and_parser_independent():
    ps = "problemset_demo"
    asset = entity_id("asset", ps, "sha256:abc")
    section = entity_id("section", asset, "p1:b0-b12", "reading")
    task = entity_id("task", section, "p2:b4-b9", "task-3")
    subtask = entity_id("subtask", task, "p2:b6", "3a")
    answer = entity_id("answer", task, "answer-key:p1:b2", "3a")
    criterion = entity_id("criterion", task, "criteria:p4:b1", "writing-rubric")
    media = entity_id("media", task, "audio:segment:00:20-00:45", "listening")

    values = [asset, section, task, subtask, answer, criterion, media]
    assert len(values) == len(set(values))
    assert all("_" in value for value in values)

    again = GraphNode(
        kind="task",
        parent_id=section,
        source_anchor="p2:b4-b9",
        semantic_key="task-3",
        provenance={"parser_version": "other-parser"},
    )
    assert again.id == task
