# Anti-Patterns

> Collection date: 2026-09-11.

1. **Legacy CRUD base classes masquerading as core** — Using `io.hiwepy.boot BaseEntity`. Model against the current `AggregateRoot` / `Repository` instead.
2. **Mixed persistence tracks** — The same aggregate both calls `save()` and persists `pullDomainEvents()`. Choose one strategy per aggregate.
3. **Domain depending on frameworks** — Domain imports Spring, MyBatis, or Javalin. Isolate via the core SPI.
4. **Context leakage** — Subject is bound but never closed. Use a scope or `finally` block.
5. **False-green default methods** — Uncovered `Repository` operations assumed to work. Test the actual adapter and handle `UnsupportedOperationException`.
