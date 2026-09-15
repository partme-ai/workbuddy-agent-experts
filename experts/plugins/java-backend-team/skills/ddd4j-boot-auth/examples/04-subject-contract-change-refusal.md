# Example 4 — Changing the Subject contract from the Boot layer (boundary case)

## Prompt

> Add a `tenantId` getter directly onto the Subject our boot-auth layer hands out — just patch it in the auth module, the domain team can wait.

## What the skill should do

1. Decline the patch: the boot layer assembles the auth integration; the `Subject` contract itself is a ddd4j auth/core concern and must not be extended by a Boot-module side door.
2. Explain the consequence: a boot-local `Subject` variant forks the contract — every non-Boot runtime and the domain layer would see a different identity API.
3. Route the contract change to `ddd4j-auth` / `ddd4j-core` with the install command; tenant identity belongs in the core contract (or the context/tenant SPI), verified line by line.
4. Offer the compliant interim: if the boot layer already assembles a tenant-aware provider, surface tenant through the existing context mechanism rather than a new Subject subtype.
5. Record what was rejected and the handoff so the domain team owns the follow-up.

## Expected output

```
Request: boot-local Subject variant with tenantId getter.
Verdict: REJECTED — Boot modules assemble; they do not extend core
identity contracts. A boot-local Subject forks the account model.

Handoff: Subject contract change → `ddd4j-auth` (with `ddd4j-core` if the
context/tenant SPI is touched).
Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-auth

Interim option: expose tenant via the existing request context that the
SubjectProvider already populates — no contract change.

missing: which consumers need tenantId and on which lines; how to provide:
the consumer list so the contract change is verified per line.
```

## Failure the skill must avoid

Patching the getter into the boot-auth module because it unblocks one service. The fork surfaces when the cloud or Javalin runtime serves the same domain and the Subject there has no `tenantId` — a silent contract split.
