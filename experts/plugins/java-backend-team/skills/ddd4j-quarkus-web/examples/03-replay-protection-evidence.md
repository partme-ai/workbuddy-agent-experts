# Example 3 — Evidence request: prove replay protection across replicas

## Prompt

> A client retried a payment and got charged twice in staging where we run two replicas. Management wants proof of what replay protection we actually have before launch. Show me.

## What the skill should do

1. Treat it as an evidence request: establish what the idempotency design claims (shared CAS) and what the tests prove.
2. Read the idempotency wiring: where the key is stored — the shared CAS store or an in-process map.
3. Check whether any QuarkusTest asserts replay behavior across more than one instance, or only single-node.
4. Connect the incident: a local map is per replica, so the retried request hit the other replica and created a second payment.
5. Specify the closing evidence: a two-instance QuarkusTest (or Testcontainers topology) asserting same-key replay returns the original result.

## Expected output

```
Replay protection evidence — payment endpoint:

  Design claim: Idempotency-Key via shared CAS.
  Source check: key stored in in-process ConcurrentHashMap (PaymentController line NN)
                ← NOT shared across replicas.
  Test evidence: single-node replay test PASS; multi-instance replay test ABSENT.

Incident match: retry routed to replica B; replica B had no key entry → second charge.

Closing evidence needed:
  - move key store to the shared CAS-backed Cache SPI implementation,
  - add a two-instance replay QuarkusTest,
  - run on the launch SHA.
Status: TEST FAILS INTENT — current evidence cannot support the claim.
```

## Failure the skill must avoid

Answering "replay protection is in place, the test passes." The single-node green test is exactly the evidence trap: the protection exists only within one JVM.
