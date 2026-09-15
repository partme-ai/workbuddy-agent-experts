# Example 3 — CAS and TTL proof against a real backend

## Prompt

> Our documentation claims "atomic set-if-absent with configurable TTL" for the cache the boot module assembles. Verify that claim is actually true before we publish it.

## What the skill should do

1. Fix the line and read how the assembled implementation performs set-if-absent (CAS) and TTL — from source, on that line.
2. Design the contention test: N concurrent writers on the same key against a real Redis, asserting exactly one success.
3. Design the TTL test: write, wait past the configured bound, assert expiry — and confirm the unit used (seconds vs milliseconds) from the line's Properties.
4. Also cover invalidate and re-set behavior, since claims usually bundle all three.
5. Report each sub-claim separately with pass/fail; do not let one green test bless the whole sentence.

## Expected output

```
Claim: "atomic set-if-absent with configurable TTL"

  CAS contention (real Redis, 64 threads, same key):
    exactly one writer succeeded            PASS
  TTL semantics:
    configured 5000 (Properties unit: milliseconds)
    key expired at ~5.0s                    PASS
    unit misread as seconds → would expire at 5000s: rule out by test  PASS
  invalidate + re-set:
    invalidate removes; next CAS succeeds   PASS

Verdict: the claim holds as worded, on line <L>, against real Redis.
Evidence: behavior TEST RUN. CI for the test suite: NOT RUN.
```

## Failure the skill must avoid

Testing CAS with a single thread and calling it atomic. Atomicity is a contention property — a single-threaded pass proves nothing, and a fake backend proves even less.
