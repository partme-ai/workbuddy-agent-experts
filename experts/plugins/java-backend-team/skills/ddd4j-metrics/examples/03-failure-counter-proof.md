# Example 3 — Proving the failure counter actually fires

## Prompt

> Sign-off question for our observability milestone: if a projection handler throws, does our failure metric go up and does the alert see it? The unit tests pass, but they passed before this milestone too.

## What the skill should do

1. Inspect what the passing tests actually assert — registration of the meter is the usual content, which proves nothing about increments.
2. Require a behavioral test: force a handler exception, assert the failure counter incremented, and assert no success or pseudo-success was recorded.
3. Check the exception path end to end: recording → exporter → collector/receiver → alert rule evaluation.
4. Verify the success counter does NOT increment on the exception path — the dual assertion prevents a pseudo-success implementation.
5. Grade evidence per hop and mark the export-chain and alert-drill steps if they have not run.

## Expected output

```
Milestone claim: "projection failures are observed and alerted"

Existing tests: meter registration asserted only (TEST, PASS — non-probative).

Required behavioral test:
  1. run projection with a handler that throws
  2. assert failure counter +1, success counter +0, position not advanced
  3. assert the record reached the in-memory exporter

Export chain: recording → OTel exporter → collector → NOT VERIFIED
Alert drill: rule fires on sustained failure / distinguishes no-data → NOT RUN

Verdict: claim NOT supportable yet. Missing: the behavioral increment test,
the export-chain check, and one alert drill.
```

## Failure the skill must avoid

Signing off on the green unit suite. Registration-without-increment tests are the canonical false green in metrics work — production counters at zero look identical to tests that never counted anything.
