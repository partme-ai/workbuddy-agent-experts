# Workflow — ddd4j Architecture Review

A canonical end-to-end flow for reviewing or designing ddd4j architecture.

## Step 1 — Confirm the source of truth

- Identify the Git root, target branch, and maintenance line.
- Verify CodeGraph is healthy. If `.codegraph/` is absent, fall back to text search.

## Step 2 — Map the dependency graph

- Enumerate compile-time dependencies between modules.
- Confirm the arrows flow from adapters toward core ports.
- Flag any domain layer that imports framework types (`org.springframework.*`, `com.baomidou.mybatisplus.*`, `io.javalin.*`, `io.quarkus.*`).

## Step 3 — Trace the runtime wiring

- For each SPI port (`CommandBus`, `Publisher`, `SubjectProvider`, `Repository`), find the concrete adapter registered in the runtime module.
- Document the request-scope binding and the shutdown hook.
- Confirm context cleanup happens on success, exception, and async completion paths.

## Step 4 — Validate behavior

- Run architecture tests (ArchUnit, `ddd-rules`).
- Run behavior tests that exercise one end-to-end command path.
- Capture runtime evidence (logs, metrics, traces).

## Step 5 — Report

Produce a single report containing:

- Current branch, maintenance line, modules inspected.
- Ports and adapters found (with file paths and line numbers).
- Registration points and lifecycle owners.
- Tests and runtime evidence consulted.
- Violations (with file paths and proposed fixes).
- Inference (clearly labeled, never merged with facts).
