# Example 5 — Idempotency worked locally, duplicates in staging

## Prompt

> Our idempotency tests were all green, but staging (three replicas behind an LB) just double-processed two submissions with the same key. Local dev still passes. What changed?

## What the skill should do

1. Diagnose the deployment-shape mismatch: the tests pass because they run single-instance against Caffeine; staging runs three replicas, and Caffeine-backed idempotency deduplicates only within one JVM.
2. Trace the profile wiring on the current line: find where the cache backend is selected and confirm staging resolves to Caffeine (default or profile omission) rather than the distributed shared-CAS provider.
3. Explain why local is green and always will be: with one instance, Caffeine and shared CAS are indistinguishable — the defect only exists with more than one replica.
4. Fix contract-first: staging profile resolves the distributed provider; a two-instance concurrent same-key test must pass; Caffeine remains only as a documented dev/single-instance fallback.

## Expected output

```
Diagnosis: single-instance test green ≠ multi-instance idempotency.
  - Cache selection (CacheConfig.java:52): "cas" profile only when
    `deploy.replicas > 1` is set — staging env var missing ⇒ Caffeine.
  - Replicas: 3 ⇒ three independent dedup stores ⇒ duplicates on cross-replica replays.
  - Local dev: 1 instance ⇒ Caffeine behaves identically to CAS ⇒ permanently green.

Fix (contract-first):
  1. RED: two instances, same key, staging profile — duplicate effect (reproduced).
  2. Fail fast at startup when replicas > 1 without the shared-CAS provider.
  3. GREEN: cross-replica same-key test against the real backend.

Evidence: SOURCE read; staging repro from incident 4821. Test run NOT EXECUTED here.
```

## Failure the skill must avoid

Tuning Caffeine's TTL or size to "fix" the duplicates. The cache is functioning perfectly — it is the wrong backing store for the deployment shape, and no local test configuration will ever expose it.
