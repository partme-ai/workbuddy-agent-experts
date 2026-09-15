# Example 5 — H2 green, production migration red

## Prompt

> All our data tests pass on H2, but the Flyway migration failed on the first deploy to the staging MySQL database. Same code, same migrations. How is that possible?

## What the skill should do

1. Name the trap immediately: an H2 unit test does not prove production dialect behavior — H2's compatibility mode accepts SQL and types that MySQL rejects.
2. Classify the failure from the migration error: dialect-specific type (e.g. a column type H2 maps differently), reserved word, or auto-increment/charset default behavior.
3. Re-run the failing migration against a real MySQL instance locally to get the true error, not the H2-filtered one.
4. Fix at the migration level (dialect-safe DDL), never by loosening the H2 test until it passes.
5. Prescribe the durable verification: migration up/down in CI against the real engine image, with H2 kept only for fast wiring checks.

## Expected output

```
Failure: V3__add_orders.sql on MySQL 8
  H2 result:        PASS (compatibility mode accepted the DDL)
  MySQL result:     FAIL — <dialect error from the real run>

Root cause: H2 compatibility mode is not a dialect implementation; the
DDL used a construct H2 tolerates and MySQL rejects.

Fix: dialect-safe DDL in the migration; keep H2 for wiring-only tests.

Durable gate: CI runs flyway migrate + undo against a MySQL container.
Until then: dialect behavior UNVERIFIED in CI — flagged.

Evidence: SOURCE + local MySQL TEST RUN. CI gate NOT RUN.
```

## Failure the skill must avoid

"Tuning" the H2 config or the test until it passes again and shipping. The migration is still broken on the real engine — the next deploy fails exactly where this one did.
