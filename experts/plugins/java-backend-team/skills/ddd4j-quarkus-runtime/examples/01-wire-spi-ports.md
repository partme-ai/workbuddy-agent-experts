# Example 1 — Wire the SPI ports into a Quarkus app

## Prompt

> We're on ddd4j-quarkus 3.3.x. Wire up CommandBus, DomainEventPublisher, and our SubjectProvider so controllers can use them.

## What the skill should do

1. Fix the line (3.3.x → Quarkus Platform 3.37.4 / ddd4j 2.0.x / JDK 17 / Maven 3) before quoting any registration idiom.
2. Read `runtime-quarkus` in that checkout to confirm the producer/BuildItem patterns the line actually uses.
3. Register the three SPI ports as CDI producers with explicit scopes, and wire a duplicate-registration guard so a second producer fails the build.
4. Bind request-scoped `Context` with restore on success, exception, and async completion — not just the happy path.
5. Define the verification: Arc build-time validation plus QuarkusTest suites for startup, dispatch, and shutdown.

## Expected output

```java
@ApplicationScoped
public class Ddd4jPorts {

    @Produces @Singleton
    CommandBus commandBus(CommandExecutor executor) { ... }

    @Produces @Singleton
    DomainEventPublisher domainEventPublisher(EventSink sink) { ... }

    @Produces @RequestScoped
    SubjectProvider subjectProvider() { ... }  // request-scoped, restored per path
}
```

Plus a lifecycle note: close/drain moves into a startup/shutdown observer, and the
evidence plan lists Arc validation (build), dispatch tests, and shutdown tests.

## Failure the skill must avoid

Registering the ports with Spring-style `@Component` expectations and "letting the container find them". Arc discovers beans at build time only — an unannotated or un-produced port is a build failure, not a late binding.
