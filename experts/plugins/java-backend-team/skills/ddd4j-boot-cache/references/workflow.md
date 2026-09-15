# Workflow — ddd4j-boot Cache Integration

A canonical end-to-end flow for wiring caches through ddd4j-boot.

## Step 1 — Confirm the source of truth

- Run ddd4j-boot-version-selection to fix the line.
- Locate the cache AutoConfiguration, Properties, and the corresponding ddd4j-cache modules.

## Step 2 — Select the provider

- Match local (Caffeine/Guava/Hutool), Redis, Redisson, or JetCache to the consistency target.
- Confirm TTL units, capacity, and key strategy.

## Step 3 — Verify wiring

- Check conditional wiring, default beans, and user Bean override points.
- Confirm the off switch truly skips assembly and connections have owners with idempotent close.

## Step 4 — Test

- Execute context tests plus TTL, invalidate, concurrency, and CAS contention behavior.
- Cover Redis round-trips and CAS against a real backend.

## Step 5 — Report

Produce a single report containing:

- Chosen provider with configuration keys.
- AutoConfiguration entry points and override points.
- Test results and evidence state (configuration, bean, behavior, CI, publish reported separately).
- Risks with proposed fixes and missing inputs.
