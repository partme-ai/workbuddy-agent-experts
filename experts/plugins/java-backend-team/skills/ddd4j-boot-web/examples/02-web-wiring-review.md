# Example 2 — Web wiring review (read-only)

## Prompt

> Pen-test findings are due and they'll hammer the web layer. Read-only check of our boot web setup first: error shape, CORS, limits, readiness. What would they find?

## What the skill should do

1. Stay read-only; findings with severity, not patches.
2. Fix the line, then read the web AutoConfiguration, Properties, and the assembled MVC/WebFlux configuration.
3. Check the unified error contract actually covers validation and framework errors, and that stack traces do not leak.
4. Check the CORS allowlist source and its fallback behavior when the environment-specific config is missing.
5. Check limits (rate/concurrency), idempotency coverage, and whether readiness aggregates real dependency checks or a constant.

## Expected output

| Check | Finding | Severity |
|---|---|---|
| Web stack | MVC + WebFlux starters both present; MVC silently serves | High |
| Error contract | domain errors mapped; validation errors return raw 400 with field dump | High |
| Stack traces | `server.error.include-stacktrace` default leaks traces on this line | High |
| CORS | allowlist falls back to `*` when the env config key is absent | Critical |
| Limits | concurrency limit configured; no evidence it is enforced on async paths | Unverified |
| Readiness | aggregates DB + MQ checks correctly | OK |

Evidence: SOURCE read on line <L>. No HTTP tests executed — read-only review.

## Failure the skill must avoid

Reviewing only the controllers. The findings a pen-test actually surfaces — CORS fallback, trace leakage, validation bypassing the error contract — all live in configuration defaults and handler registration order.
