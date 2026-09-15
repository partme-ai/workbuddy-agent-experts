# Example 2 — Read-only audit of an existing suite for false greens

## Prompt

> Our 6.7.x suite is 400 tests, all green, but we've had three prod incidents the suite never caught. Read-only audit: where is this suite lying to us?

## What the skill should do

1. Stay read-only; classify every test as contract-asserting, smoke-only, or skipped-in-disguise.
2. Find the skips: containers conditionally skipped when Docker is absent, `@Disabled` tests, empty test classes, and assumption failures that report as green.
3. Check what the "HTTP tests" actually assert — status-only assertions on endpoints whose behavior depends on auth, DB, or context.
4. Check lifecycle coverage: partial-startup rollback, repeated starts, and hook accumulation tests — the areas where prod incidents usually live.

## Expected output

```
Suite audit (6.7.x, 400 tests, all "green"):

  Smoke-only (status assertions, no payload/side-effect): 137  ← false green risk
  Skipped in disguise:
    - 42 container tests skipped (Docker unavailable on CI runner) → reported PASS
    - 8 @Disabled "flaky" tests, incl. repeated-start hook test
  Contract-asserting: 213 — healthy

  Coverage holes vs. recent incidents:
    - Partial-startup rollback: no test            ← incident #4813 class
    - Expired-token 401: status-only, expired case absent ← incident #4790 class

Recommendation: reclassify skips as BLOCKED/SKIPPED in reporting; add the two
missing lifecycle/auth contracts before the next release.
```

## Failure the skill must avoid

Summarizing "400 tests, all green, suite looks healthy". The green number is the lie — the audit exists to break it into what actually asserted behavior versus what was skipped or asserted nothing.
