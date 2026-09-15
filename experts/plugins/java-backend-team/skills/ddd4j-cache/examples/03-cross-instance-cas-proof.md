# Example 3 — Proving cross-instance CAS actually holds

## Prompt

> We switched idempotency to `CasCache` on Redis. How do we prove it works before the go/no-go? Unit tests pass.

## What the skill should do

1. State plainly why the passing unit tests prove nothing: they run in one JVM against one view; cross-instance semantics are exactly what they cannot cover.
2. Define the minimum evidence: a test with two independent `CasCache` clients (separate connections) contending for the same key.
3. Enumerate the required assertions: exactly one winner, the loser observes the loss and does not submit, re-acquisition works after TTL, and network failure fails the operation rather than skipping it.
4. Run it against a real container (Testcontainers Redis), not a mock or embedded fake.
5. Grade the evidence and name anything left unproven.

## Expected output

```
Test plan (Testcontainers Redis, two independent clients):
  1. clientA.cas(key) vs clientB.cas(key) concurrently
     → exactly one true, one false
  2. loser re-submits → blocked by existing entry
  3. wait past TTL → re-acquisition succeeds
  4. kill Redis mid-operation → operation errors out; no "treated as won"
     path, no silent proceed

Run result: NOT RUN — this is the plan.
Evidence status: SOURCE (contract read) only. Single-JVM tests dismissed as
non-probative for cluster semantics.
```

## Failure the skill must avoid

Accepting "unit tests pass" as the go signal. The single-JVM suite is structurally incapable of exercising the failure mode that matter — two JVMs racing on one key.
