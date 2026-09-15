# Review, plan, and TDD workflow

## 1. Establish truth before changing files

Capture the real repo root, branch/worktrees, dirty state, tracking refs, JDK/Maven versions, branch POM contracts, current plan/tasks, and representative runtime entrypoints. Treat historical values as search hints, not current facts.

If CodeGraph is indexed, query the startup path and owners of configuration, readiness, idempotency, CORS, JPA, schedulers, and shutdown hooks. Confirm important claims against current source and tests.

## 2. Audit the plan instead of trusting checkboxes

For each task, classify it as:

- `DONE`: implementation exists and current evidence satisfies its acceptance behavior.
- `STALE`: evidence exists but the task marker/status is outdated; correct only the marker.
- `OPEN`: required behavior or evidence is absent.
- `BLOCKED`: a named external or authorization dependency prevents progress.

Do not bulk-check tasks. Link every completion to source plus executed verification.

When the user requires plan-first execution, update the existing Superpowers plan/specification with scope, non-goals, branch matrix, observable contracts, toolchains, rollback, acceptance gates, and release authorization boundary. Stop before implementation until approval is explicit.

## 3. Convert risks into failing contracts

Prefer public/observable behavior:

| Risk | First failing contract examples |
|---|---|
| Configuration is claimed but not loaded | system/env/property precedence and invalid-production-startup rejection |
| Readiness is constant | required participant down → not ready; optional participant degraded → explicit status |
| Local-only idempotency in a cluster | production profile without shared CAS fails startup; duplicate across instances is rejected |
| CORS is overly broad | disallowed origin rejected; credential/method/header policy enforced |
| Partial startup leaks resources | later participant failure closes earlier participants in reverse order |
| JPA/runtime is not closed | normal stop closes EMF/runtime once; repeated close is safe |
| Hooks accumulate | repeated start/stop leaves no stale hook and shutdown remains idempotent |

Confirm the test fails for the intended missing behavior, not for compilation, dependency resolution, ports, stale classes, or unavailable Docker.

## 4. Implement per line

Implement the smallest approved behavior on one authoritative line, then adapt deliberately:

- Javalin 6 and 7 route/configuration APIs may differ (`unsafe.routes` is relevant on Javalin 7).
- Preserve branch-local Java syntax and avoid newer syntax leaking into older baselines.
- Preserve Maven 3/POM 4.0 `<modules>` versus Maven 4/POM 4.1 `<subprojects>`.
- Inspect effective POMs when dependency management changes; a missing upstream managed artifact is a dependency failure, not automatically a product-code failure.
- Keep production defaults strict and development fallbacks explicit.

For lifecycle ordering, make initialization transactional in spirit: record successfully initialized participants, and on failure close only those participants in reverse order. `close()` and normal stop must be idempotent.

## 5. Verify in layers

For each line record JDK, Maven, command, exit code, test count, failures/errors/skips, and SHA:

1. New failing contract (red).
2. Focused test after implementation (green).
3. Affected module tests.
4. Clean branch reactor on the real toolchain.
5. Runtime/Testcontainers contracts where behavior crosses HTTP, DB, MQ, OIDC, or Outbox.
6. `git diff --check`, generated artifact checks, and applicable repository gates.

Never label tests that did not execute as passed. Docker unavailable, zero tests, skipped integration tests, or dependency-resolution failure must be reported as `BLOCKED`, `SKIPPED`, or `FAIL` according to the evidence.

## 6. Review before release

Review correctness, compatibility, security, concurrency, shutdown ordering, observability, and documentation. Confirm plan/tasks match actual evidence. Only then proceed to Git/CI/publication if authorized, using the release-gates reference.
