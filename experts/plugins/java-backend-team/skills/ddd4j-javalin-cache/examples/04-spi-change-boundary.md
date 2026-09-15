# Example 4 — Changing the Cache SPI itself

## Prompt

> While wiring the cache, add a `compareAndSwap` default method and a `touch(key)` operation to the Cache interface so every runtime gets them.

## What the skill should do

1. Recognize the boundary: the `Cache` interface is a `ddd4j-core` SPI contract shared by all runtimes; adding methods to it is a core change, not a Javalin cache-wiring task.
2. Hand off the SPI change to `ddd4j-core`, noting the responsibilities it implies: contract definition, default-method semantics, and which implementations must override what.
3. Keep this skill's scope: after the core contract changes, wire the Javalin cache providers to implement it, register lifecycle ownership, and run contention tests on each line.
4. Warn about the specific trap this skill already knows: new default methods that adapters do not override surface as runtime `UnsupportedOperationException`, so the SPI change must land first and per-line implementations after.

## Expected output

```
Routing: Cache SPI changes belong to ddd4j-core (framework-agnostic contract).
Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core

Then this skill takes the Javalin side, per line (6.7.x/7.1.x/7.2.x):
  - Implement compareAndSwap/touch in the Javalin cache providers
  - Prove CAS semantics against the real shared backend
  - Keep lifecycle registration and idempotent close intact

Note: unoverridden default methods on the Cache SPI surface as
UnsupportedOperationException at first use — implement, don't inherit.
```

## Failure the skill must avoid

Editing the Cache interface "just while wiring" and shipping the new methods as inherited defaults. The Javalin module compiles, then the first `compareAndSwap` call in production throws — a core contract change smuggled through a runtime adapter task.
