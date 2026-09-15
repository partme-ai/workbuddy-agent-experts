# Example 2 — Read-only CI evidence audit for the three lines

## Prompt

> A contractor claims all three Javalin branches are "released". Before I sign the acceptance doc, read-only check: is the CI evidence actually there for 6.7.x, 7.1.x, and 7.2.x?

## What the skill should do

1. Stay read-only; challenge claims with evidence, do not push or publish.
2. For each line, resolve the CI runs for the exact final SHA — not "a recent green run on the branch" — and check required-job conclusions reached terminal states.
3. Distinguish the failure shapes: queued/in-progress (`NOT COMPLETE`), billing-blocked (`BLOCKED (infrastructure)`), step failure (`FAIL`), waived security (`SKIPPED`).
4. Report per line whether the claim holds, with run links/IDs and the exact gap where it does not.

## Expected output

```
Acceptance check: "all three lines released"

| Line    | Claimed | CI for final SHA                          | Verdict      |
|---------|---------|-------------------------------------------|--------------|
| 6.7.x   | released| run 8812, all required jobs success       | SUPPORTED    |
| 7.1.x   | released| run 8815 in progress (deploy job)         | NOT COMPLETE |
| 7.2.x   | released| run 8817 — security job waived by actor   | SKIPPED risk retained, not PASS |

Note: no evidence of empty-cache consumption attached for any line;
the claim "released" is unproven for that tier on all three.
```

## Failure the skill must avoid

Signing the acceptance because each branch shows *some* green run in its history. The gate is terminal required-job success for the exact release SHA — a green run from an earlier commit proves nothing about this one.
