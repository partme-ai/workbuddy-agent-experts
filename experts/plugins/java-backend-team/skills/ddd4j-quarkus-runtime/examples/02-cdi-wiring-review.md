# Example 2 — Read-only CDI wiring review

## Prompt

> Before we cut the release, review our ddd4j-on-Quarkus wiring read-only. I care about scopes, duplicates, and lifecycle ownership.

## What the skill should do

1. Stay read-only and fix the line/SHA first.
2. Enumerate every producer for `CommandBus`, `DomainEventPublisher`, and `SubjectProvider`; flag duplicates (ambiguous resolution) and scope mistakes.
3. Trace `Context` bind/release pairs and check all three exit paths: success, exception, async completion.
4. Check startup/shutdown observers own resource lifecycle; flag resources opened in constructors.
5. Verify readiness aggregates from real dependencies rather than a constant.

## Expected output

| Check | Finding | Verdict |
|---|---|---|
| CommandBus producers | one `@Produces @Singleton` | OK |
| DomainEventPublisher producers | two producers (main + test module leaked into prod) | **DUPLICATE** |
| SubjectProvider scope | `@RequestScoped`, correct | OK |
| Context release | release in `finally`; async path missing restore | **GAP** |
| Lifecycle | broker client opened in constructor; no shutdown observer | **GAP** |

Evidence: SOURCE read of wiring classes. QuarkusTest suites NOT RUN on this SHA.

## Failure the skill must avoid

Passing the review because the application boots. Duplicate producers and a missing async restore only fail under specific builds or concurrent load — the review must inspect registration and exit paths, not just startup success.
