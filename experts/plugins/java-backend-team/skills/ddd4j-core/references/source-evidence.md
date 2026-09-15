# Source Evidence Index

> Collection date: 2026-09-11. Always re-read the current branch the user specifies;
> historical paths are for locating symbols only.

- `ddd4j-core/.../ddd/model/AggregateRoot.java` — Active Record and Event Sourcing dual mode and the prohibition on mixing them.
- `ddd4j-core/.../cqrs/command/{Command,CommandBus,Result}.java` — write side.
- `ddd4j-core/.../cqrs/query/{Query,PersistenceQueryScope}.java` — domain queries and PO scope.
- `ddd4j-core/.../ddd/repository/{Repository,RepositoryRegistry}.java` — ORM-agnostic repository.
- `ddd4j-core/.../ddd/event/DomainEvent.java` — event metadata, publication, and replay.
- `ddd4j-core/.../context/{Contexts,ThreadContext}.java` — SPI and context.
- `ddd4j-core/src/test/java/io/ddd4j/core/arch/CoreIndependenceTest.java` — core dependency boundary.

Re-read the current branch on every use. Do not port 3.0.x Java / Jackson / API semantics directly into older lines.
