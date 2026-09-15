# Deep FAQ

> Collection date: 2026-09-11.

1. **Plan first or implement first?** When the user requests plan priority, update the existing fact source and wait for explicit approval.
2. **Can the three branches share an implementation?** Share the behavior contract; code must adapt to Javalin/JDK/Maven differences.
3. **What if a required participant fails?** Startup or readiness fails according to the approved contract.
4. **What if an optional participant fails?** Return an explicit degraded status; never silently report READY.
5. **When is Caffeine acceptable?** Single-instance or development mode, with explicit configuration.
6. **Can CORS use anyHost?** Production should not; configure origins, credentials, methods, and headers.
7. **What happens to hooks after a normal stop?** Remove them or prove they do not accumulate; close must be idempotent.
8. **Is Actions blocked by billing a code failure?** No — mark infrastructure BLOCKED.
9. **Does a local publication turn CI green?** No — the two are independent gates.
10. **How is a private publication proven?** Full deploy success, remote metadata/checksums, and isolated clean-cache consumption.
