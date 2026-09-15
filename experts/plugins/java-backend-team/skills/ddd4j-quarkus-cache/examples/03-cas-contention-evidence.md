# Example 3 — Evidence request: prove CAS is actually atomic

## Prompt

> The team claims their cache implementation gives us CAS semantics. Before we build idempotency on it, I want proof — what evidence should exist?

## What the skill should do

1. Define what CAS proof requires: a test where two contenders race the same key and exactly one wins, plus a multi-instance test showing the winner is visible to the other instance.
2. Inspect the implementation: does the put-if-absent path use an atomic backend operation (Redis SETNX/ Lua) or a check-then-set pair that races?
3. Look for the existing contention test in the cache module's QuarkusTest suite and its last run on the current line.
4. Separate the tiers: unit-level contention (one JVM) versus cross-instance CAS (needs the real shared backend).
5. Report evidence status honestly — absent tests are gaps, not assumptions of correctness.

## Expected output

```
CAS evidence review — Cache SPI implementation X:

  Atomic backend op: YES — putIfAbsent maps to a single Redis Lua script (line NN).
  Contention test (one JVM, N threads): EXISTS — last run PASS on line 4.0.x.
  Cross-instance CAS test (two clients, shared backend): ABSENT.

Verdict: single-JVM atomicity is evidenced; cross-instance CAS is claimed but
UNPROVEN. Idempotency built on this implementation should wait for (or add) the
two-client contention test.
Missing: two-client test run; how to provide: QuarkusTest with two cache client
instances against the shared Redis backend.
```

## Failure the skill must avoid

Accepting "it's Redis, so it's atomic" — atomicity belongs to the specific operation mapping, and a check-then-set implemented in Java code breaks under contention even on Redis.
