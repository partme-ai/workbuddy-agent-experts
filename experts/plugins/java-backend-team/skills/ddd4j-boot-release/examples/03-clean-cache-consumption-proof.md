# Example 3 — Clean-cache consumption proof

## Prompt

> The deploy job finished successfully, artifacts show up in the repository UI, and we built the consumer locally. Can we mark the line CONSUMED?

## What the skill should do

1. Decline the shortcut: a repository UI listing and a local build with a warm cache both fail to prove remote resolution — the local build may have resolved every artifact from disk.
2. Require the isolated clean-cache consumption: an empty Maven cache with `-U`, resolving exactly the coordinates consumers use.
3. Verify remote metadata completeness during the run — an incomplete deploy can satisfy a warm cache and fail a cold one.
4. Record the result per line as CONSUMED only after the cold resolution succeeds.
5. Redact any repository URLs or credentials from the output.

## Expected output

```
Claim: line 3.5.x is CONSUMED.

Evidence check:
  deploy job exit 0                    REACHED (necessary, not sufficient)
  repository UI shows artifacts        NOT EVIDENCE — visibility ≠ resolvability
  local consumer build                 NOT EVIDENCE — warm cache

Cold consumption run (isolated empty cache, -U):
  parent + BOM + all modules resolve   PASS
  remote metadata complete             PASS

Verdict: CONSUMED — evidence level reached properly.
```

## Failure the skill must avoid

Marking CONSUMED because the deploy job was green. The deploy can succeed while publishing incomplete metadata, and the first cold-cache consumer in another team discovers it — after the release announcement.
