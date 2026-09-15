# Anti-Patterns

> Collection date: 2026-09-11.

1. **Scope drift**: the user asks for Javalin but the work drifts to Quarkus/generic ddd4j; keep the target repository and escalate only for proven dependency blockers.
2. **Mechanical toolchain unification**: moving 7.1.x to Maven 4; preserve the JDK/Maven/POM contract per line.
3. **Hardcoded READY**: readiness never checks dependencies; aggregate required/optional participant states.
4. **Local idempotency posing as cluster idempotency**: production multi-instance still on Caffeine; require a shared CAS implementation.
5. **Activity posing as completion**: push, CI start, or upload logs counted as success; wait for terminal states and run clean-cache consumption.
