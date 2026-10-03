# English Sprint — ВсОШ 5–6

Offline Android trainer for fast preparation for the school stage of the English Olympiad (Tatarstan, 5–6 grades).

## MVP goals

- no text input: all answers are taps;
- 10–15 minute adaptive sessions;
- grammar micro-skills: be, have/has, do/does, articles, pronouns, tenses, prepositions, comparison, some/any;
- reading with evidence highlighting after the answer;
- story-builder exercises to prepare for the writing section without typing;
- offline listening;
- XP, streak/combo, levels and mastery by skill;
- olympiad sprint mode.

The first version is intentionally compact because the target preparation date is 9 October 2026.

## Build

GitHub Actions builds a debug APK on every push to `main`.

Open **Actions → Android APK → latest run → Artifacts → english-sprint-debug**.

The CI workflow generates bundled WAV listening files with `espeak-ng`, so the produced APK does not need Internet for listening.

## Local build

Requirements: JDK 17, Android SDK, Gradle 8.9.

```bash
gradle :app:assembleDebug
```

If bundled listening WAVs are absent, the app falls back to Android TextToSpeech.
