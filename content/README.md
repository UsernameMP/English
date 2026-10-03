# Content format

The application runtime is subject-independent. Training material lives in a canonical JSON bank.

Current bank: `app/src/main/assets/content/english_g5_vso.json`.

Core fields:
- `subject`, `grade_min`, `grade_max`
- `interaction`: UI interaction type
- `mode`: subject-neutral `practice`, or specialized grammar / reading / listening / story
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

The catalog is entitlement-filtered at runtime. Selection is persistent, while XP and Knowledge Unit evidence remain global. `licenses.json` is a release gate: every enabled pack must reference active, distributable rights. Content provenance is separate from both task JSON and commerce state.

`commerce/products.json` describes provider-neutral saleable scopes for pilot, Google Play, App Store, RU/CIS and promo adapters. Checkout remains disabled until a provider-specific legal, receipt-verification and store implementation exists.

Every shipping question also references one or more stable `knowledge_units`:

```json
"knowledge": [
  {"id": "ENG.GRAMMAR.ARTICLES", "weight": 1.0}
]
```

Legacy skill strings remain as tags for compatibility only. Learner mastery is migrated to knowledge-unit IDs so future packs can reuse the same knowledge node across grades and, later, across subjects.


## Localization

UI language and learning-content language are separate concerns.

Android UI copy lives in `res/values*/strings.xml`. Initial locales are `en` and `ru`.

Question feedback fields are locale maps rather than duplicated questions:

```json
"feedback": {
  "short": {"ru": "...", "en": "..."},
  "full": {"ru": "...", "en": "..."},
  "rule": {"ru": "...", "en": "..."}
}
```

The runtime selects the device/app locale, then falls back to English, Russian, or the first available translation. This allows future `uz`, `kk`, `vi`, `zh` and other locales without cloning the underlying exercise.


## Personal dictionary

English packs may ship an offline learner dictionary in `assets/content/dictionary_en.json`. Known words become tappable in task text. A learner can save a word locally; saved words are then eligible for vocabulary questions mixed into adaptive quick sessions.

Dictionary entries support forms/inflections, phonetics, localized translations/definitions and an example sentence. The dictionary is validated in CI together with the question bank.


## Publishing workflow

Content moves through `draft → review → verified → published`. Only `published` questions may be packaged into a release build.

CI rejects duplicate IDs, duplicate prompts for the same knowledge unit, invalid answer references, missing explanations, broken Reading evidence spans, duplicate Listening scripts, pack/grade mismatches, unknown Knowledge Unit IDs and malformed dictionary entries.

Use:

```bash
python3 scripts/validate_content.py
python3 scripts/content_report.py
```


## Listening audio

Shipping Listening items are generated offline in CI with Piper neural voices and packaged as WAV assets. The current English pack uses two voices (`lessac` and `ryan`), supports per-item pace metadata, and can define multi-speaker `segments` that are concatenated into a single offline asset. CI verifies that dialogue segments reconstruct the canonical script and use at least two voices.
