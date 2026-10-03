# Development workflow

English Sprint uses a lightweight GitHub Flow.

1. Every meaningful product change starts with an Issue.
2. Create a short-lived branch from `main`:
   - `feat/...`
   - `fix/...`
   - `content/...`
   - `chore/...`
3. Open a PR back to `main`.
4. CI must validate content and build the Android APK.
5. Review the diff and product behavior.
6. Merge only a green PR.
7. `main` is always expected to be installable.

Small typo/content corrections may share one Issue/PR when they are one logical change.

## Content rule

Question content belongs in content packs, not Java. Shipping content must pass the validator and have a published/verified review state.

## Architecture rule

The runtime must not depend on a specific subject, grade or competition. Subject-specific behavior belongs in content metadata and interaction renderers.
