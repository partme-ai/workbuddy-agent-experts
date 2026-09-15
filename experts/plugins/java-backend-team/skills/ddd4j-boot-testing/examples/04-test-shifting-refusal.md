# Example 4 — "Just mark the failing test as skipped" (boundary case)

## Prompt

> The broker round-trip test is flaky in CI and blocking our release train. Can't we just @Disable it for now and re-enable later? Everyone does it.

## What the skill should do

1. Refuse the silent disable: a disabled suite must be recorded as BLOCKED or SKIPPED in the evidence inventory with a reason and an owner — never folded into green.
2. Explain the trap: the broker suite is the only place delivery semantics (ack, retry, duplicates, recovery) are proven; disabling it converts "verified" into "unverified" for the whole integration.
3. Diagnose the flakiness instead: container startup timeouts, port collisions, and missing awaitility are the usual causes — each has a standard fix.
4. If the release train truly cannot wait, route the evidence decision to `ddd4j-boot-release`: release with a declared UNVERIFIED layer, or hold — but recorded, not hidden.
5. Record whatever path is chosen so the skipped suite cannot silently age into permanent invisibility.

## Expected output

```
Request: @Disable the broker round-trip suite to unblock the train.

Verdict: do not use a silent disable. Recorded options:
  a) fix the flake (usual suspects: container startup timeout, port
     collision, missing awaitility on async consumption) — preferred
  b) ship with the suite marked BLOCKED in the evidence inventory and
     the broker layer declared UNVERIFIED → `ddd4j-boot-release` decides
     whether that evidence level can pass the gate

Either way the inventory shows: broker round-trip — BLOCKED, reason,
owner, re-run date. A hidden skip shows nothing and is how "temporary"
disables become permanent.
```

## Failure the skill must avoid

Disabling the test with no record. The suite stays red-free and forgotten while the delivery semantics it covered silently stop being verified — the release gate then passes on evidence that no longer exists.
