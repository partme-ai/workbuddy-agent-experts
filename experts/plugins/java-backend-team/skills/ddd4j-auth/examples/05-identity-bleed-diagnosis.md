# Example 5 — Diagnosing identity bleed between requests

## Prompt

> Since we switched to Shiro, users intermittently see each other's profile data — maybe once every few thousand requests. Login and logout both work fine when I test by hand. Where do I even look?

## What the skill should do

1. Recognize the signature: intermittent cross-user data at low rate + hand-testing clean = identity residue on pooled threads, not a login bug.
2. Trace the Subject lifecycle: authenticated at entry → Provider builds `Subject` → bound to thread/request scope → must be restored at every terminal state.
3. Hunt for the residue: a bind without a matching restore on the exception path, an async handoff that skips restore, or logout that clears the framework session but not the bound ddd4j Subject.
4. Provide the decisive test: replay request A (user 1, forced exception), then request B (anonymous) on the same worker thread and assert B gets 401, not user 1's data.
5. Prescribe the fix: restore in a scope/`finally` covering success, exception, and async completion.

## Expected output

```
Diagnosis: intermittent identity bleed = Subject residue on pooled threads.
Evidence trail:
  - Login/logout flows PASS in isolation (reproduces nothing)
  - Bind site: ShiroSubjectProvider wrapper binds Subject per request (SOURCE)
  - Restore site: present after success only — exception path skips it ← defect

Leak scenario: request A (user 1) throws → restore skipped → thread returns
to pool carrying Subject(user 1) → request B hits the same thread and reads
user 1's profile.

Fix: wrap bind in a scope whose close runs in `finally`, covering exception
and async completion. Verify with the anonymous-after-exception thread-reuse
test. Evidence: SOURCE; reproduction test NOT RUN.
```

## Failure the skill must avoid

Telling the user to "check the Shiro session config" or re-test login. Login works; the defect lives in the request-end cleanup on the exception path — the one path hand-testing never exercises.
