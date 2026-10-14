#!/usr/bin/env python3
"""Voice is a first-class interaction inside existing packs; no separate sidecar."""
import hashlib
import json
from pathlib import Path
base=Path("app/src/main/assets/content")
cat=json.loads((base/"catalog.json").read_text())
ids={"math_ratio_001","math_count_001","math_mix_001"}
observed=set()
for entry in cat["packs"]:
    bank_path=Path("app/src/main/assets")/entry["asset"]
    data=bank_path.read_bytes()
    assert hashlib.sha256(data).hexdigest()==entry["sha256"],entry["id"]
    pack=json.loads(data)
    for q in pack["questions"]:
        if q["interaction"]!="spoken_reasoning": continue
        observed.add(q["id"])
        assert q["id"] in ids,q["id"]
        assert q["answer_policy"]["final_answer_type"] in ("numeric","short_text","none")
        assert q["reasoning_rubric"] in ("none","ratio-pilot-v1")
        assert q["source"]["original"] is True
        assert q["answer"]
assert observed==ids,(observed,ids)
assert not (base/"spoken_reasoning_candidates.json").exists()
src=Path("app/src/main/java/com/usernamemp/englishsprint/MainActivity.java").read_text()
assert 'if ("spoken_reasoning".equals(q.interaction))' in src
assert "new SpokenReasoningActivity" not in src
print("Voice only in mathematics pilot; grade-5 informatics is mic-free: ",len(observed))
