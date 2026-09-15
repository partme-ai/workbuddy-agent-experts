# Workflow — ddd4j-cloud Testing

A canonical end-to-end flow for verifying a Spring Cloud integration.

## Step 1 — Confirm the source of truth

- Run ddd4j-cloud-version-selection to fix the combination.
- Locate compatibility tests, src/test suites, and verification consumers.

## Step 2 — Design the suite

- Plan compatibility tests for the WebMVC/MySQL pairing.
- Plan context propagation, Feign round-trips, and Binder tests against real databases and brokers.

## Step 3 — Execute

- Run unit/behavior suites and container-based suites where Docker exists.
- Run remote-consumer verification against the private repository.

## Step 4 — Record evidence honestly

- Classify external-service gaps as NOT VERIFIED, upstream gaps as BLOCKED(upstream), and non-started CI as BLOCKED(infrastructure).
- Never translate skips into success.

## Step 5 — Report

Produce a single report containing:

- Suites executed with the combination and toolchain.
- Pass/fail plus BLOCKED/SKIPPED/NOT VERIFIED inventory.
- Gaps against the feature matrix.
- Risks with proposed fixes and missing inputs.
