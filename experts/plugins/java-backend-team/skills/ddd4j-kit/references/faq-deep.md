# Deep FAQ

> Collection date: 2026-09-11.

1. **Does `JacksonKit` still exist?** Its capability has been merged into `JsonKit`.
2. **Are the default mapper and Redis mapper the same?** No.
3. **Can the Redis mapper handle external JSON?** No — it should not.
4. **Why does event serialization avoid `DefaultTyping`?** To prevent arbitrary-class polymorphic attacks.
5. **Can `BeanKit` replace `DomainObjectMapper`?** It cannot guarantee domain semantics.
6. **How do I choose between `StrKit` and Spring `StringUtils`?** Inside ddd4j prefer the current Kit contract; in the adapter layer respect the framework boundary.
7. **What if a utility returns `null`?** Read the specific signature and tests; do not guess.
8. **Can Kit access a database?** It must not own that resource lifecycle.
9. **Are the utility signatures consistent across old lines?** Not guaranteed.
10. **When should I add a new utility?** When multiple modules reuse it, the semantics are stable, and boundary tests exist.
