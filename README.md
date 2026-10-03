# English Sprint — ВсОШ 5–6

Offline Android trainer for fast preparation for the school stage of the English Olympiad (Tatarstan, 5–6 grades).

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

GitHub Actions builds a debug APK on every push to `main`.

Open **Actions → Android APK → latest run → Artifacts → `english-sprint-v0.3.0`.**.

The CI workflow validates the content bank and generates bundled neural WAV listening files with Piper. The installed APK does not need Internet for listening.

## Local build

Requirements: JDK 17, Android SDK, Gradle 8.9.

```bash
gradle :app:assembleDebug
```

If bundled listening WAVs are absent, the app falls back to Android TextToSpeech.
