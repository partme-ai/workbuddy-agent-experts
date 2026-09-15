# Workflow — ddd4j-javalin Runtime Hardening

A canonical end-to-end flow for the Javalin runtime lifecycle.

## Step 1 — Confirm the source of truth

- Run ddd4j-javalin-version-selection to fix the line.
- Locate Ddd4jJavalinRuntime, lifecycle participants, and their tests.

## Step 2 — Review the lifecycle

- Verify the coherent `start → validate → initialize → ready → drain → close` path.
- Confirm rollback of initialized resources in reverse order after partial failure.
- Confirm close is idempotent and shutdown hooks do not accumulate.

## Step 3 — Verify readiness and context

- Confirm readiness aggregates required and optional participants; liveness stays distinct.
- Confirm Context/Subject cleanup on success, exception, and async terminal states.

## Step 4 — Test

- Exercise startup success, partial failure, restart, and embedded-test repetition.
- Run behavior tests for configuration validation and SPI registration.

## Step 5 — Report

Produce a single report containing:

- Lifecycle path with registration and ownership points (file paths and line numbers).
- Readiness contributors and their required/optional classification.
- Tests executed and evidence state per tier.
- Violations and risks with proposed fixes.
