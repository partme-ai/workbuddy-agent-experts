# Example 5 — Consumer build fails though the deploy "succeeded"

## Prompt

> We deployed all eight lines over the weekend. Monday, the first consumer build on 2021.0.x fails with a missing artifact. The deploy log said everything succeeded. What went wrong?

## What the skill should do

1. Recognize the signature: zero deploy exit plus consumer-side missing artifact means the completeness proof was skipped — the exit code alone was trusted.
2. Diff the remote metadata for the 2021.0.x line against the full expected artifact set; identify exactly which artifacts are absent.
3. Check whether the gap is incomplete metadata from the deploy, or a genuinely missing upstream Boot/ddd4j artifact (BLOCKED(upstream)).
4. Re-run the affected deploy with metadata-completeness verification, then prove it with isolated clean-cache consumption (`-U`).
5. Report redacted errors only, and record the corrected evidence for the release report.

## Expected output

```
Remote metadata diff (2021.0.x):
  expected: <n> artifacts   present: <n-2>
  missing:  <artifact-a (sources)>, <artifact-b>

Deploy log: zero exit — completeness never verified. Exit code proved
the command ran, not that the repository is complete.

Fix: redeploy with metadata verification → complete; clean-cache (-U)
consumer proof → PASS.
Classification: release-process defect, NOT BLOCKED(upstream) —
upstream artifacts were all present.
Evidence: REMOTE, isolated; errors redacted.
```

## Failure the skill must avoid

Declaring the consumer wrong because "the deploy succeeded" and pointing at their settings. The weekend release skipped the two proofs that matter — remote metadata completeness and clean-cache consumption — so the success claim was never evidence.
