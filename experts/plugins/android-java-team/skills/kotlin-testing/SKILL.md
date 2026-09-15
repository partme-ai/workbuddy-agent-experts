---
name: kotlin-testing
license: Apache-2.0
description: Design high-value Kotlin tests across unit, integration, coroutine, property, contract, adapter, end-to-end, load, and regression layers using JUnit, Kotest, MockK, Turbine, Testcontainers, or project-native tools. Use to create or assess Kotlin tests, fixtures, coverage, determinism, mutation sensitivity, and whole-project acceptance modules.
---

# Kotlin Testing

Tests prove observable contracts. Coverage measures exercised structure but does not prove migration completeness or behavioral equivalence.

## Test design

- Name the contract, source test, defect, risk, or incident each test protects.
- Assert values, typed failures, ordering, state transitions, side effects, call counts, serialization bytes, cleanup, or externally observable timing boundaries.
- Prefer real values and fakes at owned boundaries. Mock only costly or nondeterministic collaborators.
- Use table/property tests for input partitions; retain each source case identity during migrations.
- For coroutines, use virtual time and event-driven coordination. Never use unbounded waits or fixed sleeps as synchronization.
- Reuse adapter conformance suites so every implementation receives the same contract assertions plus adapter-native tests.
- Keep fixtures versioned and deterministic. Record seeds, locale, timezone, encoding, and platform assumptions.

## Test layers

| Layer | Purpose |
|---|---|
| Unit | local algorithm and value contracts |
| Component | real module behavior with owned dependencies |
| Integration | external protocol, persistence, serialization, process boundaries |
| Contract | shared behavior for every adapter/provider |
| End-to-end | public workflow through production composition |
| `<project>-test` | whole-project migration parity and differential acceptance |

## Migration rule

Production modules keep local tests. A dedicated `<project>-test` Gradle module owns copied source fixtures, cross-module scenarios, Java/Kotlin runners, output normalization, and full differential comparison. It must not replace local tests, and local tests must not be counted as whole-project acceptance unless they actually cross the production composition boundary.

## Quality gates

```bash
./gradlew --no-daemon test
./gradlew --no-daemon check
```

Add mutation, fuzz/property, load/soak, compatibility, or security gates according to risk. Do not weaken assertions to improve pass rate or inflate coverage with trivial tests.

