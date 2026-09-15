# README Template Guide

## Purpose

This guide explains how to select and adapt the README template family without forcing every project into one document shape. The family was synthesized from a broad local corpus covering skill catalogs, Java and DDD multi-module frameworks, libraries and SDKs, CLI applications, Rust crates, sample applications, and plugin monorepos.

The reusable conclusion is simple: a README is an executable entry point for a new reader. It should establish the correct mental model, get one real path working, expose boundaries and failure modes, and route deeper design material to dedicated documents.

## Evidence from the corpus

The audit reviewed 603 `README.md` and `README.zh-CN.md` files after excluding generated build directories. Common sections appeared with very different frequency, so frequency alone is not a quality signal:

| Content family | Observed role |
|---|---|
| Positioning and introduction | Explains what the project is, for whom, and why it exists |
| Installation and quick start | Provides the shortest verified success path |
| Features and usage examples | Maps user problems to supported capabilities |
| Architecture and module structure | Builds a correct mental model before configuration or extension |
| Configuration | Defines entry points, precedence, defaults, secrets, and complete examples |
| Development and verification | Makes source builds and quality gates reproducible |
| Operations, security, and troubleshooting | Separates production use from demo-only instructions |
| Compatibility, release, contribution, support, and license | Sets lifecycle and governance expectations |

The strongest component READMEs used a fixed early reading path:

```text
Positioning
    │
At a glance
    │
Architecture and core flow
    │
Capabilities and boundaries
    │
Quick start
    │
Configuration
    │
Operations and troubleshooting
    │
Verification and deep links
```

This pattern is retained across the template family. Detailed reference sections follow it and may be removed when not applicable.

## Template family and selection

Do not copy the largest template by default. Select the closest project type first, then borrow an exceptional section from the complete reference only when repository evidence makes it necessary.

| Template | Direct-use target | Distinctive content |
|---|---|---|
| [`README-Java项目模板.md`](../templates/readme/README-Java项目模板.md) | Java library, SDK, starter, framework, or Maven multi-module project | JDK/Maven baseline, BOM, module boundaries, Starter/auto-configuration, configuration prefix, version lines, Maven gates |
| [`README-Rust项目模板.md`](../templates/readme/README-Rust项目模板.md) | Rust crate or Cargo workspace | Common Rust core plus composable [domain profiles](../templates/readme/rust-profiles/README.md): crate map, features, MSRV/edition, targets, `unsafe`/FFI, Cargo gates, formats, parity, toolboxes, security frameworks and design-stage projects |
| [`README-插件项目模板.md`](../templates/readme/README-插件项目模板.md) | Host plugin, channel connector, protocol adapter, or event bridge | Plugin identity, host compatibility, lifecycle, input/output contract, ACK, retry, idempotency, state and recovery |
| [`README-技能包与生态目录模板.md`](../templates/readme/README-技能包与生态目录模板.md) | Agent Skill package, catalog, marketplace, or navigation hub | Installation matrix, skill catalog, triggers, supported agents, progressive loading, package audit and evaluation |
| [`README模板.md`](../templates/readme/README模板.md) | Unclassified project, service, CLI, desktop app, example app, or section source library | Complete 25-section reference with development, deployment, operations, governance, API and lifecycle material |

Selection flow:

```text
Does the repository expose a Cargo crate/workspace? ── yes ──► Rust template
                         │ no
Does it expose Maven/Gradle Java modules? ─────────── yes ──► Java template
                         │ no
Is it loaded by a host through a plugin contract? ── yes ──► Plugin template
                         │ no
Is its primary product a set/catalog of Agent Skills? yes ─► Skill ecosystem template
                         │ no
                         └───────────────────────────────► Complete reference template
```

For hybrid repositories, choose by the reader's main success path. A Java host plugin should usually start from the plugin template and borrow verified Java build sections; a Rust CLI should start from the Rust template and borrow command reference or distribution sections from the complete reference.

## Required first-screen questions

A new reader should answer these questions without scrolling through implementation history:

