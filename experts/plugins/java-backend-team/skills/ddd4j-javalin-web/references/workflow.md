# Workflow — ddd4j-javalin Web Implementation

A canonical end-to-end flow for building HTTP behavior on Javalin.

## Step 1 — Confirm the source of truth

- Run ddd4j-javalin-version-selection to fix the line.
- Locate the web module, web-testkit, and HTTP contract tests.

## Step 2 — Define the HTTP contract

- Specify routes, status codes, payloads, and error responses via web-testkit paths.
- Confirm Request/Trace/Tenant Context binding at request start.

## Step 3 — Implement production controls

- Configure CORS origins, credentials, headers, and methods explicitly.
- Configure validation, idempotency (shared CAS for multi-instance), request limits, and async timeouts.

## Step 4 — Clean up and report health

- Restore Context/Subject on success, exception, and async completion.
- Provide distinct liveness and readiness endpoints backed by real dependencies.

## Step 5 — Verify

- Run normal, error, replay, and async HTTP contract tests.
- Produce a report with contract coverage, evidence state, and remaining risk.
