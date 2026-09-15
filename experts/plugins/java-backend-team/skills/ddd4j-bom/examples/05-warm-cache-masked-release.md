# Example 5 — Diagnosing the CI-only resolve failure

## Prompt

> Our brand-new CI runner can't resolve `ddd4j-parent` from the private repository, but every developer machine builds fine. The artifact was released two weeks ago. What is going on?

## What the skill should do

1. Recognize the signature: fresh machines fail, warm machines pass — a warm local repository is masking a missing or un-published remote artifact.
2. Verify the remote directly: query the private repository metadata for the exact parent coordinate and timestamped artifact, not the local `~/.m2`.
3. Reproduce the consumer gate on a cold repository (`-Dmaven.repo.local` to a fresh dir) on a "working" machine — it should now fail the same way, confirming the mask.
4. Check for the related trap: `enforcer.skip` or a `dependency:go-offline` run against a warm cache passing while the remote is incomplete.
5. Prescribe the fix and the evidence grade: re-publish the parent, then require the clean-cache resolve as the release gate.

## Expected output

```
Diagnosis: warm-cache masking.

Evidence:
  - New CI runner (empty repo): parent 2.0.x-<timestamp> → 404 (remote)
  - Developer machines: resolve from ~/.m2, never touch the remote
  - Cold-repo replay on a developer machine: fails identically  ← mask proven

Root cause candidates: parent upload failed or was pruned from the private
repository two weeks ago; every local build since has been served from cache.

Fix: re-publish `ddd4j-parent`, then re-run consumer `dependency:go-offline`
+ `compile` with -U on a clean repo. Evidence: remote metadata SOURCE +
CONSUMED (failed before, must be re-proven after re-publish).
```

## Failure the skill must avoid

Telling the team to "add the artifact to the CI image cache" — that industrializes the mask. The defect is on the remote; only a cold-cache gate proves it is fixed.
