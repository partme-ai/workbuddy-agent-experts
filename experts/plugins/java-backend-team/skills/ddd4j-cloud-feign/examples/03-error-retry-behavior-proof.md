# Example 3 — Proving error decoder and retry behavior

## Prompt

> Before the release, prove our Feign error and retry handling actually behaves: failing downstream, timeouts, the works. We need evidence, not assurances.

## What the skill should do

1. Run real round-trips against a deliberately failing downstream — controlled fault injection, not mocks.
2. Verify each remote error class maps through the error decoder factory to the stable contract on the caller side.
3. Verify retry counts and backoff on idempotent endpoints, and that non-idempotent endpoints do not retry.
4. Assert cleanup after every terminal state: after error responses, after timeouts, and between retry attempts.
5. Grade the evidence per tier and state what was not exercised.

## Expected output

```
Fault-injection round-trip matrix:
  500 from downstream → stable contract exception   PASS
  404 / 409           → mapped per contract         PASS
  timeout             → contract exception + caller cleanup PASS
  retry (GET)         → 2 attempts, backoff observed      PASS
  retry (POST)        → NO retry (non-idempotent)         PASS
  cleanup between attempts                    → PASS

Evidence: TEST (real round-trips). Remaining: circuit-breaker integration
NOT RUN — out of this matrix.
```

## Failure the skill must avoid

Declaring error handling proven because one 500 produced a nice exception once. The matrix must include timeout and the between-attempts cleanup — those are the terminal states where header residue and half-cleared context actually bite.
