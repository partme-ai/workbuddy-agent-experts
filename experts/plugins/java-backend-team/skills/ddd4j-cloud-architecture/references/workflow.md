# Workflow — ddd4j-cloud Architecture Review

A canonical end-to-end flow for reviewing ddd4j-cloud boundaries.

## Step 1 — Confirm the source of truth

- Run ddd4j-cloud-version-selection to fix the Cloud→Boot→ddd4j combination.
- Confirm the branch, SHA, and CodeGraph health.

## Step 2 — Map the modules

- Enumerate parent, bom, dependencies, extensions, compatibility-tests, verification, and samples.
- Confirm extensions canonical naming with no old cmpt references.

## Step 3 — Verify upstream boundaries

- Check which Boot/ddd4j artifacts the extensions consume and their versions.
- Classify anything missing as BLOCKED(upstream) rather than reimplementing it.

## Step 4 — Validate behavior

- Run compatibility tests and verification consumers.
- Confirm Context/Tenant restoration across sync, async, Reactor, and Feign paths.

## Step 5 — Report

Produce a single report containing:

- Combination and modules inspected with entry points.
- Upstream dependencies and their evidence state.
- Tests executed (compatibility/verification) and remaining gaps.
- Violations and risks with proposed fixes.
