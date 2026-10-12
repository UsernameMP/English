# RIFT inline spoken reasoning: offline model supply chain

The APK **bundles** Russian Vosk model `vosk-model-small-ru-0.22`, licensed under Apache-2.0 as published by Alpha Cephei. The model is downloaded reproducibly during GitHub Actions, verified against a fixed SHA-256, then included in the signed Android APK; users do not download, select, or import any separate model. First use extracts the packaged ZIP into app-private no-backup files and checks the pinned ZIP digest. It does not contact the network.

- Official model catalog: https://alphacephei.com/vosk/models
- Immutable mirrored archive: https://huggingface.co/rhasspy/vosk-models/blob/e7ac2109d134b5f2404ba95389b2fb51916d4cab/ru/vosk-model-small-ru-0.22.zip
- Archive SHA-256: `961d5ff98a17f4aa6de69864d0aa71fa5bac682301d2b5d17a3f24c5c99a46d4`
- Android library: `com.alphacephei:vosk-android:0.3.75`
- Archive footprint per published repository: ~46.2 MB. Actual signed APK size and phone memory consumption must be measured.
- Model license: Apache-2.0. See https://www.apache.org/licenses/LICENSE-2.0 . Include upstream attribution on product's third-party notices before production distribution.
- Storage: packaged at `assets/models/vosk-model-small-ru-0.22.zip` in CI; extracted to `getNoBackupFilesDir()/vosk_models/ru`.
- Airplane mode: ASR uses Vosk in-process and has no remote recognition fallback.
- No weights in Git. If the asset is missing or mismatched, the Gradle build fails. No replacement model is downloaded by the Android application.

This document describes the supply chain, not measured WER. Russian child speech and mathematical number transcription need a real-phone benchmark (#212).
