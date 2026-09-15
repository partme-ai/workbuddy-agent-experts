# Example 5 — One user's Subject on another user's request

## Prompt

> Under load we intermittently see user A's identity in user B's response. It never happens in single-user testing. Where do we look?

## What the skill should do

1. Explain why single-user testing can't catch it: the defect needs two requests served by the same pooled thread.
2. Trace every `ThreadContext` bind site to its release site, and check the three exit paths independently: success, exception, async completion.
3. Look for the classic shape: release only on the success path, so a thrown exception leaves Subject A bound when the thread returns to the pool.
4. Check the async and Feign terminal states too — each hop that captures without a matching clear leaks across requests.
5. Fix with a scope that releases in a `finally` (or equivalent terminal-state hook) covering all paths, then reproduce under concurrency.

## Expected output

```
Bind sites:  HTTP entry filter (Subject + tenant)  — 1 site
Release sites: same filter, success path only      ← defect

Leak scenario: request A throws → release skipped → thread returns to pool
with Subject A bound → request B on that thread inherits Subject A.

Why load-only: requires thread reuse after a failed request; single-user
testing never reuses a poisoned thread.

Fix: release inside a finally/terminal-state hook on all three exit paths;
add an async-completion release for handoffs.
Evidence: SOURCE read; concurrent reproduction test NOT RUN — flagged.
```

## Failure the skill must avoid

Answering "call clear at the end of the request". The end of the happy path is precisely where the code already clears; the leak is the exception path (and async terminal states), which a trailing clear never reaches.
