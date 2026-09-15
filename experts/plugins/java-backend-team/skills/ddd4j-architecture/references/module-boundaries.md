# Module Boundaries

> Collection date: 2026-09-11. Always cross-check against the current root POM and CodeGraph.

- **ddd4j-annotation** — metadata only; carries no runtime implementation.
- **ddd4j-core** — framework-agnostic DDD/CQRS/Auth/Cache/Context/Health contracts.
- **ddd4j-auth / data / mq / web / cache / metrics** — capability implementations and adapter collections.
- **ddd4j-runtime** — Spring, Guice, Quarkus runtime wiring.
- **ddd4j-extensions** — Akka, Excel, Jackson, PF4J, QLExpress, and other optional capabilities.
- **ddd4j-ddd-rules** — Clean, COLA, and other architecture checks.
- **ddd4j-parent / dependencies / bom** — build and consumption governance.

When in doubt, defer to the current root POM and CodeGraph.
