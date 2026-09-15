# Example 3 — Proving CAS contention across two instances

## Prompt

> Before we sign off the idempotency design, prove the shared CAS actually holds under contention. Two instances, same key, at the same moment. What test do we run and what does evidence look like?

## What the skill should do

1. Fix the line and read the cache module's CAS contract — acquire, hold, TTL re-acquisition — so the test asserts the real semantics, not a simplification.
2. Design the contention test against the real shared backend (not a local fake): two instances acquire the same key concurrently with a slow business handler; exactly one wins, the loser must CAS-retry and then replay.
3. Cover the TTL edge: hold time exceeding the lock TTL forces re-acquisition — the loser path and the duplicate-prevention path both need assertions.
4. Run it, record per-case evidence states, and mark anything skipped explicitly.

## Expected output

```
Evidence: shared CAS contention on 7.1.x (SHA abc123, real backend)

| Case                                   | Expected                  | Actual          | State |
|----------------------------------------|---------------------------|-----------------|-------|
| Two instances, same key, concurrent    | 1 winner, 1 CAS-retry     | 1 winner        | PASS  |
| Loser after winner commits             | replay stored response    | replay          | PASS  |
| Handler exceeds lock TTL               | TTL re-acquisition path   | re-acquired     | PASS  |
| Winner crashes before storing response | lock expires, retry wins  | lock expired    | PASS  |
| Backend partitioned during test        | fail closed, no effect    | SKIPPED — chaos tooling absent |

Caveat: local single-instance contention tests are NOT evidence for this claim;
every PASS above ran against the shared backend with two instances.
```

## Failure the skill must avoid

Running the "contention" test inside one JVM against an in-memory map and reporting green. Without a second instance and the real backend, the test cannot lose a lock, expire a TTL, or split-brain — which are exactly the failure modes being certified away.
