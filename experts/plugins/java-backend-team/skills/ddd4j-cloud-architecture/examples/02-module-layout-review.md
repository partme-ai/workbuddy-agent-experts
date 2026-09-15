# Example 2 — Read-only module layout review of a fork

## Prompt

> Our fork of ddd4j-cloud has grown four custom modules over two years. Review the layout against the canonical structure before we attempt a re-merge.

## What the skill should do

1. Stay read-only — produce findings, not changes.
2. Confirm the branch, SHA, and CodeGraph freshness so the review reflects the actual tree.
3. Compare the fork's module set against parent, bom, dependencies, extensions, compatibility-tests, verification, samples.
4. Flag naming violations (any `cmpt` survivors), misplaced modules, and extensions that re-pin managed versions.
5. Check that fork changes did not break the Context/Tenant restoration coverage across sync, async, Reactor, and Feign paths.

## Expected output

| Module | Canonical slot | Verdict | Note |
|---|---|---|---|
| `<fork module A>` | extensions | OK | follows naming |
| `<fork module B>` | — | VIOLATION | old cmpt naming |
| `<fork module C>` | verification | DRIFT | consumer missing |

Plus: upstream dependency list per extension, tests executed (if any were requested) or an explicit "no tests run — read-only review", and risks with proposed fixes.

## Failure the skill must avoid

Reporting "the layout looks fine" from module names alone. The re-merge will break on the things names do not show: re-pinned versions, `cmpt` transitive references, and missing verification consumers.
