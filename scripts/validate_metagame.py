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
mini=json.loads((root/"app/src/main/assets/game/minigames.json").read_text())
production=[g for g in mini["games"] if g.get("enabled") and g.get("status")=="production"]
expected={"game_2048","tower_game","suika","match3","bubble_shooter","cozy_cafe"}
assert {g["id"] for g in production} == expected, "production mini-game registry drift"
assert all(g["duration_seconds"] == 60 for g in production), "production mini-games must use 60s sessions"
print("OK: crystal economy, 3-mode metagame, and 60s six-game production contract")
