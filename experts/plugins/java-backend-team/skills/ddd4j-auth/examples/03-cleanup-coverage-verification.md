# Example 3 — Proving Subject cleanup on every exit path

## Prompt

> Before we go to production: prove to me that after a request finishes — success, error, whatever — no user's identity is left dangling on the worker thread.

## What the skill should do

1. Locate every bind site (filter/interceptor) and its matching restore/close.
2. Verify the three exit paths independently: normal completion, thrown exception, async completion on another thread.
3. Demand behavioral evidence: a test that runs request A (authenticated), forces an exception, then runs request B on the same thread and asserts B sees no inherited identity.
4. Grade the evidence: source-read vs executed test vs load-test observation.
5. Name anything unverified explicitly instead of assuming it.

## Expected output

```
Bind sites:
  - AuthRequestFilter.bind(...) at request entry (SOURCE)
Restore sites:
  - Same filter, finally block → covers success + exception (SOURCE)
  - Async completion callback → MISSING  ← gap

Behavioral test: thread-reuse test exists for the sync exception path (TEST,
PASS). Async path has no test (NOT RUN).

Verdict: sync paths protected; async handoff can leak Subject A into request B.
Missing: async-completion restore + a test; how to provide: add the callback
and run the thread-reuse test against an async endpoint.
```

## Failure the skill must avoid

Answering "cleanup is in a `finally` block, so we're safe." The `finally` covers the synchronous paths only; the async completion path is untested and unprotected, which is exactly the load-test surprise.
