# Example 1 — Building an i18n REST endpoint

## Prompt

> Add an order-status endpoint to our ddd4j-cloud MVC service. Error messages and status labels must be internationalized, input must be validated, and auth must come from our subject setup.

## What the skill should do

1. Fix the combination with `ddd4j-cloud-version-selection`, then build on the line's webmvc extension rather than raw Spring MVC configuration.
2. Define the contract: endpoint, status codes, payload, and the unified error response shape.
3. Wire i18n so response messages resolve per request locale, with a defined fallback when no locale matches.
4. Add validation constraints whose failures map into the error contract, and authenticate via `SubjectProvider`.
5. Bind context and tenant at request start; specify the contract tests (normal, error, i18n, async) to run.

## Expected output

```
Endpoint: GET /orders/{id} → 200 {id, status, statusLabel}
Errors: 404 unknown order, 400 validation — unified error body
i18n: statusLabel + error messages from message bundle per
  Accept-Language; fallback locale defined
Auth: SubjectProvider supplies caller; tenant bound at filter
Validation: field constraints → 400 with field list, no stack traces

Tests: normal / error / i18n fallback / async replay paths — pending run.
```

## Failure the skill must avoid

Translating only the happy-path labels and returning raw validation exceptions for the error case. The contract tests exist precisely because the error path is where the unified contract and the locale fallback actually break.
