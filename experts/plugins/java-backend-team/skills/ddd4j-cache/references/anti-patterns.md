# Anti-Patterns

> Collection date: 2026-09-11.

1. **Local as cluster**: Caffeine used for multi-instance idempotency; switch to shared CAS.
2. **Non-atomic composition**: get+put; use the atomic interfaces.
3. **Key secrets**: keys containing tokens/phone numbers; use hashes or internal IDs.
4. **Cache as authority**: no source-of-truth fallback/recovery; define data authority.
5. **False green tests**: mocking Redis; add real containers.
