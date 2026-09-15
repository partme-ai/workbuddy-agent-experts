# Anti-Patterns

> Collection date: 2026-09-11.

1. **High-cardinality labels**: user/message/sql; use stable low-cardinality dimensions.
2. **Noop false green**: claiming observability complete with no exporter; mark it degraded.
3. **Testing registration only**: never testing increments; verify behavior.
4. **Metrics as health**: readiness is judged separately.
5. **Missing exception recording**: counting successes only; cover failures.