1. What is this project?
2. Who should use it, and what problem does it solve?
3. What is the supported and unsupported boundary?
4. What input enters, what processing happens, and what output leaves?
5. What is the shortest verified path to success?
6. Which runtime, package, version, and license apply?
7. Where should the reader go for configuration, API, security, and deeper architecture?

## Project-type selection matrix

Use the specialized template when one matches. Use the complete reference as a source library for the remaining project types.

| Project type | Must keep | Usually keep | Usually remove or shorten |
|---|---|---|---|
| Repository catalog or ecosystem hub | Use the skill/ecosystem template when the catalog contains Agent Skills; otherwise keep positioning, catalog, install matrix, package organization, discovery, contribution, license | Architecture of the ecosystem, supported clients, migration notice | Low-level API, deployment topology |
| Library or SDK | Requirements, installation, minimal example, API entry points, error model, compatibility, tests, release policy | Architecture, extension points, performance, security | End-user deployment and operations unless the library owns a runtime |
| Java multi-module framework | Use the Java template: positioning, architecture layers, dependency rules, module matrix, BOM/version line, quick start, sample application, architecture tests | Runtime adapters, migration, extension SPI, compatibility matrix | Marketing-oriented use-case lists |
| Rust crate or workspace | Use the Rust template: package status, crate map, features, MSRV/edition, targets, unsafe policy, examples, Cargo gates and publication | Backends, benchmarks, provenance, migration and FFI | Runtime deployment unless the workspace owns a service |
| Plugin or adapter | Use the plugin template: component identity, host compatibility, input/process/output, responsibilities, install, config path, security, recovery, verification | Protocol semantics, retries, idempotency, observability, examples | Broad ecosystem catalog except direct dependencies |
| CLI or desktop application | Demo, install methods, commands, configuration, platform support, data paths, troubleshooting, upgrade/uninstall | Architecture, keyboard shortcuts, SDK embedding | Package API details when no public SDK exists |
| Service or deployable application | Requirements, architecture, configuration, deployment, health checks, observability, backup, rollback, security | API, scaling, disaster recovery, SLOs | Package-manager-specific library instructions |
| Example application | Scenario, prerequisites, exact run commands, expected output, exercised capabilities, cleanup | Directory map, debugging, known limitations | Governance, roadmap, large architecture manifesto |
| Skill package | Use the skill/ecosystem template: positioning, install command, skill catalog, supported agents, package organization, quality checks, ecosystem, license | Trigger examples and per-skill quick usage | Runtime deployment and operational SLOs |

## Type-specific evidence

### Java

Verify coordinates and versions from `pom.xml`, Gradle files, wrapper properties, Maven Enforcer rules and CI. A directory name is not proof that a module is published. Distinguish BOM, API, core, adapter, starter, runtime and sample modules; document dependency direction and the configuration prefix from source. If multiple maintained branches target different Java or framework baselines, provide a version-line matrix.

### Rust

Verify crate names, versions, workspace members, default features, `rust-version`, edition and resolver from Cargo manifests and CI. Check crate roots for `unsafe` policy, `no_std`, feature gates and public exports. Distinguish implemented, experimental and planned capabilities. If no `Cargo.toml` or published artifact exists, mark the project as design-stage and remove crates.io badges, install commands and test claims.

The Rust template is intentionally two-layered:

1. Start with the common [`README-Rust项目模板.md`](../templates/readme/README-Rust项目模板.md).
2. Use the [`rust-profiles` selector](../templates/readme/rust-profiles/README.md) to add only the applicable domain sections.

| Rust project characteristic | Profile to add |
|---|---|
| Spreadsheet, office document, PDF, fixed-layout document, image or archive processing | Document and file-format profile |
| Behavioral port or compatibility layer for an upstream implementation | Upstream compatibility and migration profile |
| Many domain crates behind a facade and feature matrix | Large toolbox workspace profile |
| Authentication, tokens, sessions, authorization or web middleware | Authentication and security framework profile |
| Architecture and plans exist but no buildable workspace exists | Design-only stage profile, replacing install/test/release sections |
| More than one README language | Multilingual layout profile |

