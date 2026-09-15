# Workflow — ddd4j-quarkus Web Implementation

A canonical end-to-end flow for building REST endpoints on Quarkus.

## Step 1 — Confirm the source of truth

- Run ddd4j-quarkus-version-selection to fix the line.
- Locate ddd4j-quarkus-web, web-quarkus, and the HTTP tests.

## Step 2 — Define the HTTP contract

- Specify REST endpoints, status codes, payloads, and error responses.
- Bind request Context at request start with Quarkus REST filters/interceptors.

## Step 3 — Implement production controls

- Configure validation, authentication, shared-CAS idempotency, explicit CORS, and request limits.
- Separate liveness from readiness backed by real dependencies.

## Step 4 — Test

- Run QuarkusTest HTTP suites: normal, error, replay, and async paths.
- Confirm behavior holds in JVM mode and, where required, native mode.

## Step 5 — Report

Produce a single report containing:

- Endpoint inventory and contract coverage.
- Configuration keys and override points.
- Tests executed and evidence state per tier.
- Risks with proposed fixes and missing inputs.
