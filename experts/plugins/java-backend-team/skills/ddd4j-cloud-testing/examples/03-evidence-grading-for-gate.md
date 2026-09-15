# Example 3 — Grading evidence per tier for a release gate

## Prompt

> The release board wants per-capability evidence: what's proven, what's blocked, and why — for our service on the 2023.0.x line. Build the grading.

## What the skill should do

1. Fix the combination and record the exact SHA every suite ran against — evidence without a SHA is unanchored.
2. Grade each capability across the tiers: source-read, test-executed (real dependencies), remote consumption.
3. Classify every gap with the correct label: NOT VERIFIED (external behavior untested), BLOCKED(upstream), BLOCKED(infrastructure).
4. Never upgrade a tier by assumption — a mocked context test is not a propagation tier pass.
5. Output the per-capability table with the missing inputs phrased as "missing: X; how to provide: Y".

## Expected output

| Capability | Source | Test (real deps) | Remote | Gap |
|---|---|---|---|---|
| Context propagation | READ | PASS (incl. exception path) | n/a | — |
| Feign round-trip | READ | NOT VERIFIED (mocks only) | n/a | missing: two live services; how to provide: staging round-trip |
| Binder (Kafka) | READ | SKIPPED — no Docker in CI | — | BLOCKED(infrastructure) |
| Remote consumption | — | — | NOT RUN | missing: clean-cache pull; how to provide: private-repo access |

Verdict: gate blocked on Feign evidence + infrastructure.

## Failure the skill must avoid

Grading the Feign row as PASS because the mocked round-trip suite is green. The tier system exists precisely so mocked wiring and real dependency behavior are never reported as the same kind of evidence.
