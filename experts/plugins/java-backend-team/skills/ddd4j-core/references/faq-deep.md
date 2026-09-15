# Deep FAQ

> Collection date: 2026-09-11.

1. **Does Active Record mean the domain depends on MyBatis?** No — call `RepositoryRegistry`.
2. **How is `EventHandler` resolved?** Current lines prefer annotations and keep the naming-convention fallback; defer to source.
3. **Why do events require a no-arg constructor?** To support Jackson deserialization and event replay.
4. **Does `source()` keep the aggregate path?** It is a string-compatible view; the full semantics live in `EntityIdPath`.
5. **Does `ThreadContext` deep-copy objects?** Currently it only duplicates the resource map; values retain references.
6. **Where does `Query.current` start?** The current source starts at 1.
7. **What does `size=-1` mean?** The current `Query` indicates no pagination; the adapter must preserve that semantics.
8. **Can core depend on Lombok or Jackson?** Defer to `CoreIndependenceTest` and the current POM allowlist.
9. **Can I apply 3.0.x conclusions to 1.0.x?** No — verify per line.
10. **When do I need a runtime skill?** When the question reaches DI, bus registration, lifecycle, or framework assembly.
