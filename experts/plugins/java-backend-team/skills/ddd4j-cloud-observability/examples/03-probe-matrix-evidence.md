# Example 3 — Evidence: trace propagation across every hop

## Prompt

> Our traces keep breaking between services and inside async jobs. Produce evidence of where the trace context survives and where it doesn't — per hop.

## What the skill should do

1. Fix the combination, then run a traced request through every hop the service uses: MVC handler → `@Async` task → Reactor chain → Feign call.
2. Assert at each hop that the trace parent-child relationship holds (same trace id, correct parent span).
3. Identify per hop whether the loss is a missing propagation hook, a thread handoff without capture, or a downstream not forwarding headers.
4. Produce a hop-by-hop evidence table instead of a single pass/fail.
5. Grade evidence per tier and list the fixes per broken hop.

## Expected output

```
Trace propagation matrix (one traced request):
  HTTP entry → handler            trace continuous  PASS
  handler → @Async task           trace id lost     DEFECT (no capture)
  handler → Reactor chain         trace continuous  PASS
  handler → Feign → downstream    headers forwarded PASS
  consumer thread (binder)        NOT RUN (no stream in this service)

Verdict: async hop is the break; fix = capture/restore at the executor
handoff (context skill owns the mechanism).
Evidence: TEST (traced round-trip); binder hop NOT RUN — out of scope.
```

## Failure the skill must avoid

Reporting "tracing works" from one clean end-to-end trace on the happy sync path. The fragmented traces QA reported come from the async hop — the one path a happy-path demo never exercises.
