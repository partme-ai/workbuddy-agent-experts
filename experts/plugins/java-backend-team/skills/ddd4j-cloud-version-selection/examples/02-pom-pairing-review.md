# Example 2 — Read-only POM pairing review

## Prompt

> Before our upgrade window, review our service POM. We believe we're on the 2021.0.x line but someone bumped Boot last month and I don't trust the pairing anymore.

## What the skill should do

1. Stay read-only — this is a review request; do not modify any POM.
2. Extract the Spring Cloud version, Boot parent, and ddd4j coordinates from the service POM.
3. Compare the triple against the 2021.0.x matrix entry and flag any deviation.
4. Check for old `cmpt` artifact references anywhere in the dependency tree.
5. Grade each finding with its evidence state instead of asserting "the POM is fine".

## Expected output

| Check | POM says | Matrix says | Verdict |
|---|---|---|---|
| Spring Cloud | 2021.0.x | 2021.0.x | OK |
| Boot parent | <declared> | <expected from matrix> | <OK / DRIFT> |
| ddd4j line | <declared> | <expected from matrix> | <OK / DRIFT> |
| Naming | — | extensions canonical | <OK / old cmpt found> |

Each non-OK row carries the offending POM path and a proposed fix, plus an explicit note that no build or runtime verification was executed.

## Failure the skill must avoid

Declaring the pairing correct after only reading version numbers that "look right". A Boot parent bumped independently of the matrix is exactly the drift this review exists to catch, and it must be reported even when the build currently succeeds.