A project may combine profiles. For example, a document-processing compatibility port normally uses the common template plus the document-format, upstream-compatibility and multilingual profiles.

### Plugin

Verify plugin ID, entrypoint, permissions and host compatibility from the manifest and host SDK. Trace inbound input, lifecycle, target calls, acknowledgements and outbound results. Document who owns authentication, retry, deduplication, state and cleanup. Compatibility means tested host/API combinations, not merely syntactic build success.

### Skill package or catalog

Verify skill count from directories and market manifests. Distinguish catalog-only repositories from repositories that contain skill source. Each skill entry should describe when it activates, not only what it is called. Validate referenced files, scripts, installation methods, adapter output, supported agents and idempotent generation.

## Single-source-of-truth mapping

Do not manually copy facts that can drift. Derive or verify them from the actual project:

| README fact | Preferred evidence |
|---|---|
| Package name and version | Package/build manifest or release metadata |
| Runtime and toolchain versions | Build manifest, toolchain file, CI matrix |
| Modules and dependency direction | Workspace/build files and source tree |
| Public API and usage | Exported source, generated API docs, compile-tested examples |
| Configuration keys and defaults | Configuration schema and runtime loaders |
| Environment variables | Source and deployment manifests |
| Compatibility | CI matrix and compatibility tests |
| Test, lint, build, and release commands | Repository scripts and CI workflows |
| License | Repository license file |
| Support and security channels | Governance and security policy files |

When facts cannot be verified, label them **Assumption**, **Inference**, or **TBD**. Never make a badge claim stronger than the underlying evidence.

## Diagram strategy

Use a fenced `text` diagram for the first-screen architecture because it renders consistently in Git hosts, package registries, terminals, and offline viewers. It must show input, project boundary, major stages, and output.

Use Mermaid later only when it materially improves a complex relationship such as module dependency, sequence, state transition, deployment topology, or release flow. The README should remain understandable if Mermaid does not render.

## Bilingual strategy

For projects with `README.md` and `README.zh-CN.md`:

1. Keep equivalent top-level sections and navigation order.
2. Keep commands, package names, versions, IDs, paths, and configuration keys identical.
3. Translate explanations, not identifiers.
4. Avoid one language file being only a redirect when the other contains the actual documentation.
5. Validate anchors and relative links independently for both files.

## Content preservation strategy

When standardizing an existing README:

1. Inventory original headings, tables, examples, FAQ, configuration, protocol notes, and troubleshooting content.
2. Insert or reorder the common reading path.
3. Move detailed original material under the appropriate section instead of deleting it.
4. If generation is automated, manage only a clearly marked standard block and preserve content outside it.
5. Run the generator twice; the second run must produce no changes.

## Completion rubric

| Dimension | Pass condition |
|---|---|
| First-screen clarity | Positioning, audience, value, boundary, and navigation are immediately visible |
| Reproducibility | A clean environment can follow the quick start and observe the documented result |
| Architecture | Input, output, project boundary, modules, dependency direction, and failure path are understandable |
| Configuration | Entry point, precedence, defaults, secrets, validation, and full examples are covered |
| Evidence | Versions, commands, compatibility, status, coverage, and performance claims are traceable |
| Operations | Health, logs, metrics, backup, rollback, upgrade, and troubleshooting are covered when applicable |
| Security | Trust boundary, credential handling, disclosure path, and unsafe defaults are explicit |
| Lifecycle | Compatibility, release policy, roadmap/status, contribution, support, and license are discoverable |
| Maintainability | Facts come from stable sources; bilingual files and generated sections can be checked for drift |

## Final checks

- One H1 outside code fences
- Balanced code fences with language labels
- No unresolved machine placeholders in the delivered README
- No private names, absolute local paths, tokens, credentials, or sample passwords
- Every relative link resolves in its intended publishing context
- Commands use a clean environment and include expected results
- Badges reflect verified current facts
- Optional sections were removed when they add no reader value
- The first-screen text diagram remains readable at narrow widths
- `git diff --check` passes
