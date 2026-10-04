# English Sprint — ВсОШ 5–6

Offline Android trainer for fast preparation for the school stage of the English Olympiad (Tatarstan, 5–6 grades).

## v0.6.7

- an original 12-task Mathematics Grades 5–7 pack adds five global MATH Knowledge Units;
- reusable sequence-order tasks work across the generator, validator and Android runtime;
- Home shows blueprint-weighted readiness separately from evidence confidence;
- a deterministic publisher CLI refreshes and checks pack versions and SHA-256 manifests;
- a bounded privacy-safe event ledger prepares adaptive calibration and future opt-in sync;
- versionName 0.6.7 / versionCode 14; package ID, pilot signing chain and updater channel are unchanged.

## v0.6.4

- the runtime now loads an entitlement-filtered multi-pack catalog and persists pack selection;
- an original Informatics olympiad pilot proves the renderer and Knowledge Unit model outside English;
- the adaptive planner now uses Knowledge Atlas prerequisites, not only direct mastery and recent errors;
- Home shows a short prerequisite-first focus plan;
- a neutral offline activity calendar stores daily answers, accuracy, XP, crystals, combo and completed sessions without streak punishment;
- every enabled content pack must pass a machine-checked distribution-rights manifest;
- a provider-neutral product catalog separates Google Play / App Store / RU-CIS / promo scopes from entitlement decisions and learning code;
- versionName 0.6.4 / versionCode 11; the package ID, pilot signing chain and direct APK channel remain unchanged.

## v0.6.3

- XP, crystals and game-session rights are now three separate persistent resources;
- every completed learning block can earn a bounded 🎮 play credit, and starting a mini-game consumes one;
- Knowledge Atlas is a separate global relation graph with typed edges and acyclic `requires` validation;
- every shipped question now has explicit `prerequisites`; `knowledge` remains the assessed knowledge set;
- question explanations show both assessed knowledge and prerequisites;
- training target is persistent and editable: subject/grade/competition mode and target date are no longer hard-coded in MainActivity;
- content access now goes through a payment-provider-neutral entitlement abstraction;
- current English pilot pack is granted by a local pilot entitlement;
- `generator/` defines the canonical generated-question schema and deterministic draft generator;
- CI validates generator output, Atlas references/cycles, prerequisites, play-credit config, entitlements and training targets.

### Architectural boundaries

`content packs` contain questions and pack metadata.  
`knowledge_atlas.json` contains cross-pack knowledge relationships.  
`commerce/entitlements.json` describes what content is accessible; future Google Play / App Store / RU-CIS payment adapters will only produce entitlements and will not be embedded into the learning engine.  
`generator/` creates draft question JSON and can later be driven by human editors, imports or LLM pipelines. It never publishes directly.  
Game engines consume game-session rights and do not own educational content.

## v0.6.2

- updater keeps download + package/version/signature verification but hands the verified APK to the visible Android system installer via FileProvider;
- if per-app unknown-source permission is missing, the verified APK is retained and installation resumes automatically after returning from Settings;
- removes the fragile PackageInstaller.Session callback path that could fail silently on MIUI/POCO.

## v0.6.1

- Match-3 now animates swap, invalid return, match pop, drop/refill, cascades and reshuffle with dedicated game sounds;
- Listening keeps prompt/answers at normal top position while only the blue Listen action is pinned low in the thumb zone;
- positive answer chimes are slightly louder;
- update controls moved from Home to Settings;
- Reading text is plain black; any tapped English word highlights temporarily and opens dictionary lookup;
- dictionary is local-first with online fallback via dictionaryapi.dev and persistent cache;
- CI artifact/APK naming now follows versionName dynamically.

## Versioning policy

Stay on the `0.6.x` line for iterative MVP builds. Android `versionCode` still increments every build. Do not bump to `0.7.0` without explicit product-owner approval.

## v0.6

- Listening play/replay action moved substantially lower into the real thumb reach zone;
- positive-answer audio replaced with a short synthesized rising chime instead of weak system beeps;
- break-game rotation now cycles through Match-3, Memory pairs and Spark without immediate repeats;
- Match-3: 6×6 gem board with swaps, matches, cascades, refill and no-move reshuffle;
- Memory: 4×4 / 8 pairs with a bounded timer;
- first stable pilot signing chain uses the public AOSP test key (deliberately non-production);
- CI publishes a raw APK plus `latest.json` on the `apk-dist` branch;
- app checks the direct update channel, verifies package/version/signature, downloads and invokes Android's update installer.

## v0.5

- Listening primary action moved into a lower thumb-friendly task action zone;
- separate crystal economy with persistent balance, lifetime earned/spent and transaction ledger;
- configurable earning rules for correct answers, combos, records, mastery, reinforcement and 10-question blocks;
- data-driven reward shop with backgrounds, button shapes, sound packs, frame and custom title;
- original owned digital reader redeemable for crystals;
- partner codes/sticker rewards remain disabled until rights/server fulfillment are available;
- generic MiniGameHost with a bounded 45-second Tap Spark break after configurable learning blocks;
- mini-game can be skipped and returns to the exact learning session;
- game/economy/shop/reward configs are validated in CI.

## v0.4

- generic content-pack runtime and stable Knowledge Unit IDs;
- learner progress migration from legacy skill tags;
- English/Russian UI localization foundation and localizable content feedback;
- offline personal dictionary with tappable words and vocabulary reinforcement;
- stronger configurable reward audio and NEW RECORD celebration;
- in-session remediation: a missed knowledge unit returns as a different question 3–5 steps later;
- all v0.3 content validation, neural offline listening and adaptive training remain in place.

## v0.3

- canonical subject-independent JSON content bank;
- 150 verified training questions;
- CI content validator;
- adaptive weak-skill repetition without a visible "mistakes" mode;
- neutral skill map: untested topics are not shown as failures;
- large "Why?" explanations;
- game-first home screen, XP, ranks and combo effects;
- offline listening generated with a neural Piper voice;
- sound and haptic settings.

The Android renderer currently uses tap-only single-choice interactions. The content schema already reserves future interaction types for other olympiad subjects.

## Build

GitHub Actions builds a stable pilot-signed release APK on every push to `main`.

The workflow also publishes:
- `apk-dist/english-sprint-latest.apk` for direct download (no ZIP wrapper);
- `apk-dist/latest.json` for the in-app updater.

The pilot signing key is the public AOSP test key and is intentionally unsuitable for production. Store releases will use a separate production signing chain.

The CI workflow validates the content bank and generates bundled neural WAV listening files with Piper. Listening remains fully offline; Internet is only used for update checks/downloads.

## Local build

Requirements: JDK 17, Android SDK, Gradle 8.9.

```bash
gradle :app:assembleRelease
```

If bundled listening WAVs are absent, the app falls back to Android TextToSpeech.
