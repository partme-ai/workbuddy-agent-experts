# Workflow — ddd4j-cloud Web Implementation

A canonical end-to-end flow for building a web service in Spring Cloud.

## Step 1 — Confirm the source of truth

- Run ddd4j-cloud-version-selection to fix the combination.
- Locate the webmvc/webflux extensions and tests.

## Step 2 — Define the HTTP contract

- Specify endpoints, status codes, payloads, and error responses.
- Plan internationalized response messages and validation constraints.

## Step 3 — Wire context and tenant

- Bind context and tenant at request start; restore on sync, async, Reactor, and Feign terminal states.
- Wire authentication to the SubjectProvider.

## Step 4 — Implement readiness

- Aggregate readiness from real dependencies (database, Nacos, Sentinel as applicable).
- Keep liveness distinct; never hardcode READY.

## Step 5 — Verify

- Run HTTP contract tests: normal, error, i18n, replay, and async paths.
- Produce a report with contract coverage, evidence state, and remaining risk.
