# Example 3 — Full auth behavior matrix run

## Prompt

> We're about to sign off the login flow. Run through every auth case we should have evidence for — don't just check that login works.

## What the skill should do

1. Enumerate the required behavior matrix from the skill's workflow: anonymous, valid credentials, expired token, insufficient role, logout, and thread reuse.
2. Fix the line and confirm the wiring evidence (configuration present, beans created) before behavioral claims.
3. Execute each case and record pass/fail with the observed status code and resulting Subject state.
4. For thread reuse, assert that after a request completes — including a failing one — no Subject or token remains bound to the pooled thread.
5. Report each evidence layer separately and mark anything not executed as NOT RUN or BLOCKED.

## Expected output

```
Auth behavior matrix (line 3.x):
  anonymous request      → 401, no Subject created            PASS
  valid credentials      → 200, Subject bound to request      PASS
  expired token          → 401 (mapped, not 500)              PASS
  insufficient role      → 403 (mapped, not 500)              PASS
  logout                 → token invalidated, next call 401   PASS
  thread reuse           → after failed request, pooled thread
                           carries no Subject                 FAIL ← cleanup
                                                             missing on the
                                                             exception path

Sign-off: DECLINED until the exception-path cleanup is fixed and re-run.
Evidence: TEST RUN (5/6). CI for the fix: NOT RUN.
```

## Failure the skill must avoid

Declaring sign-off from "login works". The expired-token case mapping to 500 and the exception-path cleanup leak are precisely the failures a login-only check misses, and both are security findings.
