# Example 3 — Transaction and Outbox behavior proof

## Prompt

> Our Outbox pattern is supposed to publish the integration event only if the aggregate save commits. Prove that guarantee actually holds before we trust it in production.

## What the skill should do

1. Fix the line and read how the boot data module assembles the Outbox with the transaction manager (same datasource, same transaction boundary).
2. Write the two decisive behavior tests: save + publish under commit, and save + publish under a forced rollback.
3. Assert the commit case: aggregate row and Outbox row appear together.
4. Assert the rollback case: neither row appears — the Outbox entry must not survive the failed transaction.
5. Run against a real database (not an in-memory double) and report the evidence layers separately.

## Expected output

```
Outbox atomicity proof (line 3.x, real PostgreSQL):

  Test 1 — committed save:
    aggregate row present       PASS
    outbox row present          PASS

  Test 2 — forced rollback after outbox write:
    aggregate row absent        PASS
    outbox row absent           PASS   ← atomic with the transaction

Conclusion: dispatch is gated by the same transaction; a failed save
cannot leave a publishable event behind.

Evidence: behavior TEST RUN (real DB). CI: NOT RUN for this SHA.
```

## Failure the skill must avoid

Proving it with an in-memory fake that "saves" to a list. The fake commits unconditionally, so the rollback test passes trivially and proves nothing about the actual transaction boundary.
