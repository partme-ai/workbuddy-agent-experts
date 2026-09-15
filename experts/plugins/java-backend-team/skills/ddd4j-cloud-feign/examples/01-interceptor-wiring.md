# Example 1 — Wiring interceptors for service-to-service calls

## Prompt

> Our order service calls the inventory service over Feign. The inventory side needs the caller's user context and tenant headers. Set up the plumbing.

## What the skill should do

1. Fix the combination with `ddd4j-cloud-version-selection`, then use the line's Feign extension mechanisms rather than a hand-rolled `Client`.
2. Register request interceptors that capture context and tenant before the call and clear them after — per attempt, since retries re-enter.
3. Define the header allowlist: exactly the headers inventory needs; never forward Authorization or cookies onward.
4. Install the error decoder factory so inventory's errors arrive as the stable contract, not raw HTTP internals.
5. Specify the verification: a real round-trip covering success, error response, timeout, and one retry.

## Expected output

```
Interceptor inventory:
  ContextPropagationInterceptor — captures Subject/trace before call,
    clears after (attempt-safe)
  TenantHeaderInterceptor — tenant from TenantContextHolder, allowlisted

Header allowlist: [X-Tenant-Id, X-Trace-Id, <context headers>]
Excluded: Authorization, Cookie, anything not on the list

Error decoder: remote errors → stable contract exception family
Tests: real round-trip matrix (success/error/timeout/retry) — pending run.
```

## Failure the skill must avoid

Solving it by passing the tenant as a plain method parameter and letting the header stay empty "for now" — inventory then enforces tenant rules against a missing or default tenant, which is both a correctness bug and an isolation hole.
