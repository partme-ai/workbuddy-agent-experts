# Deep FAQ

> Collection date: 2026-09-11.

1. **Can Java 8 use Boot 3?** No.
2. **Can Java 17 use ddd4j 3?** Not currently supported.
3. **What does Boot 2.7 pair with?** ddd4j 1.0.x.
4. **What does Boot 3.5 pair with?** ddd4j 2.0.x.
5. **What does Boot 4.1 pair with?** ddd4j 3.0.x/Maven 4.
6. **Can Enforcer be skipped?** Not for releases.
7. **Is a local SNAPSHOT enough?** No.
8. **Is upgrading just the parent enough?** No.
9. **What about matrix conflicts?** The current POMs and execution results win; fix the matrix.
10. **How is availability proven?** Layered evidence: build, CI, publish, clean-cache consumption.
