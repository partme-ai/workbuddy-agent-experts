---
name: kotlin-coroutines
license: Apache-2.0
description: Implement and review Kotlin structured concurrency with suspend functions, CoroutineScope, dispatchers, Flow, channels, cancellation, timeouts, supervision, context propagation, and deterministic coroutine testing. Use when code imports kotlinx.coroutines, exposes suspend or Flow APIs, crosses blocking boundaries, or has lifecycle, race, leak, or cancellation defects.
---

# Kotlin Coroutines

Treat cancellation, ownership, and lifecycle as public contracts, not implementation details.

## Core rules

- Every launched coroutine must have an owner whose lifetime is explicit. Avoid `GlobalScope`.
- Prefer `coroutineScope` for fail-together work and `supervisorScope` only when sibling failure isolation is required by contract.
- Re-throw `CancellationException`; broad exception handlers must not consume cancellation.
- Move blocking calls to an appropriate dispatcher or replace them with cancellable asynchronous APIs.
- Do not expose a cold `Flow` as if it were shared state. Choose cold Flow, `StateFlow`, or `SharedFlow` from subscriber and replay semantics.
- Bound channels and queues. Define overflow, fairness, ordering, and shutdown behavior.
- Preserve context intentionally; do not pass request-scoped mutable state through globals or thread locals.
- Make cleanup run on success, failure, timeout, and cancellation. Use `finally` and cancellable resource APIs.

## Review sequence

1. Map coroutine creation sites to scope owners.
2. Trace cancellation from caller through child work and adapters.
3. Identify blocking calls and dispatcher assumptions.
4. Record ordering, buffering, retry, timeout, and supervision contracts.
5. Write deterministic tests using virtual time or event-driven synchronization.
6. Stress lifecycle transitions and repeated cancellation.

## Testing expectations

Assert emitted values, ordering, terminal errors, cancellation cleanup, no post-cancel work, and resource closure. Avoid fixed sleeps and tests that only assert completion.

```bash
./gradlew --no-daemon test
./gradlew --no-daemon check
```

