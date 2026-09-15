# Workflow — ddd4j-quarkus Runtime Binding

A canonical end-to-end flow for binding CDI/Arc to ddd4j core.

## Step 1 — Confirm the source of truth

- Run ddd4j-quarkus-version-selection to fix the line.
- Locate runtime-quarkus, its configuration, and Arc tests.

## Step 2 — Register the SPI ports

- Produce CommandBus, DomainEventPublisher, and SubjectProvider beans via producers/BuildItems.
- Fail fast on duplicate registrations.

## Step 3 — Bind request context

- Establish request-scoped Context binding and restoration on success, exception, and async completion.
- Confirm startup/shutdown observers own resource lifecycle.

## Step 4 — Verify readiness and shutdown

- Aggregate readiness from real dependencies.
- Confirm drain and idempotent close, including native image boundaries.

## Step 5 — Verify

- Run Arc/QuarkusTest suites covering startup, request context, shutdown, and duplicate registration.
- Produce a report with registration points, lifecycle owners, evidence state, and remaining risk.
