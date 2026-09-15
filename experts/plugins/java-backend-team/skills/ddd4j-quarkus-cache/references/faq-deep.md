# Deep FAQ

> Collection date: 2026-09-11.

1. **What is chosen first?** The maintenance line.
2. **Is 4.0.x Quarkus 4?** No.
3. **Why are runtime/deployment separate?** It is the Quarkus build-time model.
4. **What happens to a class without a CDI scope?** Arc may not discover it.
5. **Can a BOM create beans?** No.
6. **Why is Docker detection special?** Quarkus uses multiple classloaders.
7. **Does a native test equal a JVM test?** No.
8. **How is a Security skip reported?** SKIPPED, as a risk.
9. **Can OIDC configuration be printed?** Secrets must be redacted.
10. **What is the completion evidence?** Current-line source plus the matching test/release tiers.
