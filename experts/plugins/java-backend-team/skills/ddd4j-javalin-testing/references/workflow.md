# Workflow — ddd4j-javalin Testing

A canonical end-to-end flow for verifying a Javalin service.

## Step 1 — Confirm the source of truth

- Run ddd4j-javalin-version-selection to fix the line.
- Locate ddd4j-javalin-testcontainers and the web/auth/data test suites.

## Step 2 — Design the suite

- Plan HTTP contract tests against web-testkit paths.
- Plan Keycloak, PostgreSQL, and MQ broker round-trips via Testcontainers; bind port 0.

## Step 3 — Execute

- Run lifecycle tests: startup success, partial failure, restart, and repeated starts without hook accumulation.
- Run behavior tests for HTTP, auth, data, and MQ.

## Step 4 — Record evidence honestly

- Mark Docker-unavailable or skipped containers BLOCKED/SKIPPED — never PASS.
- Keep configuration, behavior, container, CI, and publish evidence separate.

## Step 5 — Report

Produce a single report containing:

- Suites executed with the line and toolchain.
- Pass/fail plus BLOCKED/SKIPPED inventory.
- Gaps against the feature matrix.
- Risks with proposed fixes and missing inputs.
