# Workflow — ddd4j-cloud Observability Integration

A canonical end-to-end flow for observability in a Spring Cloud service.

## Step 1 — Confirm the source of truth

- Run ddd4j-cloud-version-selection to fix the combination.
- Locate the monitor/nacos/sentinel extensions and tests.

## Step 2 — Design the observability set

- Separate liveness from readiness; readiness aggregates real dependencies including Nacos and Sentinel.
- Plan trace propagation, metrics, and logging against the backend.

## Step 3 — Wire external services

- Configure Nacos registration/configuration and Sentinel rules with real connectivity.
- Mark any untestable external behavior NOT VERIFIED rather than assuming success.

## Step 4 — Test

- Verify probes respond per dependency state.
- Verify trace context propagation across sync, async, Reactor, and Feign paths.
- Verify metrics and logs carry low-cardinality, redacted labels.

## Step 5 — Report

Produce a single report containing:

- Extension inventory with configuration keys.
- Probe behavior per dependency state and evidence per tier.
- Tests executed and remaining gaps.
- Risks with proposed fixes and missing inputs.
