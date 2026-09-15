# Production Controls

> Collection date: 2026-09-11.

- **Idempotency** — Single-instance local and production shared CAS must be separate.
- **CORS** — Allowlist for `origin`, `credentials`, `headers`, and `methods`.
- **Limits** — Request size, timeout, rate limit.
- **Health** — Liveness checks only the process; readiness aggregates required dependencies — DB, MQ, Auth, Outbox, and so on.
