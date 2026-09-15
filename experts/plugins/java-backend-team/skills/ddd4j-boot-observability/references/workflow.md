# Workflow — ddd4j-boot Observability Integration

A canonical end-to-end flow for wiring observability through ddd4j-boot.

## Step 1 — Confirm the source of truth

- Run ddd4j-boot-version-selection to fix the line.
- Locate Actuator, monitor, metrics, and OTel AutoConfiguration and Properties.

## Step 2 — Design the observability set

- Separate liveness from readiness; make readiness aggregate real dependencies.
- Plan metrics, trace, and logging exporters against the observability backend.

## Step 3 — Verify wiring

- Check conditional wiring, default beans, and user Bean override points.
- Confirm the off switch truly skips assembly and exporters have owners with idempotent close.

## Step 4 — Test

- Execute context tests plus behavior tests: probe responses, metric increments, export delivery.
- Verify the collector/exporter actually receives data.

## Step 5 — Report

Produce a single report containing:

- Chosen exporters and endpoints with configuration keys.
- AutoConfiguration entry points and override points.
- Test results and evidence state (configuration, bean, behavior, CI, publish reported separately).
- Risks with proposed fixes and missing inputs.
