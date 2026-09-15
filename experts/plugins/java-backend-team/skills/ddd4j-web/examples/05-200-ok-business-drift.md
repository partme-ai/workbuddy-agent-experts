# Example 5 — Diagnosing "everything returns 200" error drift

## Prompt

> Our team's service returns HTTP 200 with a JSON body like `{"success": false, "code": "ORDER_EXPIRED"}` on business failures, and the monitoring we just built counts everything as healthy. Other ddd4j services return real 4xx/5xx. Whose bug is it, and what does the contract actually require?

## What the skill should do

1. Rule: HTTP 200 is not proof of business correctness — the ddd4j contract maps failure classes to stable statuses (400, 401, 403, 404, 409, 415, 422, 429, 500) with a unified payload, so status-family monitoring and per-service behavior align.
2. Compare against the contract: `ORDER_EXPIRED` on a submitted order is a 409-class conflict; expired sessions are 401-class; validation failures 400/422 — not 200s with a flag.
3. Explain the concrete damage: status-family dashboards, rate limiting, retry logic at gateways, and the orchestrator all read status codes — a 200-only service is invisible to all of them.
4. Locate where the drift enters: a custom `success` flag protocol ported from a legacy framework, diverging per developer — check the adapter's exception translator and the unified payload.
5. Give the remediation: translate business exceptions through the adapter's exception mapping, run the `web-testkit` error-mapping cases, and align monitoring to status families.

## Expected output

```
Verdict: the 200-on-failure service violates the ddd4j HTTP contract.

Contract mapping (SOURCE, web-core contract + adapter):
  ORDER_EXPIRED (submit against expired order) → 409 Conflict class
  session/token problems                       → 401
  payload validation failures                  → 400/422
  downstream system errors                     → 500, cause preserved
                                                 internally, no stack trace out

Damage: status-family monitoring reads the service as 100% healthy; gateway
retries and rate limits never engage; cross-service dashboards mislead.

Remediation: route business exceptions through the adapter's exception
translator; re-run web-testkit error cases; alerting switches to status
families. Status: testkit re-run NOT RUN.
```

## Failure the skill must avoid

Declaring both styles "fine, just different conventions." The 200-only protocol is why the monitoring lied — tolerating it defeats the cross-runtime consistency the web contract exists to provide.
