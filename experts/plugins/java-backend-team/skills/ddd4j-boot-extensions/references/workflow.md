# Workflow — ddd4j-boot Extensions Integration

A canonical end-to-end flow for adding an optional Boot extension.

## Step 1 — Confirm the source of truth

- Run ddd4j-boot-version-selection to fix the line.
- List the current ddd4j-boot-extensions submodules from the root POM.

## Step 2 — Select the extension

- Match the need (Akka, Excel, QLExpress, QRCode, Monitor, …) to an existing submodule.
- Mark anything absent as NOT IMPLEMENTED rather than inventing it.

## Step 3 — Verify wiring

- Check classpath guards, enabled switches, conditional wiring, and user Bean overrides.
- Confirm resources have owners, failure rollback, and idempotent close.

## Step 4 — Test

- Execute context tests and real behavior tests: enabled, disabled, classpath-missing.
- Confirm disabling degrades without breaking core.

## Step 5 — Report

Produce a single report containing:

- Chosen extensions with configuration keys.
- AutoConfiguration entry points and override points.
- Test results and evidence state (configuration, bean, behavior, CI, publish reported separately).
- Risks with proposed fixes and missing inputs.
