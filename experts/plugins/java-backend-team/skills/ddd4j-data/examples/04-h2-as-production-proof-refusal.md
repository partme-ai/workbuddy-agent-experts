# Example 4 — Boundary: H2 suite claimed as production proof

## Prompt

> We need sign-off that the new event store handles concurrent appends. All 240 tests pass on H2 in 40 seconds. Good to ship? Also skip the container stuff — we don't have Docker in this environment.

## What the skill should do

1. Refuse the sign-off: H2 does not emulate the row locking, MVCC visibility, or dialect behavior the concurrency claim depends on — the 40-second suite proves logic, not database behavior.
2. State precisely what remains unproven: `AggregateVersionConflictException` under real contention, transaction visibility across connections, deadlock/retry behavior on the target dialect.
3. Do not soften the refusal into "probably fine" — the claim "handles concurrent appends" is exactly the claim H2 cannot support.
4. Offer paths that do produce evidence: Testcontainers against the real engine in CI, a staging database run, or an explicitly downgraded claim ("logic verified on H2; concurrency unverified").
5. Record the evidence grade honestly: TEST (H2, logic only) — production behavior NOT VERIFIED.

## Expected output

```
Sign-off request: "event store handles concurrent appends"

Provided evidence: TEST (H2, 240 tests PASS) — covers append logic and
conflict mapping, not database concurrency semantics.

Cannot be proven on H2:
  - concurrent append → exactly one AggregateVersionConflictException
    under real row locking
  - cross-connection visibility during the caller's transaction
  - dialect-specific index/lock behavior under contention

Options:
  a) Testcontainers Postgres run in CI (preferred)
  b) Staging database contention run
  c) Ship with the downgraded claim: "logic verified; concurrency
     NOT VERIFIED" — recorded as a known risk.
```

## Failure the skill must avoid

Signing off because the suite is green and fast. A concurrency claim verified only on H2 is unverified — and "no Docker here" makes the gap worse, not smaller.
