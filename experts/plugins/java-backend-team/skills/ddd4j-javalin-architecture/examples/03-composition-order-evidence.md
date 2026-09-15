# Example 3 — Proving composition and shutdown order

## Prompt

> Can you verify the claim that our cache provider is shut down after the data provider on 6.7.x? We need it for a change ticket.

## What the skill should do

1. Fix the line (6.7.x → Javalin 6.7/ddd4j 1/JDK 17/Maven 3) and locate the registration sites of both lifecycle participants in the current source.
2. Read `JavalinLifecycleParticipant` registration order in `Ddd4jJavalinRuntime` — shutdown runs in reverse registration order, so "cache closes after data" means cache must be registered before data.
3. Find the test that executes startup and close and asserts the close order; if none exists, the claim is unproven.
4. Report the evidence tier honestly: source ordering plus an executed test, or the exact gap.

## Expected output

```
Claim: cache closes after data on 6.7.x.

Evidence:
  - Registration site: RuntimeConfiguration.java line NN — data registered before cache
    (reverse-order shutdown ⇒ cache closes first)          ← contradicts the claim
  - Close-order test: NOT FOUND on this branch
  - Behavior test run: NOT RUN

Verdict: claim NOT SUPPORTED. Current registration makes cache close before data.
Fix: swap registration order and add a close-order contract test.
Missing: executed shutdown-order test; how to provide: run the lifecycle suite
on 6.7.x after the fix.
```

## Failure the skill must avoid

Answering "yes, shutdown is reverse registration order, so it's fine" without reading the actual registration order. The generic rule does not prove this service's order — the registration site and an executed test do.
