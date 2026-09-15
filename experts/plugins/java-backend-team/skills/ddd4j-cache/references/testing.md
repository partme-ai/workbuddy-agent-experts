# Testing

> Collection date: 2026-09-11.

1. Local providers: TTL, capacity, invalidate, concurrency.
2. Redis/Memcached: real container round-trips and disconnection.
3. CAS: multi-client contention.
4. Serialization: round-trip, corrupted data, version changes.
5. Observability: hit/miss/error consistent with business state.

When Docker is unavailable or containers are skipped, mark BLOCKED/SKIPPED.
