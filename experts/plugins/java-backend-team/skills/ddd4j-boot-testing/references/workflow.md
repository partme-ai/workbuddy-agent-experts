# Workflow — ddd4j-boot Testing

A canonical end-to-end flow for verifying ddd4j-boot integrations.

## Step 1 — Confirm the source of truth

- Run ddd4j-boot-version-selection to fix the line.
- Locate the target module's src/test, consistency scripts, and Testcontainers fixtures.

## Step 2 — Design the test matrix

- Plan ApplicationContextRunner and slice tests for conditional wiring and user overrides.
- Plan HTTP contract, database, Redis, and broker round-trips against real backends.

## Step 3 — Execute

- Run the context and behavior suites for the target modules.
- Run container-based suites where Docker is available.

## Step 4 — Record evidence honestly

- Mark Docker-unavailable or skipped suites BLOCKED/SKIPPED — never PASS.
- Keep configuration presence, bean creation, behavior, CI, and publish evidence separate.

## Step 5 — Report

Produce a single report containing:

- Suites executed with the line, JDK, and Maven used.
- Pass/fail plus BLOCKED/SKIPPED inventory.
- Coverage of the feature matrix and gaps found.
- Risks with proposed fixes and missing inputs.
