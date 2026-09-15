# Example 2 — Dependency direction review

## Prompt

> Before our architecture review board, do a read-only pass on the ddd4j-javalin 7.1.x modules. I need to know if anything depends in the wrong direction.

## What the skill should do

1. Stay read-only — review only, no edits.
2. Enumerate the modules (parent, bom, dependencies, core, ddd, auth, data, mq, web, cache, extensions, testcontainers) and read each module's POM dependencies on 7.1.x.
3. Flag any adapter module imported by core/ddd, any production module depending on testcontainers at compile scope, and any module bypassing the BOM with direct versions.
4. Verify with executed contract tests where available; mark tests that were not run as `NOT RUN`.

## Expected output

| Module | Depends on | Direction | Verdict |
|---|---|---|---|
| `web` | `core`, `ddd` | adapter → core | OK |
| `data` | `core`, `ddd` | adapter → core | OK |
| `ddd` | `auth` (runtime class) | core → adapter | VIOLATION — invert via SPI |
| `mq` | `testcontainers` (compile) | production → test support | VIOLATION — move to test scope |

Plus: what was checked and found clean, and what was not verified (for example, no runtime composition test executed).

## Failure the skill must avoid

Declaring the architecture clean because all modules compile and tests pass. Wrong-direction dependencies compile fine — that is exactly why the review must read POMs and imports, not build status.
