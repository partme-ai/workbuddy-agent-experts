# Workflow — ddd4j-cloud Context Propagation

A canonical end-to-end flow for request context propagation in Spring Cloud.

## Step 1 — Confirm the source of truth

- Run ddd4j-cloud-version-selection to fix the combination.
- Locate core/data/web/feign context filters and their tests.

## Step 2 — Map the propagation surface

- Enumerate entry points: request headers, ThreadContext, async executors, Reactor, and Feign calls.
- Identify which extension handles each hop.

## Step 3 — Verify restoration and cleanup

- Confirm restoration on sync, async, Reactor, and Feign terminal states.
- Confirm cleanup on success, exception, and thread-pool reuse; no residue across requests.

## Step 4 — Test

- Run propagation tests across every hop, including exception and pool-reuse paths.
- Verify cross-service headers survive a real Feign round-trip.

## Step 5 — Report

Produce a single report containing:

- Propagation map (hop → mechanism → owner) with file paths.
- Restoration/cleanup coverage per terminal state.
- Tests executed and evidence state per tier.
- Violations and risks with proposed fixes.
