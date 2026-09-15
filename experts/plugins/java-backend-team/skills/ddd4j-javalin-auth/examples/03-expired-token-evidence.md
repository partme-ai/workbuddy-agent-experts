# Example 3 — Proving the expired-token path returns 401

## Prompt

> Before the pen test, give me evidence that an expired JWT actually gets a 401 on our 7.2.x service — not just that the filter class exists.

## What the skill should do

1. Fix the line (7.2.x → Javalin 7.2/ddd4j 3/JDK 21/Maven 4) and locate the access-manager/registration site for the protected routes.
2. Trace what actually runs for `/api/*` requests: which `SubjectProvider` validates the token and which exception maps to 401.
3. Execute the evidence: obtain a real (or Testcontainers Keycloak) token, expire it, send the request, and record status, body shape, and absence of token leakage in logs.
4. Report per-path evidence: valid token, expired token, missing token, wrong issuer — with PASS/FAIL/NOT RUN per case.

## Expected output

```
Evidence: expired-token handling on 7.2.x (SHA abc123)

| Case                | Expected | Actual | State |
|---------------------|----------|--------|-------|
| Valid token         | 200      | 200    | PASS (executed) |
| Expired token       | 401      | 200    | FAIL  |
| Missing token       | 401      | 401    | PASS (executed) |

Expired-token FAIL root cause: clock-skew tolerance configured as 86400s
(oidc.properties line NN) — effectively never expires.
Fix: set tolerance ≤ 60s, re-run the suite, then re-run the wrong-issuer case.

Log check: no token value in response or logs for any case. PASS.
```

## Failure the skill must avoid

Reporting "expired tokens are rejected, the JWT validator is registered" from source reading alone. The class existing proves nothing — the executed request is the evidence, and here it found a tolerance misconfiguration a smoke test would have blessed.
