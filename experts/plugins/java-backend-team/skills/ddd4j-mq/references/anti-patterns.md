# Anti-Patterns

> Collection date: 2026-09-11.

1. **Container equals success**: only starting the broker; require a round-trip.
2. **Premature ACK**: acknowledging before business processing; acknowledge after success.
3. **Infinite retries**: no backoff/dead-letter; set an upper bound.
4. **Shutdown leakage**: closing only the consumer; close every owner in reverse order.
5. **One naming for all**: reusing illegal destinations across brokers; convert per rule.
