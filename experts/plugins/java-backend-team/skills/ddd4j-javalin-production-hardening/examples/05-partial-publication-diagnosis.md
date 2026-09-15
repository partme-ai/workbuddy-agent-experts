# Example 5 — Partial publication that everyone called a success

## Prompt

> Last night's release script said "published" for all three branches. Today the consumer build for 7.2.x fails with a 404 on one module. The script exited zero. What actually happened?

## What the skill should do

1. Classify the evidence honestly: exit zero and upload lines are activity, not completion — check the RFC9457 404 body and `target/resume.properties` to identify the failed module and the remote state.
2. Verify the inventory: compare the expected 14-module coordinate list against what the private remote actually serves for 7.2.x, per the serial-publication rule (stop at first partial failure — the other branches' state must be checked, not assumed).
3. Recover explicitly: resume/re-deploy only the failed module with the repository-supported retry, then revalidate the complete inventory.
4. Close the gate: run the isolated empty-cache consumption proof; only that turns "published" into a terminal PASS for the release status table.

## Expected output

```
Release status: 7.2.x publish = PARTIAL (was reported as success).

Evidence:
  - Script exit 0, 14 upload lines .................. producer activity only
  - Consumer 404: ddd4j-javalin-cache metadata ...... RFC9457, first-publish
    metadata never finalized for that module
  - target/resume.properties: records cache module incomplete
  - Remote inventory: 13/14 resolvable

Recovery: resume publish for ddd4j-javalin-cache (-r), confirm metadata build
increment, revalidate 14/14, then empty-cache consumption proof (-U).

| Branch   | Deploy      | Empty-cache consume |
|----------|-------------|---------------------|
| 6.7.x    | PASS        | PASS                |
| 7.1.x    | PASS        | NOT RUN — must verify, not assume |
| 7.2.x    | PARTIAL → resume | pending re-proof |

Family release: NOT green while 7.2.x is partial and 7.1.x consumption is unproven.
```

## Failure the skill must avoid

Accepting the script's exit zero and re-running the consumer "until the repo syncs". A Maven 4 first-publish metadata failure does not heal by retrying the consumer — the partial module must be resumed, revalidated, and re-proven from an empty cache.
