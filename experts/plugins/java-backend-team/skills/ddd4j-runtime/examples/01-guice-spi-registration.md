# Example 1 — Registering core ports in a Guice runtime

## Prompt

> Our team picked Guice for a ddd4j 2.0.x service (we don't want Spring). Show me how the Module should register CommandBus, SubjectProvider, and the Repository so the static entry points actually work.

## What the skill should do

1. Confirm the runtime port list: `CommandBus`, `DomainEventPublisher`, `SubjectProvider`, `Repository` implementations, and any `Cache` binding.
2. Structure a Guice `Module` that binds each port exactly once, in dependency order (Repository/SubjectProvider before consumers).
3. Wire duplicate detection: a second binding for the same executor type must fail at injector creation, not silently override.
4. Establish the request scope binding with restore-on-every-terminal-state.
5. Specify the runtime-testkit checks: registration, context restore, shutdown close.

## Expected output

```
GuiceModule outline:
  bind(Repository.class).to(JdbiOrderRepository.class)        // once
  bind(SubjectProvider.class).to(ShiroSubjectProvider.class)  // once
  CommandBus: register executors via a registrar executed at
  injector start; duplicate executor type → CreationException (fail fast)

Request scope: ddd4j scope object bound at filter entry, restores previous
values in finally — covers success, exception, async.

Testkit checks: Contexts.resolve(...) non-empty after startup; context
restore after forced exception; close() runs once, idempotent.
Status: plan SOURCE; testkit run NOT RUN.
```

## Failure the skill must avoid

Binding the ports in arbitrary order and assuming DI sorts it out. Guice builds the graph but does not know ddd4j's registration semantics — a `CommandBus` handler resolving before its `Repository` binding is a startup-order defect, not a DI mystery.
