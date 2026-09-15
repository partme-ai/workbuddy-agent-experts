# Projection

> Collection date: 2026-09-11.

**Core**: `ProjectionRunner`, `ProjectionPositionRepository`, `ProjectionService`, `ProjectionMetrics`.

**Adapters**: Spring, Javalin, Quarkus, Micronaut, Vert.x, Helidon, Dropwizard. Position storage can use JDBI / JPA / R2DBC / Panache. Read-model writes and position advancement must be idempotent and have explicit transaction boundaries.
