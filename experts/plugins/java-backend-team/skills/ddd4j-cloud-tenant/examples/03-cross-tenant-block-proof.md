# Example 3 — Proving cross-tenant reads are blocked

## Prompt

> Compliance wants evidence that tenant A can never read tenant B's orders, including through our Feign calls to the billing service. Produce it.

## What the skill should do

1. Run the isolation tests against a real database — a mocked `TenantContextHolder` proves nothing here.
2. Probe both layers: SQL filtering on the order tables in this service, and tenant headers on the Feign call to billing (verified from billing's side too).
3. Cover the hostile path: forge a tenant header without a matching token claim and confirm it is rejected, not trusted.
4. Exercise the non-happy terminals: exception mid-query, async execution, and Feign retry — isolation must hold on each.
5. Grade the evidence per tier and mark anything unexercised as NOT VERIFIED.

## Expected output

```
Isolation evidence (real MySQL, real services):
  tenant A reads B's orders (direct)      → BLOCKED  PASS
  tenant A reads B's orders (via Feign)   → BLOCKED  PASS (billing side asserted)
  forged tenant header, no token match    → REJECTED PASS
  exception mid-query → tenant restored   → PASS
  async + retry paths                     → NOT RUN  (marked)

Verdict: isolation proven on tested paths; async/retry tier NOT VERIFIED.
```

## Failure the skill must avoid

Handing compliance a green unit-test suite that mocked the holder. The evidence that satisfies this request is behavioral — real database, forged-header attempt, and the receiving service's side of the Feign call.
