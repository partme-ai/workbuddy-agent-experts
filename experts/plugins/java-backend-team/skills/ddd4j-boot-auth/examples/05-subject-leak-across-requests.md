# Example 5 — Subject leaking across requests

## Prompt

> Users occasionally see another user's profile after a request errors out. It's rare, only under load, and we can't reproduce it with single requests. Where do we look?

## What the skill should do

1. Recognize the signature: intermittent cross-user data under load equals per-request state surviving thread reuse — start at the auth request cleanup, not at the business code.
2. Trace the Subject/token bind site and its release; check the three exit paths independently: success, exception, and async completion.
3. Identify the classic defect: cleanup registered only on the success path, so any thrown exception skips it and the pooled thread keeps the previous Subject.
4. Confirm the auth filter/interceptor order — an error thrown before the cleanup filter runs escapes it entirely.
5. Prescribe the fix (release in a finally-scoped wrapper covering all exit paths) and re-run the thread-reuse case under a mixed success/failure load.

## Expected output

```
Bind site:  AuthFilter.bindSubject(...) — binds Subject per request
Release:    AuthFilter cleanup runs after chain.doFilter returns normally
            ← exception thrown by the controller skips the release

Reproduction: mixed load with ~N% failing requests reproduces the
"wrong user" response; single-request tests never do, matching the report.

Fix: move the release into a finally-scoped wrapper (or scoped context)
that executes on success, exception, and async completion alike.

Verification: thread-reuse test under mixed success/failure load PASS.
Evidence: SOURCE + behavior TEST RUN.
```

## Failure the skill must avoid

Answering "add a logout call in the error handler" or blaming the cache. The leak lives in the bind/release pairing of the auth filter, and only the exception path under thread reuse exposes it — exactly where intuition says not to look.
