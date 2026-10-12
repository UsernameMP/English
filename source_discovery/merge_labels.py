import json
from pathlib import Path

root = Path(__file__).resolve().parent
target = root / "link_labels.jsonl"
old = target.read_text(encoding="utf-8") if target.exists() else ""
known = set()
for line in old.splitlines():
    try:
        row = json.loads(line)
        known.add(row.get("url"))
    except ValueError:
        pass
new = []
for path in sorted((root / "runs").glob("labels_checkpoint_*.jsonl")):
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        url = row.get("url")
        if not url or not row.get("id") or not row.get("type") or url in known:
            continue
        known.add(url)
        new.append(row)
if new:
    with target.open("a", encoding="utf-8") as output:
        if old and not old.endswith("\n"):
            output.write("\n")
        for row in new:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
print("New canonical labels:", len(new))
