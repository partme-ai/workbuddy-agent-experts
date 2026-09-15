# Workflow — ddd4j-boot Architecture Review

A canonical end-to-end flow for reviewing ddd4j-boot module boundaries.

## Step 1 — Confirm the source of truth

- Run ddd4j-boot-version-selection to fix the line, JDK, Maven, and POM model.
- Confirm the branch, SHA, and CodeGraph health.

## Step 2 — Map the modules

- Enumerate parent, dependencies, bom, core, auth, data, mq, web, cache, extensions, and samples.
- Separate aggregator POMs from concrete implementation modules.

## Step 3 — Verify assembly

- For each AutoConfiguration, confirm conditional wiring, default implementations, and user Bean override points.
- Confirm platform versions stay in the BOM, not in concrete modules.

## Step 4 — Validate behavior

- Run target module context and behavior tests.
- Distinguish dependency resolution from bean creation evidence.

## Step 5 — Report

Produce a single report containing:

- Version line and modules inspected (with file paths).
- Auto-configuration entry points, defaults, and override points.
- Tests executed and evidence state (source, test, CI, publish reported separately).
- Violations and risks, each with a proposed fix.
