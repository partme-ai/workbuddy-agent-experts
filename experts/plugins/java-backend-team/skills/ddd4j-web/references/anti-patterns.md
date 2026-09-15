# Anti-Patterns

> Collection date: 2026-09-11.

1. **Context leakage** — Only the success path cleans up. Cover exception and async paths.
2. **Hardcoded READY** — Do not skip the dependency check. Aggregate participants.
3. **Permissive CORS** — Any host in production. Use an explicit allowlist.
4. **Local idempotency impersonating cluster** — Use shared CAS.
5. **Adapter drift** — Only one runtime tested. Use the testkit to align.
