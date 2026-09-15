# Example 5 — "Artifact not found" despite yesterday's successful deploy

## Prompt

> Yesterday's deploy of 4.0.x said SUCCESS, but today a teammate's fresh clone can't resolve the auth extension artifact: "Could not find artifact". Did the deploy get rolled back?

## What the skill should do

1. Read the symptom correctly: a fresh clone failing resolution while local builds succeed is the warm-cache signature — the local repo has the artifact, the remote may not.
2. Re-check yesterday's "SUCCESS" evidence: deploy exit code alone is not success — the 61-module inventory must have been counted per module; a partial deploy exits zero but misses artifacts.
3. Verify against the remote directly: clean-cache (`-U`) resolve of the missing coordinates from the private repository.
4. Compare the deploy-time inventory against the artifact list actually present remotely; the missing entries identify the failed slice of the deploy.
5. Prescribe the recovery: re-deploy (with authorization) and re-consume with `-U` until the inventory matches end to end.

## Expected output

```
Diagnosis: partial deploy, not rollback.
  - Yesterday: exit code 0 reported as SUCCESS, but no module inventory was counted.
  - Remote check: 58/61 artifacts present; missing = auth-extension (runtime+deployment) + bom patch.
  - Fresh clone fails on exactly the missing coordinates; local builds pass on warm cache.

Recovery:
  1. Re-run publish for the missing modules (with explicit authorization).
  2. Count the 61-module inventory post-deploy.
  3. Clean-cache (-U) resolve per module → CONSUMED.

Report correction: yesterday's SUCCESS was PARTIAL; evidence tiers updated.
```

## Failure the skill must avoid

Believing yesterday's "deploy SUCCESS" exit code and blaming the teammate's setup or a rollback. The inventory count — not the exit code — is what defines a complete deploy.
