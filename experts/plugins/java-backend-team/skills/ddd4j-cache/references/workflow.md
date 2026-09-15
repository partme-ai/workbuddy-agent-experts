# Workflow — ddd4j Cache Implementation

A canonical end-to-end flow for selecting and hardening a ddd4j cache.

## Step 1 — Confirm the source of truth

- Identify which store is authoritative for the data and what happens on a cache miss.
- Confirm the deployment shape: instance count, shared Redis or not.

## Step 2 — Select the implementation

- Match the scenario to the provider matrix (local, Redis, Redisson, JetCache, Memcached).
- Verify the artifact exists in the current maintenance line.

## Step 3 — Configure keys and serialization

- Build keys with domain, tenant, version, and stable identifier.
- Restrict REDIS_OBJECT_MAPPER to trusted data.

## Step 4 — Implement behavior

- Verify get/put/invalidate, TTL units, zero and negative values.
- For locks: owner, timeout, and release on exception.
- For idempotency: use AtomicCache/CasCache, never get-then-put.

## Step 5 — Test

- Local: TTL, capacity, invalidate, concurrency.
- Distributed: real container round-trips, contention, disconnection, retry without duplicates.
- Mark skipped containers BLOCKED/SKIPPED.

## Verify

- Confirm observability (hit/miss/error) aligns with business state.
- Confirm no sensitive values appear in keys or logs.
- Produce a report with implementation choice, evidence state, and remaining risk.
