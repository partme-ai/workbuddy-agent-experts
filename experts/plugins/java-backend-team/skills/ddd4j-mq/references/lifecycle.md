# Lifecycle

> Collection date: 2026-09-11.

Order: validate → producer init → consumer init → listener register → ready.

On any step failure: shut down initialized resources in reverse order. Normal stop: stop receiving first, drain, then close consumer, producer, and connection. close must be idempotent.
