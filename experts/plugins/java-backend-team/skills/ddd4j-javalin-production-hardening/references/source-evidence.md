# Source Evidence Routing

> Collection date: 2026-09-11.

When using this skill, re-confirm in the target `ddd4j-javalin` checkout:

- Current branch, POM model, Maven Wrapper, JDK, and Javalin version.
- `Ddd4jJavalinApplication`, configuration objects, web lifecycle, readiness, idempotency, and CORS implementations.
- Whether `Ddd4jJavalinRuntime` and `JavalinLifecycleParticipant` exist and their test status.
- The actual owners of the JPA EntityManagerFactory, MQ, Outbox, schedulers, and shutdown hooks.
- The current fact source in `docs/superpowers/specs/`, `plans/`, and `reports/`.
- GitHub Actions required jobs for the final SHA, plus private Maven remote metadata and clean-cache consumers.

The historical matrix serves only as a locating hypothesis; it cannot substitute for current source, POM, test, CI, and remote artifact evidence.
