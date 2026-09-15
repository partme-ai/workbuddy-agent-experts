# Example 4 — Changing core semantics from a Boot module (boundary case)

## Prompt

> Our boot-web module needs the aggregate version check to work differently — just override the core aggregate behavior inside the boot module, it's a two-line change.

## What the skill should do

1. Decline the specific change: the Boot layer only assembles ddd4j capabilities and should not copy or alter core semantics — this is a hard rule, not a style preference.
2. Do not use a Boot module patch to modify `AggregateRoot` behavior; explain that such a change forks semantics per line and breaks every other consumer of core.
3. Offer the compliant alternatives: adjust the core contract in `ddd4j-core` (with its own line-by-line verification), or add an assembly-level decorator in the adapter layer.
4. Hand off core-contract work to the `ddd4j-core` skill with the install command.
5. Record the decision and what was not changed so the review trail is clear.

## Expected output

```
Request: override core aggregate version-check behavior inside ddd4j-boot-web.
Verdict: REJECTED — Boot modules assemble ddd4j capabilities; they do not
copy or redefine core contracts.

Compliant paths:
  a) Change the contract in ddd4j-core, verified on the current line
     (hand off to the `ddd4j-core` skill).
  b) Keep the core contract intact and wrap it at assembly time in the
     boot adapter (decorator), leaving core semantics untouched.

missing: which behavior the version check should have; how to provide: the
core contract change request or the decorator specification.
```

## Failure the skill must avoid

Making the two-line change because it compiles. The forking of core semantics inside a Boot module is invisible until a second service depends on the same core and gets different behavior.
