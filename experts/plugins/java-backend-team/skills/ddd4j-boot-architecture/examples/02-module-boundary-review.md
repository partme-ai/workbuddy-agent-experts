# Example 2 — Module boundary review (read-only)

## Prompt

> Our reviewer flagged that ddd4j-boot-data "knows too much". Can you do a read-only boundary review of the boot modules and tell us where the layering is broken?

## What the skill should do

1. Stay read-only; report findings, not patches.
2. Confirm the maintenance line and enumerate parent, dependencies, bom, core, auth, data, mq, web, cache, extensions, samples with file paths.
3. Flag any Boot module that re-implements or copies `ddd4j-core` semantics instead of assembling them.
4. Flag platform versions declared outside the BOM and aggregator POMs that carry implementation code.
5. Rate each finding with evidence (source read, which paths) and a proposed fix direction.

## Expected output

| Module | Finding | Why it breaks the boundary | Fix direction |
|---|---|---|---|
| `ddd4j-boot-data` | declares `mysql.version` in its own POM | Platform versions belong to the BOM | Move to `ddd4j-boot-bom` |
| `ddd4j-boot-core` | subclasses a core aggregate strategy to add Spring retries | Boot layer assembles, does not copy core | Decorate at assembly via the adapter |
| `ddd4j-boot-extensions` | aggregator POM contains helper classes | Aggregator POMs stay separate from implementations | Move classes to a concrete module |

Evidence: SOURCE (module POMs and sources read). Tests and CI NOT RUN — read-only review.

## Failure the skill must avoid

Reporting "architecture looks fine" after only listing module names. Boundary violations live in POM contents and class hierarchies, which require actually reading the sources of the target line.
