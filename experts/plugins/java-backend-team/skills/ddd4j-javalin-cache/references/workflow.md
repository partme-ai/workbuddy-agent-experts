# Workflow — ddd4j-javalin Cache Integration

A canonical end-to-end flow for wiring caches into a Javalin service.

## Step 1 — Confirm the source of truth

- Run ddd4j-javalin-version-selection to fix the line.
- Locate the cache module and web idempotency tests.

## Step 2 — Select the provider

- Use Caffeine only for single-instance or development, with explicit configuration.
- Use a distributed cache with shared CAS for multi-instance production idempotency.

## Step 3 — Wire lifecycle

- Register cache providers as lifecycle participants with owners and idempotent close.
- Confirm readiness reflects cache backend availability where required.

## Step 4 — Test

- Verify TTL, invalidate, and concurrency for local providers.
- Verify real CAS contention, retries, and TTL re-acquisition against the shared backend.

## Step 5 — Report

Produce a single report containing:

- Provider choices with configuration keys.
- Lifecycle registration and shutdown order.
- Tests executed and evidence state per tier.
- Risks with proposed fixes and missing inputs.
