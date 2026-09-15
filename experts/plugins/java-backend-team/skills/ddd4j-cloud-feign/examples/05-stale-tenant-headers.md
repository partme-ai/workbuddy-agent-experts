# Example 5 — Calls carry the previous request's tenant headers

## Prompt

> Intermittently, inventory receives a Feign call with the wrong tenant header — always a tenant that some earlier request used. Our own service sees the right tenant. What is happening?

## What the skill should do

1. Recognize the signature: wrong tenant only on outbound calls, correct tenant inside the caller — the defect is in the Feign capture/clear cycle, not in the request handling.
2. Trace the interceptor: headers must be captured at call time from `TenantContextHolder` and cleared after the call — a static or per-client cached header value survives across requests on pooled threads.
3. Check the terminal states: a timeout or exception that skips the clear leaves the captured headers bound for the next call from that thread.
4. Check retry behavior: each attempt must re-read the tenant; a capture hoisted before the retry loop freezes the first attempt's headers.
5. Fix attempt-safe capture/clear and add a round-trip regression test that interleaves two tenants through the same client.

## Expected output

```
Finding: TenantHeaderInterceptor caches the header in a client-level
field set on first use — cleared only on success.

Leak path: request A (tenant 7) times out → clear skipped → request B
(tenant 42) reuses the client → outbound call carries tenant 7.

Why caller-side looks right: in-process TenantContextHolder is correct;
the stale value lives only in the outbound header path.

Fix: read tenant at call time per attempt; clear in finally across
success/timeout/error/retry. Evidence: SOURCE; interleaved-tenant
round-trip test NOT RUN — flagged.
```

## Failure the skill must avoid

"Fixing" it by clearing headers at the start of each HTTP request. That cleans the inbound path while the stale value lives in the Feign client state — the interleaved-tenant round-trip is the test that actually catches it.
