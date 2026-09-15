# Example 4 — Changing event publishing semantics from the Boot layer (boundary case)

## Prompt

> In the boot-mq module, make every publish also write an audit row and swallow broker errors — ops wants the app to never crash on MQ issues. Quick change in the adapter, right?

## What the skill should do

1. Decline the placement of the semantic change: swallow-on-error publishing changes the delivery contract of `DomainEvent` publication, which is a `ddd4j-core` / `ddd4j-mq` concern, not a Boot-adapter local tweak.
2. Explain the consequence: silently swallowing broker errors converts at-least-once into at-most-zero with no signal — events vanish while the app looks healthy.
3. Route the contract question to `ddd4j-mq` (with `ddd4j-core` if event publication semantics move) with the install command.
4. Offer the compliant Boot-layer alternative: the Outbox pattern (`ddd4j-boot-data`) decouples publish from the request path, and required/optional listener classification governs startup behavior — both are designed answers to "never crash on MQ issues".
5. Record the refusal and the chosen alternative.

## Expected output

```
Request: swallow broker errors in boot-mq publish + audit side-write.
Verdict: REJECTED — this changes DomainEvent publication semantics,
which belong to the ddd4j-mq/core contracts, not a Boot adapter.

Risk named: swallowed errors = silent event loss; the app never crashes
because it never admits the publish failed.

Handoff: `ddd4j-mq` (publication contract), `ddd4j-core` (event semantics).
Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-mq

Compliant alternatives:
  a) Outbox pattern — publish decoupled from request, retried reliably
     (see ddd4j-boot-data)
  b) classify listeners/publishers required vs optional per deployment
     need — explicit degradation, not silent swallowing
```

## Failure the skill must avoid

Making the change because the app stops crashing. It stops crashing because it stops publishing — the first sign is a downstream consumer that quietly starves, days after the "fix".
