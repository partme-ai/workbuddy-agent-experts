# Workflow — ddd4j-quarkus Testing

A canonical end-to-end flow for verifying a Quarkus integration.

## Step 1 — Confirm the source of truth

- Run ddd4j-quarkus-version-selection to fix the line.
- Locate the Quarkus test extensions and fixtures.

## Step 2 — Design the suite

- Plan QuarkusTest suites with QuarkusTestResource lifecycle management.
- Plan Arc validation for scopes and registrations; plan Testcontainers for real backends.

## Step 3 — Execute

- Run JVM-mode suites: HTTP, auth, data, MQ, and cache behaviors.
- Run native tests where the contract requires them.

## Step 4 — Record evidence honestly

- Handle Docker availability across Quarkus's classloader boundaries; mark skips BLOCKED/SKIPPED, never PASS.
- Keep source, behavior, container, CI, and publish evidence separate.

## Step 5 — Report

Produce a single report containing:

- Suites executed with mode (JVM/native) and toolchain.
- Pass/fail plus BLOCKED/SKIPPED inventory.
- Gaps against the feature matrix.
- Risks with proposed fixes and missing inputs.
