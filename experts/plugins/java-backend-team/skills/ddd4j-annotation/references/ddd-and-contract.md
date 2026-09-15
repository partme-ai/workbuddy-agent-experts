# DDD and Contract Annotations

> Collection date: 2026-09-11.

- **`Contract`** — marks another annotation as an auditable contract.
- **`BusinessType`** — business type enumeration / classification model.
- **`DDDAnnotation`** — generic DDD metadata entry point.

Do not assume `DDDAnnotation` auto-registers a Spring or CDI Bean. Runtime integration must be verified in the corresponding Runtime module.
