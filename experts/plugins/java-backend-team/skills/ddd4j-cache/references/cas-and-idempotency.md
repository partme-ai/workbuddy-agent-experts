# CAS and Idempotency

> Collection date: 2026-09-11.

Core provides AtomicCache, CasCache, CASOperation, and GetsResponse.

Cluster idempotency tests must at least cover: two independent clients contending for the same key, a single winner, re-acquisition after TTL, network failure, and retries without duplicate submission. Local synchronous or single-JVM tests cannot prove cross-instance CAS.
