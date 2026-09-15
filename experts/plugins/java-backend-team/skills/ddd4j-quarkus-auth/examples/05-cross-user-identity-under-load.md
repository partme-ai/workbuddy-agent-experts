# Example 5 — User B sees user A's identity under load

## Prompt

> Under load testing, roughly one in a few thousand responses comes back with the wrong user's profile. Individually we can't reproduce it. Where do we look?

## What the skill should do

1. Pattern-match the symptom: intermittent cross-user identity under concurrency means a Subject/context leak on a pooled worker thread, not a token validation bug.
2. Trace every Subject bind site and its release; check the three exit paths independently — success, exception, async completion.
3. Expect the classic defect: release only on the success path, so a thrown exception leaves the previous request's Subject bound when the thread returns to the pool.
4. Check auth filters specifically: a filter that binds the Subject but returns early on error (before release) is the usual culprit.
5. Recommend the fix (scope/`finally` covering all paths) and the load-level test that reproduces it.

## Expected output

```
Bind sites: AuthFilter.java line NN — binds Subject + Tenant per request.
Release sites: AuthFilter.java line NN — release on success only  ← defect

Leak scenario: request A throws in the controller → release skipped → thread
returns to the pool with Subject A bound → request B on the same thread resolves
Subject A. Matches the 1-in-N rate: only error-path collisions leak.

Fix: release in a finally-style path covering success, exception, and async
completion; add a test that throws mid-request under concurrency.
Evidence: SOURCE read. Load reproduction NOT RUN — flagged as remaining gap.
```

## Failure the skill must avoid

Answering "clear the context at the end of the request" — a success-path clear that misses the exception path, which is exactly where this leak lives. The fix must cover all three exit paths.
