# Example 2 — Read-only controller and readiness review

## Prompt

> Review our web layer read-only before the audit: error contract, context binding, auth, readiness probes. Tell me what an auditor would flag.

## What the skill should do

1. Stay read-only — inspect controllers, error handlers, filters, and probe configuration.
2. Check every error path returns the unified contract — no stack traces, no provider-specific bodies.
3. Verify context/tenant binding at request start has matching cleanup, and that async handlers capture locale and context before the handoff.
4. Verify auth flows through `SubjectProvider` rather than ad-hoc header reads.
5. Inspect readiness vs liveness: readiness must aggregate real dependencies and neither probe may be hardcoded.

## Expected output

| Area | Finding | Severity |
|---|---|---|
| Error contract | `/upload` returns raw `BindException` trace on bad input | HIGH |
| Readiness | `/ready` returns hardcoded UP; liveness wired to DB ping | HIGH |
| Auth | two controllers read `X-User` header directly | MEDIUM |
| i18n | error messages not localized (default locale only) | LOW |

Evidence: SOURCE only. Probe behavior per dependency state NOT RUN — the readiness finding requires a live probe test to confirm impact.

## Failure the skill must avoid

Passing the web layer because endpoints return 200 on the happy path. The audit-relevant defects — the escaped stack trace and the hardcoded READY — live entirely in the error and probe paths that a happy-path smoke test never touches.
