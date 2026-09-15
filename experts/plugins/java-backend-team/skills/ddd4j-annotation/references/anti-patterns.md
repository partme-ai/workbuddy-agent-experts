# Anti-Patterns

> Collection date: 2026-09-11.

1. **Annotation equals implementation** — Adding `@ApiIdempotent` does not prove idempotency. Verify the consumer.
2. **Framework semantics projected** — Assume every `RUNTIME` annotation is a Bean. Check the registrar.
3. **Field metadata leakage** — Domain references PO annotations. Isolate via mapping.
4. **Cross-line copy** — High-line annotation attributes copied to old lines verbatim. Recompile per line.
5. **No behavior tests** — Only test that reflection finds the annotation. Add adapter behavior tests.
