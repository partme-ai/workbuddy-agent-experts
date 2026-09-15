---
name: swift-concurrency
license: Apache-2.0
description: Implement and review Swift structured concurrency with async/await, Task groups, actors, global actors, Sendable, AsyncSequence, continuations, cancellation, priorities, clocks, and deterministic testing. Use for actor-isolation errors, data races, task leaks, callback bridging, cancellation defects, or Swift 6 strict-concurrency work.
---

# Swift Concurrency

Treat isolation and cancellation as API contracts. Compile under the project's real Swift language and strict-concurrency settings.

## Core rules

- Prefer structured child tasks and task groups. Detached tasks require an explicit ownership and context-transfer justification.
- Keep mutable shared state actor-isolated or otherwise synchronized; do not silence diagnostics with unchecked `Sendable` without proof.
- Propagate cancellation through loops, AsyncSequence production, continuations, and I/O adapters.
- Resume checked continuations exactly once on every path; retain cancellation handles for callback APIs.
- Do not block cooperative executors with synchronous I/O or locks held across suspension.
- Preserve actor isolation in public protocols and closures. Use `@MainActor` only for UI/main-thread state, not as a general race workaround.
- Define ordering, buffering, backpressure, termination, and cleanup for AsyncStream/AsyncSequence adapters.
- Treat task-local values and priorities as contextual hints, not durable business state.

## Review sequence

1. Map task creation to owners and termination conditions.
2. Trace actor isolation and `Sendable` crossings.
3. Trace cancellation from caller to resources and continuations.
4. Identify blocking work, unbounded buffers, reentrancy assumptions, and priority inversions.
5. Add deterministic lifecycle tests using clocks, continuations, or event-driven coordination.
6. Run strict-concurrency compilation and stress the affected state transitions.

```bash
swift build
swift test
```

