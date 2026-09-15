# Workflow — ddd4j-quarkus Cache Integration

A canonical end-to-end flow for wiring caches into a Quarkus service.

## Step 1 — Confirm the source of truth

- Run ddd4j-quarkus-version-selection to fix the line.
- Locate ddd4j-quarkus-cache and the cache tests.

## Step 2 — Select the provider

- Compare Quarkus Cache, Redis, and the ddd4j Cache SPI against the consistency target.
- Use shared CAS for multi-instance idempotency.

## Step 3 — Wire CDI and lifecycle

- Register cache providers with correct CDI scopes and configuration mappings.
- Confirm startup/shutdown observers own connections and close is idempotent.

## Step 4 — Test

- Run QuarkusTest suites for TTL, invalidate, concurrency, and real CAS contention.
- Verify native image compatibility where the contract requires it.

## Step 5 — Report

Produce a single report containing:

- Provider choices with configuration keys and CDI scopes.
- Lifecycle owners and registration points.
- Tests executed and evidence state per tier.
- Risks with proposed fixes and missing inputs.
