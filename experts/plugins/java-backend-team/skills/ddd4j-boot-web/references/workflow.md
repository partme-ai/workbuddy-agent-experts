# Workflow — ddd4j-boot Web Integration

A canonical end-to-end flow for building a web application through ddd4j-boot.

## Step 1 — Confirm the source of truth

- Run ddd4j-boot-version-selection to fix the line.
- Locate the web AutoConfiguration, Properties, and the ddd4j-web-webmvc/webflux modules.

## Step 2 — Select the web stack

- Choose Spring MVC or WebFlux and confirm context binding, error handling, and authentication wiring.

## Step 3 — Verify wiring

- Check conditional wiring, default beans, and user Bean override points.
- Confirm validation, idempotency, CORS allowlist, limits, and readiness configuration.

## Step 4 — Test

- Execute context tests plus HTTP contract tests: normal, error, replay, and async paths.
- Confirm readiness aggregates real dependencies and never hardcodes READY.

## Step 5 — Report

Produce a single report containing:

- Chosen web stack with configuration keys.
- AutoConfiguration entry points and override points.
- Test results and evidence state (configuration, bean, behavior, CI, publish reported separately).
- Risks with proposed fixes and missing inputs.
