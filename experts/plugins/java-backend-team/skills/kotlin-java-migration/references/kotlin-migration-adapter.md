# Kotlin migration adapter

| Java source mechanism | Kotlin target decision |
|---|---|
| POJO/record | data/value model only if equality, mutability, copy, and Java ABI remain correct |
| interface/default method | interface, sealed contract, or function type according to runtime use |
| checked exception | typed failure contract; preserve Java ABI annotations when callers require them |
| `CompletableFuture` | `suspend` with explicit cancellation and executor semantics |
| Reactor `Mono`/`Flux` | suspend/Flow after specifying cold/hot, backpressure, ordering, and errors |
| Jackson annotations | preserve exact wire schema through verified Kotlin/Jackson configuration or explicit DTO adapter |
| reflection/annotations | explicit metadata/registry or retained JVM reflection with runtime tests |
| `ServiceLoader` | JVM service loader, DI registry, or generated registry with discovery parity tests |
| synchronized/concurrent maps | locks, atomics, channels, or concurrent collections chosen from the original memory contract |
| ThreadLocal | coroutine context only if propagation and cleanup semantics are proven |

Record the selected mapping, rejected alternatives, compatibility obligations, and executable evidence in the migration ledger. Kotlin concision is not permission to remove Java overloads, lifecycle hooks, error detail, or extension points.

