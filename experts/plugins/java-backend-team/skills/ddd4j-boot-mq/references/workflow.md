# Workflow — ddd4j-boot MQ Integration

A canonical end-to-end flow for wiring messaging through ddd4j-boot.

## Step 1 — Confirm the source of truth

- Run ddd4j-boot-version-selection to fix the line.
- Locate the MQ AutoConfiguration, Properties, listener registrar, and the corresponding ddd4j-mq modules.

## Step 2 — Select the broker

- Match the broker to delivery semantics and ordering needs.
- Confirm topic/tag/group/namespace configuration and required versus optional listeners.

## Step 3 — Verify wiring

- Check conditional wiring, default beans, and user Bean override points.
- Confirm required-listener failure blocks startup, retry/dead-letter policy is configured, and close is idempotent.

## Step 4 — Test

- Execute context tests plus Testcontainers round-trips: publish/consume, ack, nack/retry, duplicates, recovery, shutdown.
- Mark Docker-unavailable suites BLOCKED/SKIPPED.

## Step 5 — Report

Produce a single report containing:

- Chosen broker and adapter with configuration keys.
- AutoConfiguration entry points, listener registrations, and override points.
- Test results and evidence state (configuration, bean, behavior, CI, publish reported separately).
- Risks with proposed fixes and missing inputs.
