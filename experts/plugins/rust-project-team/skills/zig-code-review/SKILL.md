---
name: zig-code-review
license: Apache-2.0
description: Review Zig project code for style, correctness, and logic. Invoke when reviewing PRs/diffs, assessing project conventions, or requesting a Zig-focused code quality audit.
---

# Zig Code Review

## Capability Boundaries

### ✅ Strong Suits
1. Reviewing Zig code style and consistency
2. Checking correctness and safety (error handling, memory, lifetimes)
3. Checking code structure and logic clarity
4. Zig version compatibility checks

### ⚠️ Requirements
1. Requires code to review (diff, file list, or code snippet)
2. Requires a target Zig version

### ❌ Out of Scope
1. Writing new code → use zig-0.16 skill
2. Non-Zig code review → use the appropriate language review skill

## When to use

Use this skill when the user needs to review a Zig PR/commit/diff, audit coding conventions, or check code quality.

## Data Privacy

This skill does not collect, store, or transmit any user data. All reviews happen entirely within the local conversation.

This skill reviews Zig project code for:

- Code style and consistency (project conventions + Zig style guide)
- Correctness and safety (errors, memory, lifetimes, resource cleanup)
- Code-structure and logic clarity (functions/modules responsibilities, control flow)
- Zig version compatibility pitfalls (build system, I/O, container init, removed features)

## Quick Start

**Example invocations:**
```
Review this Zig code: <paste code>
Check this diff for Zig version compatibility issues
Review this commit's Zig code quality
```

## Workflow

Step 1. **Determine review scope** — Get diff, file list, or modules to review
Step 2. **Confirm Zig version** — Check via `zig version` or project config. When reviewing code, load the matching reference file from references/.
Step 3. **Run mechanical checks** — Check formatting `zig fmt`, removed APIs, build config
Step 4. **Review logic & correctness** — Control flow, boundary checks, error propagation
Step 5. **Review resources & memory** — Allocator choice, defer/errdefer, lifetimes
Step 6. **Output structured feedback** — Use the Output Template

## When to Invoke

Invoke when the user asks to:

- Review a Zig PR / commit / diff
- Audit a Zig codebase’s coding conventions and module structure
- Review a code snippet’s logic and error-handling correctness
- Prepare code before merge or release (quality gate)

## Inputs to Ask For (if missing)

- Review scope: a diff, file list, or specific modules/functions
- Target Zig version (or confirm repo’s version; do not assume)
- Expected behavior / invariants (what must be true after the change)
- Build entry points: `build.zig`, `build.zig.zon`, main/root file locations
- Any project-specific conventions (naming, layering, error taxonomy, allocators)

## Review Workflow (Project-Level)

1. Identify the repository’s conventions
   - Directory structure: `src/`, `src/main.zig` (exe) / `src/root.zig` (lib), module layout, naming patterns
   - Error types strategy, allocator strategy, logging strategy
2. Run mechanical checks
   - Formatting (`zig fmt` expectations)
   - Compile-breaking API mismatches and removed features for the repo’s Zig version
3. Review logic and correctness
   - Control flow clarity, invariants, boundary checks, error propagation correctness
4. Review memory and resource management
   - Allocator choice, `defer` / `errdefer`, ownership, lifetime safety
5. Review public API and maintainability
   - Module boundaries, dependency direction, duplication, naming, docs/tests
6. Produce structured output (see Output Template)

## Checklist

### A. Style & Consistency (Should Be Deterministic)

- Naming matches project conventions and Zig Style Guide (types, functions, files, constants)
- Imports grouped consistently (std → third-party → local), unused imports removed
- Public symbols are intentionally exported (avoid accidental `pub`)
- Avoid “magic numbers”; encode invariants as constants or types
- No overly long functions without clear sections; extract helpers if needed

### B. Module & Responsibility Boundaries (Project Quality)

- Each module has a single responsibility and clear API surface
- No cyclic dependencies between modules; dependencies flow one way
- Shared utilities are in a well-known location, not copied across modules
- Error types are defined at appropriate boundary (library vs application)
- Configuration/schema types are centralized and reused

### C. Logic & Correctness (Most Important)

