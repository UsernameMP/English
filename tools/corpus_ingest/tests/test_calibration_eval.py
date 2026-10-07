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
