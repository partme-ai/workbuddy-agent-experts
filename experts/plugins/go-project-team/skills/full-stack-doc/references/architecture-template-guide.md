# Architecture Template Guide

## Purpose

This guide explains how to use the complete architecture template and its composable profiles. It was synthesized from 20 bilingual or Chinese/English architecture documents totaling approximately 17,654 lines across full runtimes, JVM platforms, plugin ecosystems, edge nodes, embedded devices, local Python nodes, message adapters, RAG components, monitoring integrations and enterprise channels.

The goal is not to reproduce any source project's metaphor, name or directory. The reusable value is the structure used to turn architecture intent into verifiable implementation, operations and evolution contracts.

## Template family

| Resource | Responsibility |
|---|---|
| [`架构设计文档模板.md`](../templates/architecture/架构设计文档模板.md) | Complete technology-neutral architecture baseline |
| [`profiles/README.md`](../templates/architecture/profiles/README.md) | Profile selection, combination and conflict rules |
| Runtime/application profile | Process, module, bootstrap, concurrency and deployment profiles |
| Plugin/extension profile | Extension points, manifests, lifecycle, isolation and compatibility |
| Edge/embedded profile | Hardware budgets, local autonomy, HAL, OTA and reconnect behavior |
| Message/event profile | Topic, Schema, ACK, ordering, idempotency, DLQ and backpressure |
| AI/Agent/RAG profile | Agent main chain, deterministic boundaries, context, memory, tools and evaluation |
| Observability/control-plane profile | Telemetry, cardinality, desired/actual state, command receipts and drift |

## Mandatory output filename

Architecture documents generated from this family must use one of two suffixes:

```text
<Stem>-Architecture.md
<Stem>-Architecture.zh_CN.md
```

Rules:

1. Use `-Architecture.md` for English or the repository's default language.
2. Use `-Architecture.zh_CN.md` for Simplified Chinese.
3. Keep paired-language stems identical, including case.
4. Put component, profile, platform, or version qualifiers before `-Architecture`.
5. Use `Architecture` with an uppercase `A`; use `zh_CN` exactly with an underscore.

Valid examples:

```text
ExamplePlatform-Architecture.md
ExamplePlatform-Architecture.zh_CN.md
ExamplePlatform-Gateway-Architecture.md
ExamplePlatform-Gateway-Architecture.zh_CN.md
ExamplePlatform-V2-Architecture.zh_CN.md
```

Invalid examples:

```text
ExamplePlatform-Architecture_CN.md
ExamplePlatform-Architecture.zh-CN.md
ExamplePlatform-architecture.md
ExamplePlatform-架构设计.md
Architecture.md
```

Validate output names before delivery:

```bash
python3 scripts/validate_architecture_filenames.py \
  docs/ExamplePlatform-Architecture.md \
  docs/ExamplePlatform-Architecture.zh_CN.md
```

## What the corpus consistently did well

### 1. Start with non-negotiable architecture drivers

Strong documents did not begin with framework inventories. They first stated why the system exists, its product/system subject, non-negotiable goals, compatibility obligations, platform constraints and explicit non-goals.

Reusable pattern:

```text
problem and audience
  → non-negotiable goals
  → hard constraints
  → architecture response
  → implementation location
  → acceptance evidence
```

### 2. Separate target, current skeleton and platform boundary

This three-part status pattern prevented a roadmap from being mistaken for implementation:

| View | Question |
|---|---|
| Target state | What contract should eventually hold? |
| Current skeleton | What modules, paths, tests and runtime behavior exist now? |
| Platform boundary | What is intentionally delegated, cut, unsupported or impossible here? |

Use it for every complex or partially implemented capability, not only once at document level.

### 3. Map concepts to concrete modules

A principle becomes actionable only when the document maps it to components, modules, contracts, state ownership, protocols and tests. Avoid architecture metaphors that do not constrain dependency direction or runtime behavior.

### 4. Document complete flows

The strongest documents described multiple flows rather than one happy path:

- inbound and outbound;
- synchronous and asynchronous;
- data, control and observability;
- success, validation failure, timeout, retry, cancellation and recovery;
- local execution and upstream delegation;
- startup, steady state, drain, shutdown, upgrade and rollback.

### 5. Make constraints measurable

Resource-constrained documents converted platform identity into CPU, RAM, Flash, queue, task, connection, power and network budgets. Server documents used concurrency, latency, throughput, queue and state budgets. Monitoring documents constrained label cardinality and telemetry buffers.

### 6. Treat operations as architecture

Startup reports, health semantics, doctor/status commands, configuration precedence, migration dry-runs, upgrade and rollback, diagnostics, logs, metrics, traces and audit were part of the architecture contract rather than an afterthought.

## Common architecture reading path

