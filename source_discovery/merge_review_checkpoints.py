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
    "r313_historical_reconciled_apho_29.jsonl": "9a2a4e530e53f0ac6c3cefbbc4fc63373dba9f30",
    "r313_historical_reconciled_r413_39.jsonl": "9d75650d7df61c1cdd0b6ddf79bc11705ec321a4",
}
EXPECTED_ROWS = {"r313_historical_reconciled_apho_29.jsonl": 29, "r313_historical_reconciled_r413_39.jsonl": 39, "r337_review_r342_343_00_49.jsonl": 50, "r337_review_r342_343_50_99.jsonl": 50}
TYPE_CORRECTION_CHECKPOINTS = {
    "r307_r306_corrections_fixed.jsonl": "61254ca48e8195307d65609906992aad77815041",
}
ALLOWED_TYPES = {"task", "solution", "criteria", "participant_work", "archive", "source", "unrelated", "review"}


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()