# Example 1 — Context across async and Feign hops

## Prompt

> In our ddd4j-cloud service the request context and user Subject are fine in the controller, but inside our `@Async` report builder and our Feign call to the pricing service they're gone. Wire it properly.

## What the skill should do

1. Fix the combination with `ddd4j-cloud-version-selection`, then read the line's context filters to use the provided mechanisms, not ad-hoc copies.
2. Bind request headers into `ThreadContext` at entry and wrap each `@Async` handoff with explicit capture/restore around the executor.
3. Wire the Feign interceptor path so context and tenant headers are captured before the call and cleared after — including on each retry attempt.
4. Cover the terminal states: restore on sync, async, Reactor, and Feign completion; release on success, exception, and before the thread returns to the pool.
5. Specify the tests to run, including the exception and pool-reuse paths.

## Expected output

```
Hop map:
  HTTP entry → ThreadContext bind (web filter) — owner: web extension
  @Async hop → capture/restore wrapper — owner: async propagation
  Feign hop  → interceptor captures headers, clears after — owner: feign extension

Terminal states covered: sync / async / Reactor / Feign
Cleanup paths: success, exception, pool reuse

Tests to run: propagation per hop + exception path + pool-reuse path +
real Feign round-trip. Evidence after run: <graded>.
```

## Failure the skill must avoid

Fixing only the `@Async` case by copying the context map manually into the task. It patches one hop, skips the Feign capture/clear cycle, and leaves the exception-path cleanup gap that leaks context to the next request on the pooled thread.
