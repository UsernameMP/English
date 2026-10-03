# Content format

The application runtime is subject-independent. Training material lives in a canonical JSON bank.

Current bank: `app/src/main/assets/content/english_g5_vso.json`.

Core fields:
- `subject`, `grade_min`, `grade_max`
- `interaction`: UI interaction type
- `mode`: grammar / reading / listening / story
- `skills[]`: adaptive-learning tags
- `stimulus.text/audio/image`
- `prompt`, `options[]`, `answer[]`
- `feedback.short/full/rule`
- `evidence`: exact text span used for reading highlighting
- `review.status`

The Android renderer currently ships `single_choice`. The schema reserves future interactions so physics, mathematics and other olympiad subjects can share the same engine.

Run before committing content:

```bash
python3 scripts/validate_content.py
```


## Product packs and Knowledge Atlas compatibility

The app loads a pack through `assets/content/catalog.json`. A pack owns product metadata (subject, grade range, competition, season) and can be swapped without changing the question renderer.

Every shipping question also references one or more stable `knowledge_units`:

```json
"knowledge": [
  {"id": "ENG.GRAMMAR.ARTICLES", "weight": 1.0}
]
```

Legacy skill strings remain as tags for compatibility only. Learner mastery is migrated to knowledge-unit IDs so future packs can reuse the same knowledge node across grades and, later, across subjects.
