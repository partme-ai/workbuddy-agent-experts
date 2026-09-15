# Example 3 — Delivery behavior proof with Testcontainers

## Prompt

> We claim our MQ integration handles retries, duplicates, and broker restarts. Give us real evidence for that sentence, not just a context that starts.

## What the skill should do

1. Fix the line and read the assembled ack/retry/dead-letter semantics from the adapter source first, so the tests target the actual contract.
2. Spin up the real broker via Testcontainers and run the full round-trip suite: publish/consume, ack, nack/retry, duplicates, recovery, shutdown.
3. Assert each behavior separately — a passing "messages flow" test proves none of the failure semantics.
4. If Docker is unavailable in the environment, record the suite as BLOCKED/SKIPPED explicitly rather than reporting green.
5. Report configuration presence, bean creation, and behavior as separate layers; attach CI status for the suite.

## Expected output

```
Claim: "retries, duplicates, and broker restarts handled"

Evidence (Testcontainers, line 3.x adapter):
  publish/consume                PASS
  ack on success                 PASS
  nack → retry N times           PASS (bounded, as configured)
  duplicate delivery observed    PASS (consumer dedupe verified)
  broker container restart →
    consumer recovers, no loss   PASS
  graceful shutdown mid-flight   PASS
  Docker available: yes          (otherwise: suite BLOCKED, claim unproven)

Evidence: behavior TEST RUN. CI for the suite: NOT RUN.
```

## Failure the skill must avoid

Reporting the claim verified from a context-start test plus a mocked broker. None of the three claimed behaviors — retry, duplicates, restarts — exist in that setup; the claim would be untested in production terms.
