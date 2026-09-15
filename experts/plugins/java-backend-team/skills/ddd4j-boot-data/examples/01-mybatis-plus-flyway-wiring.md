# Example 1 — MyBatis-Plus + Flyway wiring

## Prompt

> Set up persistence for our Boot 3 ddd4j service: the team is a MyBatis-Plus shop, we want Flyway-managed schema, and the domain's Repository SPI needs a working implementation.

## What the skill should do

1. Fix the maintenance line, then read the data AutoConfiguration and Properties on that line.
2. Select MyBatis-Plus as the access implementation and confirm the Flyway wiring and the registered transaction manager.
3. Register the concrete `Repository` implementation that satisfies the domain's `Repository` SPI for aggregates.
4. Verify the wiring semantics: defaults guarded by `@ConditionalOnMissingBean`, off switch skips assembly, resources have owners with idempotent close.
5. Prove with a real database round-trip plus a transaction commit/rollback test — not just a started context.

## Expected output

```
Selection: MyBatis-Plus (access) + Flyway (schema) on line 3.x.

Wiring:
  - configuration prefix per the line's Properties
  - SqlSessionFactory / transaction manager assembled by the boot data
    module, defaults user-overridable via @ConditionalOnMissingBean
  - MybatisAggregateRepository registered as the Repository impl

Verification:
  context test              PASS
  aggregate save/load       PASS (real DB)
  rollback on exception     PASS
  flyway migrate (up)       PASS   down: NOT RUN — flagged

Evidence: SOURCE + behavior TEST RUN. CI: NOT RUN.
```

## Failure the skill must avoid

Stopping at "the context started, so persistence works." A green context with no round-trip proves bean wiring only — the first aggregate save is where mapper scanning and transaction binding actually break.
