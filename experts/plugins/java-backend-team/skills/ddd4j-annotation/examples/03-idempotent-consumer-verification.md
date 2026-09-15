# Example 3 — Proving `@ApiIdempotent` actually works

## Prompt

> Our payment endpoint has `@ApiIdempotent` on it, so duplicates are handled, right? The same order got charged twice yesterday.

## What the skill should do

1. Refuse to accept the annotation as proof of behavior.
2. Trace the api-family consumer chain: which Web/Runtime adapter must register the `IdempotencyGuard`, and is it on the classpath?
3. Check the idempotency scope backing (single-instance local vs shared CAS) and whether it matches the deployment.
4. Require evidence: a test that submits the same request twice and asserts one side effect.
5. Report the evidence state for each layer (SOURCE, TEST, runtime observation).

## Expected output

```
Annotation: @ApiIdempotent on PaymentResource.charge (SOURCE confirmed, line NN)
Consumer:   IdempotencyGuard — NOT registered in the Web adapter config
Scope:      N/A (no guard found)
Evidence:   SOURCE only. Duplicate-submission test NOT RUN.

Verdict: the annotation is inert. Charges are NOT deduplicated.
Missing: registered guard + behavioral test; how to provide: wire the guard in
the web adapter and add a replay test asserting a single charge.
```

## Failure the skill must avoid

Answering "yes, `@ApiIdempotent` handles duplicates." The double charge happened precisely because the annotation was trusted as its own implementation.
