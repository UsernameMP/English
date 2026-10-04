#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
eco=json.loads((root/"app/src/main/assets/game/economy.json").read_text())
meta=json.loads((root/"app/src/main/assets/game/metagame_catalog.json").read_text())
r=eco["rewards"]; g=eco["economy_guardrails"]
assert r["correct_answer"] <= g["ordinary_task_target"], "ordinary crystal reward inflated"
assert max(r.values()) <= g["hard_task_target_max"], "single reward exceeds hard-task guardrail"
prices=[i["price_crystals"] for m in meta["modes"] for i in m["items"]]
assert min(prices) >= g["first_meaningful_purchase_min"], "first purchase too cheap"
assert len({m["id"] for m in meta["modes"]}) >= 3
assert {"pet","defense","hero"} <= {m["id"] for m in meta["modes"]}
print("OK: crystal economy and 3-mode metagame guardrails")
