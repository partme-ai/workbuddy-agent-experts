# Example 4 — Designing the error payload in the Boot layer (boundary case)

## Prompt

> Frontend wants a new error payload: `{ code, message, traceId, userHint }`. Just add it to the boot-web error handler — it's one class.

## What the skill should do

1. Decline the "one class" framing: the error payload is the shared error contract; defining it in the boot layer forks it from the `ddd4j-web` contract the other runtimes and the docs follow.
2. Explain the fork: cloud/javalin/quarkus services would emit a different shape, and frontend then needs per-runtime parsing — the contract must move where all adapters follow it.
3. Route the contract change to `ddd4j-web` (with `ddd4j-core` if the context/trace identifiers interact) with the install command.
4. Offer the compliant Boot-layer work: once the contract is updated upstream, this skill wires the new payload into the MVC/WebFlux handler and proves it with contract tests on this line.
5. Record the handoff and the wiring follow-up.

## Expected output

```
Request: new error payload shape added in ddd4j-boot-web's handler.
Verdict: REJECTED as a boot-local change — the error payload is a shared
contract. A boot-local shape forks it from every other runtime.

Handoff: contract change → `ddd4j-web` (with `ddd4j-core` if traceId /
context identifiers are affected).
Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-web

Then, back here: wire the updated contract into the MVC/WebFlux error
handling on this line and verify with HTTP contract tests (error +
validation paths).

missing: the field semantics for userHint and traceId source; how to
provide: the frontend contract request or the upstream contract PR.
```

## Failure the skill must avoid

Adding the payload class to boot-web because it ships fastest. Six months later the error shape differs per runtime and the frontend carries a compatibility shim — the exact fork the contract discipline exists to prevent.
