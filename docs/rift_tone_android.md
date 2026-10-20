# RIFT Voice: T-One 71M Android integration (#221)

## Fixed architecture

- All microphone audio and ASR processing remain on Android. No remote ASR, no transcription fallback to a cloud recognizer.
- A task's `spoken_reasoning` interaction uses the existing `SpokenReasoningWidget`; original recognized transcript and user-edited transcript remain **separate** in private per-attempt storage.
- Audio is deleted after recognition. Future server-side reasoning operates on an explicitly authorized **text transcript only**. No sync capability is introduced by this migration.

## Reproducible model

Upstream: `csukuangfj/sherpa-onnx-streaming-t-one-russian-2025-09-08`, commit `9d63341e0f2d8a8b2edaa825aa1fcfe3c5283b47`.

- ONNX model SHA-256: `5ded080e2a6c86ecc11bcb0902d77524eb3e8b0844cb0c0754347f5aafb4dabc` (upstream Git LFS ID, size 144,193,702 bytes).
- Model uses 8 kHz input. RIFT microphone captures 16 kHz mono PCM16 and applies an explicit 63-tap Hamming-windowed low-pass filter before decimation by 2.
- Runtime: `com.github.k2-fsa.sherpa-onnx:sherpa-onnx:v1.13.8` using the upstream Android Java API and `OnlineToneCtcModelConfig`.
- Upstream Apache-2.0 license: https://huggingface.co/csukuangfj/sherpa-onnx-streaming-t-one-russian-2025-09-08/blob/9d63341e0f2d8a8b2edaa825aa1fcfe3c5283b47/LICENSE .
- CI downloads only model.onnx and tokens.txt from the exact HF revision; verifies model SHA and vocabulary; bundles both inside the APK. No user ZIP/model download.
- Only arm64-v8a is explicitly packaged. Other ABIs require their own native validation.

## Critical caveat: verbatim speech

CTC models can delete repetitions, filler sounds, hesitations, self-corrections or negations even when grammar correction is disabled. This implementation does **not** claim zero omissions. Upstream decode is greedy search with endpoint segmentation disabled, no language-model correction and no rewriting of the ASR result. Record these omissions in the real child-speech benchmark (#225), including WER/CER and critical numeric/negation/operator accuracy.

## Remaining release gates

- GitHub Android CI on this PR: compile, model download/SHA, bundle/ABI assertions, static smoke.
- Physically verify ARM64 Android, airline mode, fresh install, microphone permission, transcription, repeated attempt, typed fallback and upgrades from current pilot APK.
- Measure real device startup, RTF, peak memory, CPU, thermal, battery and APK footprint; check unknown low-end device support.
- Compare against Vosk on identical consented child mathematical utterances with an independently transcribed verbatim gold set.
- The existing release signing weakness (#141) is **not** fixed by this migration. No production-ready signing claim until a private keystore is provisioned.

Release readiness is NOT established by a successful Gradle build alone.
