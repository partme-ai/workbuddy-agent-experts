# Workflow — ddd4j-javalin Extensions Composition

A canonical end-to-end flow for composing optional Javalin extensions.

## Step 1 — Confirm the source of truth

- Run ddd4j-javalin-version-selection to fix the line.
- Locate the extensions module, samples, and module composition tests.

## Step 2 — Compose modules

- Order the Guice Modules and apply Modules.override for business bindings.
- Register SPI providers with unique implementations.

## Step 3 — Manage lifecycle

- Give extension resources explicit owners and idempotent close.
- Confirm extension failure degrades without breaking the core runtime.

## Step 4 — Test

- Run composition tests: default wiring, business override, and disabled-classpath paths.
- Exercise real behavior through the extension's public entry points.

## Step 5 — Report

Produce a single report containing:

- Module composition order and override points.
- SPI registrations and lifecycle owners.
- Tests executed and evidence state per tier.
- Risks with proposed fixes and missing inputs.
