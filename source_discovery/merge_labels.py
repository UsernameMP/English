import json
from pathlib import Path

root = Path(__file__).resolve().parent
target = root / "link_labels.jsonl"
old = target.read_text(encoding="utf-8") if target.exists() else ""
known = set()
for line in old.splitlines():
    try:
        row = json.loads(line)
        known.add(row.get("raw_occurrence_id") or row.get("id"))
    except ValueError:
        pass
new = []
for path in sorted((root / "runs").glob("labels_checkpoint_*.jsonl")):
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        raw_id = row.get("raw_occurrence_id") or row.get("id")
        if not row.get("url") or not raw_id or not row.get("type") or raw_id in known:
            continue
        known.add(raw_id)
        new.append(row)
if new:
    with target.open("a", encoding="utf-8") as output:
        if old and not old.endswith("\n"):
            output.write("\n")
        for row in new:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
print("New canonical labels:", len(new))
