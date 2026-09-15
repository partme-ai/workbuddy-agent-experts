# Workflow — ddd4j-javalin Architecture Review

A canonical end-to-end flow for reviewing ddd4j-javalin module boundaries.

## Step 1 — Confirm the source of truth

- Run ddd4j-javalin-version-selection to fix the line (6.7.x/7.1.x/7.2.x).
- Confirm the branch, SHA, and CodeGraph health in the target checkout.

## Step 2 — Map the modules

- Enumerate parent, bom, dependencies, core, ddd, auth, data, mq, web, cache, extensions, and testcontainers.
- Confirm each module's dependency direction and Javalin/JDK/Maven/POM contract.

## Step 3 — Verify composition

- Trace how the runtime composes auth, data, MQ, web, and cache providers.
- Confirm Context/Subject/resource cleanup on success, exception, and async terminal states.

## Step 4 — Validate behavior

- Run the line's contract and behavior tests.
- Confirm real readiness aggregation, shared CAS idempotency, and explicit CORS for production paths.

## Step 5 — Report

Produce a single report containing:

- Line, modules inspected, and entry points (with file paths).
- Composition and lifecycle ownership.
- Tests executed and evidence state per tier.
- Violations and risks with proposed fixes.
