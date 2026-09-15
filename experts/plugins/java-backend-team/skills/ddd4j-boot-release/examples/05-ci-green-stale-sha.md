# Example 5 — CI green on a stale SHA

## Prompt

> All CI jobs are green, we pushed the release tag, and consumers immediately report resolution failures on one line. CI was green! Where did this fall apart?

## What the skill should do

1. Reconstruct the evidence chain per line: CI run SHA versus release SHA, deploy record, and consumption evidence — one of them is disconnected.
2. Identify the classic break: CI went green on the pre-tag commit, and commits merged between the run and the tag were never built by CI at all.
3. Check the deploy record for the affected line: a failed or partial deploy with a zero exit can masquerade as published until a cold consumer resolves it.
4. Prescribe the repair: re-run CI pinned to the release SHA, redeploy if the artifacts differ, and re-prove with clean-cache consumption before re-announcing.
5. Add the gate that prevents a repeat: CI must be terminal-success for the exact release SHA before deploy is allowed to start.

## Expected output

```
Incident: consumers report resolution failure on 3.0.x; CI green.

Evidence chain (3.0.x):
  CI run:        green, SHA abc1234
  release SHA:   def5678 (two commits later — never CI-built)  ← break
  deploy record: partial — parent + 9 of 12 modules
  consumption:   none (was skipped as "CI covered it")

Repair:
  1. CI re-run pinned to def5678
  2. redeploy after green; verify metadata completeness
  3. clean-cache (-U) consumption proof
  4. gate added: deploy starts only after terminal CI success on the
     exact release SHA

Evidence: per-line chain audit; repair TEST RUN pending.
```

## Failure the skill must avoid

Re-running the deploy alone and re-announcing. The un-CI-built commits still have no evidence, and the partial deploy's root cause stays unknown — the same failure returns on the next line.
