# Example 3 — Cross-line API assumption

## Prompt

> Our other service uses ddd4j 3.0.x and calls `query.persistence(OrderPO.class)`. We're on 1.0.x. Can we just copy that?

## What the skill should do

1. Refuse to confirm parity from the name alone. The `1.0.x`, `2.0.x`, and `3.0.x` APIs are verified per line.
2. Read `PersistenceQueryScope` in **both** lines and compare the actual signature.
3. Report one of three outcomes: identical signature, different signature (with the diff), or symbol absent in the target line.
4. Mark the unverified parts explicitly rather than guessing.

## Expected output

```
Question: can `query.persistence(P.class)` be copied from 3.0.x to 1.0.x?

Evidence:
  - 3.0.x: PersistenceQueryScope.java line NN — `<P> Query<M> persistence(Class<P> poType)`
  - 1.0.x: <read result, or "symbol not found at the expected path">

Verdict: <IDENTICAL | DIFFERENT | ABSENT>
Evidence status: SOURCE (read) — TEST and CI not run for the 1.0.x side.
Missing: 1.0.x test proving the method behaves as expected; how to provide: run the line's query tests.
```

## Failure the skill must avoid

Answering "yes, the API is stable across lines" without reading the older line. That is exactly the cross-line parity assumption the skill exists to prevent.
