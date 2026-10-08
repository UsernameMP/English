from calibration_eval import evaluate


def test_calibration_eval_matches_repeated_sections_and_tasks():
    gold={
        "documents":{
            "doc":{
                "filename":"tasks-demo.pdf",
                "sections":[
                    {"label":"Speaking Set 1","semantic_type":"SPEAKING_SET","page_start":1,"page_end":1,
                     "tasks":[{"label":"Task 1","kind":"ORAL_RESPONSE","anchor_page":1,"artifacts":[]}]},
                    {"label":"Speaking Set 2","semantic_type":"SPEAKING_SET","page_start":2,"page_end":2,
                     "tasks":[{"label":"Task 1","kind":"ORAL_RESPONSE","anchor_page":2,"artifacts":[]}]},
                ]
            }
        }
    }
    machine={
        "doc":{
            "sections":[
                {"label":"Speaking Set 1","semantic_type":"SPEAKING_SET","page_start":1,"page_end":1,
                 "tasks":[{"label":"Task 1","number":"1","kind":"ORAL_RESPONSE","page_start":1,"page_end":1,"artifacts":[]}]},
                {"label":"Speaking Set 2","semantic_type":"SPEAKING_SET","page_start":2,"page_end":2,
                 "tasks":[{"label":"Task 1","number":"1","kind":"ORAL_RESPONSE","page_start":2,"page_end":2,"artifacts":[]}]},
            ]
        }
    }
    report=evaluate(gold,machine)
    assert report["reviewable_documents"] == 1
    assert report["metrics"]["section_recall_micro"] == 1.0
    assert report["metrics"]["task_recall_micro"] == 1.0
    assert report["metrics"]["known_kind_accuracy_micro"] == 1.0


def test_artifact_compatibility_accepts_generic_grid_for_crossword():
    gold={"documents":{"doc":{"filename":"x.pdf","sections":[
        {"label":"Math","page_start":1,"page_end":1,"tasks":[
            {"label":"Task 1","kind":"UNKNOWN","anchor_page":1,"artifacts":[{"kind":"CROSSWORD"}]}
        ]}
    ]}}}
    machine={"doc":{"sections":[
        {"label":"Math","page_start":1,"page_end":1,"tasks":[
            {"label":"Task 1","number":"1","kind":"UNKNOWN","page_start":1,"page_end":1,
             "artifacts":[{"kind":"GRID","page":1}]}
        ]}
    ]}}
    report=evaluate(gold,machine)
    assert report["metrics"]["artifact_recall_micro"] == 1.0


def test_reconstruction_metrics_are_reported():
    gold = {
        "sections": [{
            "label": "Tasks",
            "semantic_type": "UNKNOWN",
            "page_start": 1,
            "page_end": 1,
            "tasks": [{"label": "Task 1", "kind": "SELECT_ONE", "anchor_page": 1, "artifacts": []}],
        }]
    }
    machine = {
        "sections": [{
            "label": "Tasks",
            "semantic_type": "UNKNOWN",
            "page_start": 1,
            "page_end": 1,
            "tasks": [{
                "label": "Task 1",
                "number": "1",
                "kind": "SELECT_ONE",
                "page_start": 1,
                "page_end": 1,
                "body_blocks": [{"id": "b1"}],
                "body_spans": [{"page": 1, "bbox": [10, 10, 100, 80]}],
                "review_required": False,
                "artifacts": [{
                    "kind": "FIGURE",
                    "asset_binding_confidence": 0.8,
                }],
            }],
        }]
    }
    report = evaluate_document("demo", gold, machine)
    assert report["metrics"]["body_reconstruction_coverage"] == 1.0
    assert report["metrics"]["review_required_rate"] == 0.0
    assert report["metrics"]["asset_binding_confidence_avg"] == 0.8
