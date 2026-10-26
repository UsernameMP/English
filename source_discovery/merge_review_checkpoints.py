#!/usr/bin/env python3
"""Idempotently merge explicitly audited RIFT Review checkpoints, without downloading documents.

Only the explicitly audited reviewed resource shards listed here are eligible. Older historical
checkpoints require separate reconciliation and are intentionally not merged.
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "link_labels.jsonl"
CHECKPOINTS = {
    "r294_review_r299.jsonl": "bc2fb77519dbc39631edc2166315fc72703cae3a",
    "r295_review_r300.jsonl": "c578f9c6b466ce51704d0ec31c49c5c61d20ed1f",
    "r296_review_r301.jsonl": "1f3ad337080850ecd2c54105d33f8bab4231d0ab",
    "r297_review_r302.jsonl": "65d4536e4828574921456ce649dafb94a3b4995e",
    "r298_review_r303.jsonl": "08ad3a871798448ffc2bacdb591d0ae2ac4fd37a",
    "r299_review_r304.jsonl": "293a93e58479ccc7806638c5fcfa916273e9959e",
    "r300_review_r305.jsonl": "f7639b0785919311d3df88405cb6b8462c3b89fb",
    "r301_review_r306.jsonl": "9f574a33f87a1f2c06fef96442a62b738f982a4e",
    "r302_review_r307.jsonl": "f59716a0b441557c6693a95436aa925253be8261",
    "r303_review_r308.jsonl": "6ee039da354c2f423ee1b099fdbbb6c879b2f1b3",
    "r304_review_r309.jsonl": "a5297f262cecd074e3327f29beeb85d2518c6e0a",
    "r305_review_r310.jsonl": "c497cae957172af9cfb7f4ceb0bbd4acb27502ee",
    "r306_review_r311.jsonl": "7398a8845c27a10193f0993716ac864367e90abf",
    "r307_review_r312.jsonl": "39485d7151f2f72c12b4ebcae6a3af0dae59404b",
    "r308_review_r313.jsonl": "6f1023442a34d73da3bbedc1ed500b4a67c3f212",
    "r309_review_r314.jsonl": "b4a6c2d457d8f04b5442cc820f8f8ad34b8c49c5",
    "r310_review_r315.jsonl": "f7a85607997343f15eddf16e3372e7601dbc792f",
    "r311_review_r316.jsonl": "44efa09651b1c1a1ba376863cb08b952e55cdab6",
    "r312_review_r317.jsonl": "9def741c80390429b330c0bbf46963135f123a6f",
    "r313_review_r318.jsonl": "d6627a7af10f90ea19bb330bcfea4e686bc7bd3f",
    "r314_review_r319.jsonl": "0bfcd59a94f115c5f8951b2101410f4b6a937252",
    "r315_review_r320.jsonl": "73e9d45c3609c2c61146357527e523e06d1e63c3",
    "r316_review_r321.jsonl": "64dd6748788186625586d6c1d174ad6b79b8a3d0",
    "r317_review_r322.jsonl": "b5681a897720aadf67e9adb55ae1fc78aca90b39",
    "r318_review_r323.jsonl": "2613b46aa06e281353ad04a29853e11639253900",
    "r319_review_r324.jsonl": "2859b8053dc976d7de1859f4bf3fb37584532916",
    "r320_review_r325.jsonl": "35336d00e09cb8dbcbb277e86d1dd9a9ca3c0b02",
    "r321_review_r326.jsonl": "0bb11f34197902841cf62c0213317847f79056c5",
    "r322_review_r327.jsonl": "8e3bfc9f0990b3d35033163fe5d36dc17508c5b6",
    "r323_review_r328.jsonl": "dbaaf5795bf565caebc9a7e24f28457bf61d520b",
    "r324_review_r329.jsonl": "3a2192162e2e3fb50f46f827dd0922e790f02ed3",
    "r325_review_r330.jsonl": "76d34ff82c779b8a7b6e5673ab305b1f5acda1a3",
    "r326_review_r331.jsonl": "8c0c30e2fe7d4db827992e37a91b2dd73d9c179e",
    "r327_review_r332.jsonl": "42d05cd4c78021f69cd8c2f2b0d79acd7d20c1ec",
    "r328_review_r333.jsonl": "9e340a0ae9a3f7674827201528faa62cb84b9d59",
    "r329_review_r334.jsonl": "8815e098f2d5f05124739f3f2b7e3ff258e6f9c8",
    "r330_review_r335.jsonl": "32159fe2fbe0eaefef89f6002a8d4c211d34ff48",
    "r331_review_r336.jsonl": "b3e6d8741a2455f6f1b9b60e6a9741e51fcedbe5",
    "r332_review_r337.jsonl": "7ec38afed96a12719a766c5700f8f41f14adb73d",
    "r333_review_r338.jsonl": "cd74d665b92c91219fea1a1729800ca4eec90bba",
    "r334_review_r339.jsonl": "fb2694ba8d4efaa4721d91011fc3b33499b60d0b",
    "r335_review_r340.jsonl": "8307595398375b10c356b3ad84fa43fd6df5e3bd",
    "r336_review_r341.jsonl": "7ba4b1cd35b73936fe3418b70f2779f2a73ca48b",
    "r337_review_r342_343_00_49.jsonl": "79544ba01295141ec60b06512eb5e322311718d7",
    "r337_review_r342_343_50_99.jsonl": "8d077e68d037a5dab7c4cc9b8cb28f9124cb9fbc",
    "r338_review_r343_344_00_49.jsonl": "fb6b56bac44621a490b25b7958b1b6b4782da5f8",
    "r338_review_r343_344_50_99.jsonl": "ed4ec41055a124369cd0639a0a8859bea48e1f1c",
    "r339_review_r344_345_00_49.jsonl": "92c03eb9ae0ca9187f286014439f5be7f5896446",
    "r339_review_r344_345_50_99.jsonl": "831e9801e0e43f2c3b7b78467aa5abe6361549cb",
    "r340_review_r345_346_00_49.jsonl": "ac92745da482b3847b5fa894c673dfc4e3b6332a",
    "r340_review_r345_346_50_99.jsonl": "8289f46630a657147528a7e621a38f24f49daffe",
    "r341_review_r346_347_00_49.jsonl": "965c20d55b508f4c93ea30b529c3d296347382ec",
    "r341_review_r346_347_50_99.jsonl": "3f920b666720aaa5ef43b3209cb338c904005cd5",
    "r342_review_r347_348_00_49.jsonl": "c8fddef80c9beb558ef660e91393a5ecc83c1739",
    "r342_review_r347_348_50_99.jsonl": "024a728bf68f34f33f32d54be2f86dbb4effb19e",
    "r343_review_r348_349.jsonl": "97dc7701c9d1accbf3f5a700144bd8f79589cd54",
    "r344_review_r349_350_00_49.jsonl": "8d22e0276e11252d16d53f8ce5ff175344eba5ec",
    "r344_review_r349_350_50_99.jsonl": "b2a32a5500874161d40312dd5bc0ca1e24ccfacd",
    "r345_review_r350_351_00_49.jsonl": "741112f86f67b13af908da7a130952cfe801a7f9",
    "r345_review_r350_351_50_99.jsonl": "58ecb928aca5589440d01c408a571e77d178fbb0",
    "r313_historical_reconciled_apho_29.jsonl": "9a2a4e530e53f0ac6c3cefbbc4fc63373dba9f30",
    "r313_historical_reconciled_r413_39.jsonl": "9d75650d7df61c1cdd0b6ddf79bc11705ec321a4",
}
EXPECTED_ROWS = {"r345_review_r350_351_00_49.jsonl": 50, "r345_review_r350_351_50_99.jsonl": 50, "r344_review_r349_350_00_49.jsonl": 50, "r344_review_r349_350_50_99.jsonl": 50, "r342_review_r347_348_00_49.jsonl": 50, "r342_review_r347_348_50_99.jsonl": 50, "r341_review_r346_347_00_49.jsonl": 50, "r341_review_r346_347_50_99.jsonl": 50, "r340_review_r345_346_00_49.jsonl": 50, "r340_review_r345_346_50_99.jsonl": 50, "r339_review_r344_345_00_49.jsonl": 50, "r339_review_r344_345_50_99.jsonl": 50, "r313_historical_reconciled_apho_29.jsonl": 29, "r313_historical_reconciled_r413_39.jsonl": 39, "r337_review_r342_343_00_49.jsonl": 50, "r337_review_r342_343_50_99.jsonl": 50, "r338_review_r343_344_00_49.jsonl": 50, "r338_review_r343_344_50_99.jsonl": 50}
TYPE_CORRECTION_CHECKPOINTS = {
    "r307_r306_corrections_fixed.jsonl": "61254ca48e8195307d65609906992aad77815041",
}
ALLOWED_TYPES = {"task", "solution", "criteria", "participant_work", "archive", "source", "unrelated", "review"}


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def parse_jsonl(data, label):
    rows = []
    for line_no, line in enumerate(data.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{label}:{line_no}: malformed JSON") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"{label}:{line_no}: expected object")
        rows.append(obj)
    return rows


def audited_type_corrections():
    """Load only SHA-pinned, provenance-matched corrections already applied to canonical labels."""
    overrides = {}
    for filename, expected_sha in TYPE_CORRECTION_CHECKPOINTS.items():
        data = (ROOT / "runs" / filename).read_bytes()
        if git_blob_sha(data) != expected_sha:
            raise ValueError(f"{filename}: unexpected correction blob SHA")
        for patch in parse_jsonl(data, filename):
            occurrence = patch.get("raw_occurrence_id")
            if not occurrence or occurrence in overrides:
                raise ValueError(f"{filename}: duplicate/missing corrected occurrence")
            overrides[occurrence] = dict(patch, correction_checkpoint=filename)
    return overrides


def is_audited_type_override(canonical, original, overrides):
    """Allow a prior reviewed label to differ only when an audited correction changed its type."""
    occurrence = canonical.get("raw_occurrence_id")
    patch = overrides.get(occurrence)
    return bool(
        patch
        and canonical.get("correction_checkpoint") == patch["correction_checkpoint"]
        and original.get("resource_id") == canonical.get("resource_id") == patch.get("resource_id")
        and original.get("url") == canonical.get("url") == patch.get("url")
        and original.get("type") == patch.get("previous_type")
        and canonical.get("type") == patch.get("corrected_type")
    )


def merge():
    old_data = TARGET.read_bytes()
    canonical = parse_jsonl(old_data, TARGET.name)
    by_occurrence = {}
    by_resource = {}
    for row in canonical:
        occurrence = row.get("raw_occurrence_id") or row.get("id")
        resource = row.get("resource_id")
        if occurrence:
            if occurrence in by_occurrence:
                raise ValueError(f"Duplicate canonical raw occurrence: {occurrence}")
            by_occurrence[occurrence] = row
        if resource:
            by_resource.setdefault(resource, row)

    new = []
    skipped = 0
    audited_overrides = audited_type_corrections()
    corrected_skipped = 0
    for filename, expected_sha in CHECKPOINTS.items():
        path = ROOT / "runs" / filename
        data = path.read_bytes()
        actual_sha = git_blob_sha(data)
        if actual_sha != expected_sha:
            raise ValueError(f"{filename}: unexpected Git blob SHA {actual_sha}")
        rows = parse_jsonl(data, filename)
        expected_rows = EXPECTED_ROWS.get(filename, 100)
        if len(rows) != expected_rows:
            raise ValueError(f"{filename}: expected {expected_rows} records, got {len(rows)}")
        for row in rows:
            occ = row.get("raw_occurrence_id")
            rid = row.get("resource_id")
            url = row.get("url")
            kind = row.get("type")
            if not occ or not rid or not url or kind not in ALLOWED_TYPES:
                raise ValueError(f"{filename}: incomplete review row {occ!r}")
            prior = by_occurrence.get(occ)
            if prior:
                if prior.get("resource_id") != rid or prior.get("url") != url:
                    raise ValueError(f"Conflicting occurrence provenance: {occ}")
                if prior.get("type") != kind:
                    if not is_audited_type_override(prior, row, audited_overrides):
                        raise ValueError(f"Conflicting occurrence type: {occ}")
                    corrected_skipped += 1
                skipped += 1
                continue
            prior_resource = by_resource.get(rid)
            if prior_resource:
                if prior_resource.get("url") != url:
                    raise ValueError(f"Conflicting resource URL: {rid}")
                if prior_resource.get("type") != kind:
                    if not is_audited_type_override(prior_resource, row, audited_overrides):
                        raise ValueError(f"Conflicting resource type: {rid}")
                    corrected_skipped += 1
                skipped += 1
                continue
            by_occurrence[occ] = row
            by_resource[rid] = row
            new.append(row)

    if new:
        addition = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in new)
        prefix = old_data + (b"\n" if old_data and not old_data.endswith(b"\n") else b"")
        content = prefix + addition.encode("utf-8")
        fd, temp_name = tempfile.mkstemp(prefix=".rift-labels-", dir=str(ROOT))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, TARGET)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
    print(f"RIFT reviewed checkpoint merge: existing={len(canonical)} added={len(new)} skipped={skipped} audited_type_overrides={corrected_skipped} total={len(canonical)+len(new)}")
    return len(new)


if __name__ == "__main__":
    merge()
