# Example 3 — Challenging claimed release evidence

## Prompt

> Verify mode: the team says the 7.1.x release is done — pushed, CI green, published to the private repo. Don't publish anything yourself, just tell me if the evidence actually holds.

## What the skill should do

1. Stay in verification mode: challenge each claimed tier without pushing or publishing.
2. Check the chain separately — local HEAD vs tracking ref vs remote ref; CI runs for the exact pushed SHA with terminal required-job conclusions; deploy inventory and remote metadata; isolated empty-cache consumption.
3. Distinguish activity from acceptance: a push event, a started workflow, and deploy upload lines are each insufficient for their tier.
4. Report per-tier states (PASS/FAIL/BLOCKED/SKIPPED/NOT RUN) and name the exact missing evidence.

## Expected output

```
Claim: 7.1.x release complete.

| Tier            | Claimed | Verified                                    | State |
|-----------------|---------|---------------------------------------------|-------|
| Remote SHA      | pushed  | local HEAD = tracking = remote (SHA 9f2c1a) | PASS  |
| CI              | green   | run 8844: required job "verify" still running | NOT COMPLETE |
| Deploy          | done    | 14/14 modules uploaded, metadata build #31  | PASS  |
| Consumption     | implied | empty-cache proof never run                 | NOT RUN |

Verdict: release NOT complete. CI not terminal; consumption proof missing.
Local publication plus blocked CI would still not close the CI tier.
```

## Failure the skill must avoid

Rubber-stamping "release done" because the push succeeded and a deploy log shows uploads. Two of the four tiers are unproven — and the CI tier is the one currently running, which is precisely the activity-as-acceptance trap.
