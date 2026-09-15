# Workflow — ddd4j-quarkus Architecture Review

A canonical end-to-end flow for reviewing ddd4j-quarkus boundaries.

## Step 1 — Confirm the source of truth

- Run ddd4j-quarkus-version-selection to fix the line (3.3.x/4.0.x).
- Confirm the branch, SHA, and CodeGraph health.

## Step 2 — Map the modules

- Enumerate parent, bom, dependencies, extension-parent, auth, data, mq, web, cache, extensions, and samples.
- Separate runtime from deployment modules per the Quarkus build-time model.

## Step 3 — Verify CDI wiring

- Check bean scopes, qualifiers, and BuildItem/Recorder usage without projecting the Spring model.
- Confirm request Context binding and cleanup across startup/shutdown and native boundaries.

## Step 4 — Validate behavior

- Run Arc/QuarkusTest suites for the target modules.
- Confirm BOM imports do not masquerade as registered beans.

## Step 5 — Report

Produce a single report containing:

- Line and modules inspected with entry points.
- CDI registrations, scopes, and lifecycle owners.
- Tests executed and evidence state per tier.
- Violations and risks with proposed fixes.
