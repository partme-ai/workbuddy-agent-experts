# Ownership and Imports

> Collection date: 2026-09-11.

- **`ddd4j-parent`** — plugin management, build, test, and publish conventions.
- **`ddd4j-dependencies`** — third-party library versions and necessary replacement coordinates.
- **`ddd4j-bom`** — the consumer-facing collection of ddd4j artifact versions.
- **Adapter `dependencies` / BOM** — owns only Boot, Cloud, Javalin, and Quarkus ecosystem dependencies.

Review order: direct declarations → parent → BOM import order → effective POM → dependency tree.
