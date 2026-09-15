# Deep FAQ

> Collection date: 2026-09-11.

1. **Can local caches be used in development?** Yes — with non-production cluster semantics stated explicitly.
2. **Does Redis equal CAS?** No — it depends on the command/script implementation.
3. **Does Redisson always release locks safely?** Owner and exception tests are required.
4. **Is JetCache a storage engine?** It is an abstraction/multilevel capability; the underlying store still needs configuration.
5. **What unit does TTL use?** Read the specific implementation.
6. **Can a cache store DomainEvents?** Only with explicit serialization and a defined source of truth.
7. **When to degrade?** Decide fail-open/fail-closed based on business consistency.
8. **How is tenant isolation achieved?** Key namespace verified together with the context.
9. **Can full keys be logged?** Not for sensitive keys.
10. **What proves completion?** Provider behavior, real backends, concurrency, and failure tests.
