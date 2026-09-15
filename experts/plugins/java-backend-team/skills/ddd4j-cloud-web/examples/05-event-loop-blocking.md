# Example 5 — WebFlux service stalls under load

## Prompt

> We moved one service to the WebFlux extension and now it freezes entirely for seconds at a time under moderate load. CPU is idle. Same code worked on MVC. What changed?

## What the skill should do

1. Name the WebFlux-specific failure first: handlers run on event-loop threads, so one blocking call (JDBC, remote call, file IO) stalls every request multiplexed on that loop — idle CPU is the signature.
2. Hunt the blocking sites: synchronous data-access calls, blocking Feign/HTTP clients, and `block()` on reactive chains.
3. Check the context angle: if someone "fixed" context loss by copying ThreadLocals onto the event loop, that is both a leak and a sign the reactive propagation path was skipped.
4. Give the legitimate fixes: move blocking work to a bounded scheduler with explicit context capture, or use the line's non-blocking data/Feign paths.
5. Require the async contract test before sign-off — this failure only reproduces under concurrency.

## Expected output

```
Findings:
  - OrderHandler calls the JDBC repository directly on the event loop
    (blocking) — stalls all requests on that loop.
  - One controller calls `.block()` on an internal reactive client.

Why MVC worked: request-per-thread isolates blocking calls per request;
event-loop multiplexing concentrates them.

Fix: route blocking work to a bounded scheduler with context captured
before the handoff; replace `.block()` with the non-blocking path.
Evidence: SOURCE. Concurrency reproduction test NOT RUN — required.
```

## Failure the skill must avoid

"Fixing" it by raising the event-loop thread count. Blocking calls on loops scale the stall, not remove it, and the context copied along with the workaround starts leaking across requests — the underlying blocking work must move off the loop.
