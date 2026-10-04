#!/usr/bin/env python3
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
catalog=json.loads((ROOT/"app/src/main/assets/content/catalog.json").read_text())
out=ROOT/"build/content-pilot"; out.mkdir(parents=True,exist_ok=True)
manifest={"schema_version":"1.0","channel":"public-pilot","warning":"No secrets. Production paid content must use authenticated backend.","packs":{}}
for p in catalog["packs"]:
    if not p.get("enabled",True): continue
    src=ROOT/"app/src/main/assets"/p["asset"]
    raw=src.read_bytes()
    name=p["id"]+".json"
    (out/name).write_bytes(raw)
    manifest["packs"][p["id"]]={
        "version":p["content_version"],
        "sha256":hashlib.sha256(raw).hexdigest(),
        "url":f"https://raw.githubusercontent.com/UsernameMP/English/content-pilot/{name}"
    }
(out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
print(f"Prepared {len(manifest['packs'])} pilot packs")
