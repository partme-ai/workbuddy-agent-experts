# Example 2 — Read-only audit of a CI test report

## Prompt

> Our pipeline is green and leadership wants to ship. Before I sign, check the last CI report read-only — I don't fully trust it.

## What the skill should do

1. Stay read-only — audit the report and the pipeline definition, change nothing.
2. Reclassify every entry: real PASS, real FAIL, SKIPPED (with reason), and anything reported green that never executed.
3. Check the three classifications are used correctly: NOT VERIFIED vs BLOCKED(upstream) vs BLOCKED(infrastructure).
4. Verify the compatibility suite actually ran against MySQL, not an embedded substitute.
5. Produce the corrected evidence inventory and the explicit list of what remains unproven.

## Expected output

```
Report audit (pipeline run #<id>):
  Reported green: 47 tests
  Reclassified:
    41 real PASS
    4 SKIPPED — "broker not reachable in CI" → NOT VERIFIED (reported green)
    2 SKIPPED — container suites, no Docker → SKIPPED(infrastructure)
  Compatibility suite: ran against H2, NOT MySQL — pairing not satisfied
  CI for verification consumers: stage absent → BLOCKED(infrastructure)

Corrected verdict: NOT ship-ready. 4 capabilities lack real evidence.
```

## Failure the skill must avoid

Signing off because the dashboard is green. The audit's job is the reclassification — four skipped broker tests and an H2-based compatibility run are the difference between green and actually verified.
