# Example 2 — Read-only web layer review

## Prompt

> Before our external launch, do a read-only review of the REST layer: CORS, error bodies, limits, and the readiness probes. Line 3.3.x.

## What the skill should do

1. Stay read-only and fix the line/SHA (3.3.x → Quarkus Platform 3.37.4 / ddd4j 2.0.x / JDK 17 / Maven 3).
2. Inventory endpoints and their status-code/error-body contract; flag raw exception leakage.
3. Check CORS is explicit and minimal, not a permissive wildcard carried over from dev.
4. Check request limits (body size, concurrency) are set for production traffic.
5. Verify liveness and readiness are separate, and readiness aggregates real dependencies.

## Expected output

| Check | Finding | Verdict |
|---|---|---|
| Error bodies | `ConstraintViolationException` handler returns stable 400 | OK |
| Error bodies | unhandled `Exception` returns stack trace with 500 | **VIOLATION** |
| CORS | `*` origin + credentials enabled from dev config | **RISK** |
| Request limits | no body-size limit configured | **GAP** |
| Probes | readiness checks DB + broker; liveness is process-only | OK |

Evidence: SOURCE read of web layer + config. QuarkusTest HTTP suites NOT RUN on this SHA.

## Failure the skill must avoid

Reporting "web layer ready" because the endpoints return 200 in staging. The wildcard CORS plus stack-trace leakage are launch blockers that a happy-path smoke test never exercises.
