# Example 5 — All green, broker feature broken in production

## Prompt

> Our CI was fully green for weeks, yet the first day in production the event consumption failed constantly. How did the suite miss a broken consumer?

## What the skill should do

1. Reconstruct what the green suite actually executed: which binder tests ran, and against what broker (embedded, in-memory, or real).
2. Locate the evidence gap — typically ACK-mode differences between the embedded binder and the real broker, or a container suite skipped for missing Docker and reported as covered.
3. Reclassify the historical reports: the broker tier was NOT VERIFIED, not PASS — and fix the reporting so it can't recur.
4. Reproduce the production failure against the real broker in the test environment, then fix and re-grade.
5. State the durable rule: green means executed-and-passed; everything else keeps its own label in the report.

## Expected output

```
Reconstruction:
  - Binder suite ran with the in-memory test binder; ACK default differs
    from real Kafka's configured mode.
  - Container suite: skipped (no Docker) — but reported under the generic
    "integration" green checkbox.

Reclassification: broker tier was NOT VERIFIED for weeks, not PASS.
Reporting fix: skips and embedded-only runs get their own label, never
folded into green.

Reproduction: real Kafka + configured ACK mode → consumer failure
reproduced; fix + rerun PASS. Historical reports corrected.
```

## Failure the skill must avoid

Blaming production config or "bad luck" while leaving the reporting intact. The suite missed the failure because the evidence report allowed embedded-broker coverage and skips to read as green — that reporting defect is the thing to fix.
