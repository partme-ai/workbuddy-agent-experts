# Example 3 — Evidence request: expired and insufficient-role paths

## Prompt

> An auditor wants proof that expired tokens are rejected and that role checks actually enforce. What can you show me?

## What the skill should do

1. Treat it as an evidence request and separate tiers: which tests exist, which ran, which were skipped.
2. Enumerate the required auth test paths: anonymous, valid, expired, insufficient-role.
3. Check the QuarkusTest suites in the current checkout for those cases and read their latest CI result for the audited SHA.
4. Report honestly: a missing expired-token test is a gap, not a pass — Security SKIPPED is a risk, never PASS.
5. List exactly how to close each gap (run the suite, add the missing case).

## Expected output

```
Auth evidence — SHA abc1234, line 3.3.x:

  anonymous request → 401        TEST: RUN (QuarkusTest AuthAnonymousTest) — PASS
  valid token + role → 200       TEST: RUN (AuthValidTest) — PASS
  expired token → 401            TEST: ABSENT — no suite asserts expiry
  valid token, no role → 403     TEST: RUN (AuthForbiddenTest) — PASS

Gap: expired-token path is untested; auditor requirement unmet.
How to close: add an expired-token case (token with `exp` in the past) to the
auth QuarkusTest suite and run CI on the audit SHA.
Status: TEST partial — the missing case blocks the audit sign-off.
```

## Failure the skill must avoid

Telling the auditor "expiry is handled" because the token parser has an expiry check in code. Source presence is not behavior evidence — only a run test on the audited SHA counts.
