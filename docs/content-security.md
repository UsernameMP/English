# Protected content delivery

## Assumption
The APK and the device are untrusted. Reverse engineering, rooted-device access, runtime hooks and copied caches are expected threats. Client-side obfuscation is defense in depth, not authorization.

## Production boundary
Public metadata (subjects, grades, olympiad families/stages, prices and availability) may ship with the app. Paid question payloads must not.

Production flow:
1. Authenticated client requests a bounded learning batch.
2. Backend verifies account, active subject subscription, requested grade/competition scope and risk signals.
3. Planner selects only the next required task IDs. IDs exposed to clients are opaque/non-enumerable.
4. Backend returns a signed, expiring content envelope with a small batch (client contract currently caps requests at 30).
5. Offline cache is encrypted at rest with a per-install/session content key protected by Android Keystore; no corpus/master key is hardcoded in the APK.
6. Cache has expiry, size ceiling and revocation/version metadata. Logout/subscription expiry removes usable cached paid content.
7. API applies account/device quotas, rate limits, replay protection and extraction anomaly detection.

## Key model
Server signing/private keys and corpus encryption master keys never ship to clients. Client may contain public verification keys. Device-local wrapping keys are generated in Android Keystore. Content data keys are short-lived and scoped to an authorized envelope/cache generation.

## Attestation
Play Integrity / App Attest style signals are optional server-side risk inputs, never the only authorization mechanism. Unsupported or degraded devices receive reduced offline/cache allowances rather than gaining a bypass.

## Pilot transition
Current JSON assets remain temporarily for the offline pilot. Production CI must later reject protected task banks in release assets (#95). `ContentDeliverySource` is the migration seam: the bundled source is replaced by the server source without changing learning UI/domain code.

## Abuse controls
No bulk export endpoint. No sequential task enumeration. Bounded adaptive pagination, opaque cursors, per-account/device budgets, telemetry for abnormal traversal, and server-side entitlement checks on every content grant.

## Incident response
Rotate signing/content keys, revoke sessions/cache generations, disable compromised app versions, invalidate affected envelopes, preserve privacy-minimized audit events, and issue a forced minimum-version policy when required.
