# Workflow — ddd4j Runtime Binding

A canonical end-to-end flow for binding a framework container to ddd4j core.

## Step 1 — Confirm the source of truth

- Identify the target runtime and maintenance line.
- List the SPI ports that need registration (CommandBus, Publisher, SubjectProvider, Cache, Repository).

## Step 2 — Define assembly order

- Order provider initialization by dependency.
- Note the framework registration point (e.g. afterSingletonsInstantiated, CDI observer, Module).

## Step 3 — Register and guard

- Register each SPI exactly once; fail fast on duplicate executor types.
- Use scope objects to restore previous values on unbind.

## Step 4 — Bind request context

- Establish Request/Thread/Reactive Context at request start.
- Restore the previous context on success, exception, and async completion.

## Step 5 — Manage lifecycle

- Aggregate readiness from real dependencies.
- On partial failure, roll back initialized resources in reverse order.
- Drain, then idempotent close.

## Verify

- Exercise the full validate → initialize → register → ready → drain → close path with runtime-testkit.
- Run real framework startup/shutdown tests.
- Produce a report with registration points, lifecycle owners, evidence state, and remaining risk.