```text
Document control and status
  → executive summary
  → drivers, constraints and non-goals
  → context and trust boundary
  → current state, target state and gaps
  → principles and ADRs
  → layers, components and dependencies
  → runtime and core flows
  → state, data, protocols and configuration
  → security, reliability and resource budgets
  → deployment, operations and extensions
  → compatibility, validation, risks and roadmap
```

## Evidence mapping

| Architecture claim | Preferred evidence |
|---|---|
| Modules and dependency direction | Build manifests, workspace files, source imports, architecture tests |
| Runtime processes and lifecycle | Entrypoints, bootstrap code, process manifests, runtime traces |
| Configuration and defaults | Schema, loaders, environment mapping, startup output |
| Data ownership and consistency | Schemas, repositories, transactions, outbox/inbox and state tests |
| Protocol and error semantics | Schema files, public types, handlers, contract tests |
| Security and permissions | Policy code, manifests, sandbox config, threat tests |
| Failure and recovery | Retry/replay code, chaos tests, runbooks, incident evidence |
| Performance and resource claims | Reproducible benchmark/load commands and target hardware |
| Deployment and compatibility | Deployment manifests, CI matrices, migration/upgrade tests |
| Current implementation status | Source, tests, release artifacts and actual runtime output |

## Diagram strategy

Every diagram needs a question. Prefer the smallest diagram that answers it:

| Question | Diagram |
|---|---|
| Who is outside/inside the system? | Context flowchart |
| What are the layers or component dependencies? | Container/component flowchart |
| What happens across participants over time? | Sequence diagram |
| Which transitions are legal? | State diagram |
| Who owns which data? | ER/data ownership diagram |
| Where do processes and state run? | Deployment diagram |
| What happens under failure/retry? | Failure flow or state diagram |

Use fenced `text` for a first-screen view and portability. Use Mermaid for deeper flow, sequence, state, dependency and deployment relationships. A diagram does not replace the adjacent responsibilities, constraints and failure table.

## Architecture document levels

| Level | Owns | Must not duplicate |
|---|---|---|
| Product architecture baseline | Cross-version boundaries, principles, target topology and contracts | Release-specific implementation detail |
| Version architecture delta | Changes from the baseline, migration and version acceptance | The entire product architecture |
| System/component architecture | One deployable or bounded component's internals and external contracts | Organization-wide product strategy |
| Protocol/API specification | Field-level Schema, errors and examples | Broad system narrative |
| Deployment/runbook | Environment operations, commands and incident procedures | Design rationale already owned by architecture/ADR |

The standalone complete template can produce a system or component architecture document. When used inside the 10-document product baseline, link detailed component/protocol/runbook material rather than duplicating it.

## Project-type profile selection

Choose the primary profile by the system's main runtime responsibility, then add only real cross-cutting profiles:

```text
Server/JVM/native/local runtime?     → runtime/application
Loaded through a host contract?      → plugin/extension
Hardware or strict resource budget?  → edge/embedded
Broker, stream or event semantics?   → message/event
Model, Agent, tool, memory or RAG?    → AI/Agent/RAG
Telemetry, policy or desired state?  → observability/control plane
```

## Content preservation

When standardizing an existing architecture document:

1. Inventory all original sections, diagrams, contracts, examples and appendices.
2. Label current, target, partial and non-goal content before reordering.
3. Move details under the common reading path; do not delete unique protocol, failure, resource or security material.
4. Split field-level specs and runbooks only when links and ownership remain clear.
5. Preserve stable historical anchors when other documents depend on them.
6. If generation is automated, manage a bounded block and verify idempotence on the second run.

## Quality rubric

| Dimension | Pass condition |
|---|---|
| Drivers | Architecture choices trace to business, quality, compatibility or platform constraints |
| Honesty | Current, partial, target and non-goal states are distinguishable |
| Boundaries | Responsibilities, dependencies, trust and state ownership are explicit |
| Runtime | Processes, concurrency, lifecycle and core flows are understandable |
| Data/protocol | Authority, consistency, versioning, errors, ACK/idempotency are defined |
| Security | Assets, threats, identity, permission, secrets and isolation are covered |
| Reliability | Failure detection, retry, degradation, replay, recovery and rollback are testable |
| Resources | Latency, throughput, memory, queues, storage or hardware limits have budgets |
| Operations | Startup, health, diagnostics, observability, migration and upgrade are executable |
| Evolution | ADRs, compatibility, risks, debt, stages and reversal conditions are recorded |
| Evidence | Key claims point to source, tests, manifests, commands or runtime evidence |

## Final checks

- Output basename matches `*-Architecture.md` or `*-Architecture.zh_CN.md`
- One H1 outside code fences
- Balanced fenced blocks with language labels
- No unresolved machine placeholders in delivered documents
- No private project names, local absolute paths, credentials or production endpoints
- Current and target diagrams are not mixed without labels
- Every main flow includes failure and recovery semantics
- Numeric claims identify target versus measurement and include evidence
- Relative links resolve in both language variants
- Architecture terminology matches manifests, source, protocols, configuration and deployment
- `git diff --check` passes
