# Anti-Patterns

> Collection date: 2026-09-11.

1. **Domain equals PO** — Framework annotations pollute the aggregate. Map explicitly.
2. **Fake transactions** — EventStore or Outbox commit independently. Share a transaction entry point.
3. **Concurrent position conflict** — `MAX(position)+1`. Use an atomic allocator.
4. **Lost projections** — Cursor before view. Guarantee the commit order.
5. **Database false-green** — Only H2 or mock. Use real dialect containers.
