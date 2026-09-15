# Example 1 — New feature module layout

## Prompt

> We're adding a notification capability to ddd4j-boot on the 3.x line. Where should the code live — a new module, the parent, or the BOM? And where does the Spring wiring go?

## What the skill should do

1. Fix the maintenance line first (version selection precedes architecture decisions).
2. Place version declarations in `ddd4j-boot-dependencies` / `ddd4j-boot-bom`, never in the concrete module.
3. Create a concrete implementation module for the capability; keep aggregator POMs separate from implementation code.
4. Put conditional wiring and lifecycle in the concrete feature module, with `@ConditionalOnMissingBean` default implementations and documented override points.
5. Confirm the Boot layer assembles ddd4j capabilities rather than copying core implementations.

## Expected output

```
Layout:
  ddd4j-boot-dependencies / ddd4j-boot-bom — version entries for the new
      client libraries (platform versions stay here, not in the module)
  ddd4j-boot-notification (new) — implementation + AutoConfiguration +
      conditional wiring + lifecycle
  samples — usage sample wired through the starter/aggregator

Rules applied:
  - Aggregator POM ≠ starter; the sample consumes the concrete module.
  - Defaults declared with @ConditionalOnMissingBean so user beans win.
```

## Failure the skill must avoid

Pinning the new client's version inside `ddd4j-boot-notification`'s own POM. Dependency overreach like this resolves locally today and produces version conflicts the moment another module pulls the same client.
