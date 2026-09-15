# Swift migration adapter

| Java source mechanism | Swift target decision |
|---|---|
| POJO/record | struct/class chosen from value versus identity semantics; preserve schema separately |
| interface/default method | protocol, generic constraint, existential, or closure according to runtime use |
| checked exception | typed `Error` and `throws`; retain error category and causal evidence |
| `CompletableFuture` | async/await with cancellation-aware continuation or adapter |
| Reactor `Mono`/`Flux` | async/AsyncSequence only after specifying buffering, ordering, cancellation, and terminal errors |
| Jackson model | explicit Codable DTO or custom codec preserving exact keys, defaults, nulls, numbers, and bytes |
| reflection/annotations | generated metadata or explicit registry; never silently drop runtime discovery |
| `ServiceLoader` | explicit factory/provider registry with discovery and ordering tests |
| synchronized/concurrent maps | actor, lock, atomic, or isolated service selected from the original memory contract |
| ThreadLocal | task-local or explicit context only after propagation and cleanup are defined |

Record each mapping, compatibility obligation, rejected alternative, and executable evidence. Swift-native architecture may improve safety but cannot silently reduce Java features or extension points.

