---
name: swift-testing
license: Apache-2.0
description: Design high-value Swift tests across XCTest or Swift Testing, unit, integration, async, contract, adapter, end-to-end, property, performance, and regression layers. Use to create or assess Swift tests, fixtures, coverage, determinism, mutation sensitivity, platform matrices, and whole-project migration acceptance packages.
---

# Swift Testing

Tests prove observable contracts. Coverage is supporting structural evidence, not behavioral equivalence.

## Test design

- Name the source test, contract, defect, risk, or incident protected by each test.
- Assert values, typed errors, ordering, state transitions, side effects, bytes, cleanup, and public lifecycle behavior.
- Prefer real values and controlled fakes at owned boundaries. Mock only expensive or nondeterministic collaborators.
- Preserve every parameterized source case identity during migrations even when Swift groups cases in one test declaration.
- For async tests, use expectations, continuations, clocks, or event-driven hooks with bounded timeouts; avoid fixed sleeps.
- Reuse one conformance suite across adapters, then add adapter-native failure and lifecycle cases.
- Test every claimed platform or condition in CI; conditional compilation is part of the behavioral surface.

## Layers

| Layer | Purpose |
|---|---|
| Unit | local algorithms and value contracts |
| Component | one target with owned collaborators |
| Integration | filesystem, database, network protocol, C/Objective-C bridge |
| Contract | shared requirements for every provider/adapter |
| End-to-end | public workflow through production composition |
| `<project>-test` | whole-project migration parity and differential acceptance |

## Migration rule

Production targets retain local tests. A dedicated `<project>-test` Package or clearly separated integration target owns copied Java fixtures, cross-target scenarios, Java/Swift runners, normalization, and full differential reports. Neither layer substitutes for the other.

```bash
swift test
swift test --enable-code-coverage
```

Add sanitizers, Thread Sanitizer, performance, fuzz/property, compatibility, or load gates according to risk. Do not inflate coverage with trivial assertions.

