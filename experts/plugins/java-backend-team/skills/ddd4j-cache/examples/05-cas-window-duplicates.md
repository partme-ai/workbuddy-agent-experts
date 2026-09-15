# Example 5 — Diagnosing duplicates despite an "atomic" guard

## Prompt

> We use Redis for idempotency and we still got a duplicate submission last night. The code does `if (redis.get(key) == null) { process(); redis.set(key, ...) }`. It's Redis, it's atomic, so how did this happen?

## What the skill should do

1. Diagnose the real defect: `get`-then-`set` is two round-trips, not one atomic operation — the check-then-act window between them is the race.
2. Explain the exact interleaving: two requests read null on different connections, both pass the check, both process.
3. Show the ddd4j-correct path: the `CasCache`/`AtomicCache` contracts put the compare-and-set in one server-side operation, so the winner is decided atomically.
4. Note the secondary hazards while fixing: TTL must cover the retry window, and the failure path must fail closed.
5. Demand the two-client contention test as proof of the fix.

## Expected output

```
Defect: check-then-act window in get→process→set.

Interleaving that produced the duplicate:
  t1: req A  GET key → null
  t2: req B  GET key → null      (A still processing, nothing set)
  t3: req A  process + SET key
  t4: req B  process + SET key   ← second charge

"Redis is atomic" is per-command, not per-sequence.

Fix: replace the sequence with a single CasCache/AtomicCache operation so
claim-and-set is one server-side step; set TTL to cover the retry window;
fail closed when Redis errors.

Verify: two-client contention test — one winner, one rejected. Status: NOT RUN.
```

## Failure the skill must avoid

Answering "increase the Redis timeout" or "retry the set." The race is in the application's two-step sequence; no amount of connection tuning closes a check-then-act window.
