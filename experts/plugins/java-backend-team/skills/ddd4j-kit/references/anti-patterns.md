# Anti-Patterns

> Collection date: 2026-09-11.

1. **Reinventing the wheel** — Business modules write their own string / collection / JSON utilities. Always check Kit first.
2. **Cross-scenario mixing** — Using the Redis mapper for HTTP or EventStore. Match the scenario to the mapper.
3. **Implicit domain mapping** — Bean copy obscures semantic differences. Map explicitly.
4. **Swallowed exceptions** — A utility failure returns `null`. Preserve diagnosable exceptions.
5. **Cross-line assumption** — 3.0.x utility signatures used on older lines. Verify per line.
