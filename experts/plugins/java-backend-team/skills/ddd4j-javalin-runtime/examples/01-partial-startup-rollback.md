# Example 1 — Rollback after partial startup failure

## Prompt

> On our 7.2.x service, if the MQ listener registration fails midway through startup, we end up with an open connection pool and a half-bound web server. How should the runtime handle this?

## What the skill should do

1. Confirm the line (7.2.x → Javalin 7.2/ddd4j 3/JDK 21/Maven 4) and locate `Ddd4jJavalinRuntime` plus the participant registration sites.
2. Make initialization transactional in spirit: record each successfully initialized `JavalinLifecycleParticipant`, and on failure close only those, in reverse registration order.
3. Ensure the failed participant is not closed (it never finished initializing) and that the original failure is rethrown, not swallowed by the rollback.
4. Write the failing contract first: a test where the third participant throws must assert the first two closed in reverse order and nothing else.

## Expected output

```java
// start() records participants as they initialize
initialized.add(dataParticipant);      // 1st — closed last
initialized.add(mqParticipant);        // 2nd — throws in initialize()

// on failure:
for (int i = initialized.size() - 1; i >= 0; i--) {
    initialized.get(i).close();        // data closed after mq attempt aborts
}
throw startupFailure;                  // original cause preserved
```

Plus the test evidence: red contract first (current code leaks the pool), green after the fix, and the remaining gap (no Testcontainers run against a real broker yet).

## Failure the skill must avoid

Swallowing the MQ failure inside a broad try/catch "so the service still starts". Partial startup must roll back initialized resources in reverse order and fail loudly — a half-bound web server that looks alive is the worst outcome.
