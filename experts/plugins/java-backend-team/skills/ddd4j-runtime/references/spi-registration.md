# SPI Registration

> Collection date: 2026-09-11.

Static entry points such as Contexts/Registry/SubjectKit must be registered by the runtime. Registration detects duplicates and missing entries, and uses a scope object to restore previous values. A duplicate CommandBus executor type should fail fast.