- Inputs validated at module boundaries (index bounds, nullability, ranges)
- Optional unwrapping is guarded (`if (opt) |v| ... else ...` or `orelse`)
- `@intCast`/`@floatCast`/`@ptrCast` usage is justified and safe
- `switch` is exhaustive where it must be; non-exhaustive enums handled intentionally
- No unreachable states without proof (`unreachable` must be justified)

### D. Error Handling & Resource Safety

- Error propagation is correct: `try` used where failure must bubble up
- `catch` does not hide important failures; avoid `catch unreachable` on allocs
- Partial construction uses `errdefer` to prevent leaks on mid-function failure
- Every allocation has a corresponding cleanup path
- Container lifecycle is correct (`.empty`/`.init` + proper `deinit(allocator)` where applicable)

### E. Zig Version Compatibility (Common Review Gate)

- Build system uses modern APIs (avoid outdated build fields/patterns)
- I/O uses `std.Io` patterns (avoid old `std.io` examples that no longer compile)
- Removed language features are not used (`async`/`await`, `usingnamespace`, etc.)
- Formatting follows modern formatter conventions (e.g. `{f}` where required)

### F. Concurrency (If Applicable)

- Shared mutable state guarded (mutex/atomics) with clear ownership rules
- Thread spawning/joining is paired; failure paths handled
- Atomics use appropriate orderings; avoid “default to strongest ordering” without reason

### G. C Interop (If Applicable)

- ABI is correct: `extern`, calling convention, alignment, packed-field pointer hazards avoided
- `@cImport` boundaries are controlled; headers and `-I` paths are explicit in build
- Strings and buffers respect C conventions (NUL-termination, lifetimes)

### H. Tests & Tooling

- Tests cover success + failure paths (especially parsing, IO, state transitions)
- Use the right assertions for slices/strings
- CI/build steps compile on target platforms (if cross-compiling is a goal)

## Output Template

Provide review feedback in this structure:

1. Summary
   - What the change does and overall health (1–3 sentences)
2. Blocking Issues (must fix)
   - Each item: Location → Symptom → Why it is risky → Suggested fix
3. Non-blocking Improvements
   - Refactors, naming, structure, doc improvements
4. Zig Version Notes (if relevant)
   - Any outdated patterns found and the modern replacement
5. Suggested Patch (optional)
   - Minimal change proposal for the most important item

## Local References (Vendored)

These files are copied into this skill so reviews remain useful when external sites are unavailable:

- `references/code-review.md`
- `references/style-guide.md`

## Embedded Reference Cards

Use these quick checks when you need fast feedback or when you don’t have access to external references.

### High-confidence “always flag” patterns

- `return &local_var` (dangling pointer)
- `.?` without a guarding `if` / `orelse` path (panic risk)
- `catch unreachable` on allocation / fallible ops (panic risk)
- Pointer to packed field (undefined behavior)
- Unpaired resource cleanup (`defer` missing on success path or missing `errdefer` on partial construction)

### Readability and logic structure checks

- Each function has a single responsibility and an obvious precondition/validation section
- Error paths do not bypass cleanup; early returns do not leak resources
- Branching is explicit; avoid deeply nested conditionals when a guard clause is clearer
- Boundary checks are near the boundary; do not assume inputs are valid unless enforced by types

## Audience

| User Type | Usage |
|-----------|-------|
| **Zig developers** | Self-check before commit, or review team PRs |
| **Project maintainers** | Unify team coding conventions |
| **CI pipeline** | Reference as code quality gate |

Customization:
- Specify review strictness (strict / standard / light)
- Specify focus area (security / style / full)
- Specify output format (full report / blocking only / suggestions only)

## Gotchas

1. **Confirm version before review** — Different Zig versions have significant API differences; always check the target
2. **Don't over-suggest** — Some patterns (e.g. `catch unreachable`) may be intentional design choices
3. **Project conventions first** — Always prioritize the project's existing conventions over external standards
4. **Consistent output** — Use the same output template for every review so readers find issues quickly

## FAQ

**Q: What information is needed for a review?**
A: At minimum, a Zig code snippet or diff, plus the target version.

**Q: How does this skill relate to `zig-0.16`?**
A: `zig-code-review` focuses on the review process and standards. `zig-0.16` provides language reference and API details. They complement each other.

**Q: Can you auto-fix found issues?**
A: Suggestions are provided but not applied directly. The user can confirm before applying.

