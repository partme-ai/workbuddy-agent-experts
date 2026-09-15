# Example 4 — Adding cache methods to the domain via the boot layer (boundary case)

## Prompt

> Have the boot-cache module add a `getOrLoad(key, loader)` convenience onto the Cache interface our aggregates use — every service re-implements it, it belongs in the framework.

## What the skill should do

1. Decline the placement: the `Cache` interface the domain depends on is the `ddd4j-cache` / `ddd4j-core` SPI; a Boot module extends implementations, not the SPI the domain sees.
2. Explain the fork: a boot-local Cache subtype means the domain layer now depends on a Boot-era type, breaking the framework-agnostic boundary and every non-Boot runtime.
3. Route the SPI change to `ddd4j-cache` (and `ddd4j-core` if the domain contract moves) with the install command; the change must then be proven per implementation, since atomic semantics are implementation responsibilities.
4. Offer the compliant alternative: a helper in the boot-cache module that composes existing SPI operations, leaving the interface untouched.
5. Record the refusal and handoff so the contract owners decide.

## Expected output

```
Request: add getOrLoad(key, loader) to the domain-facing Cache interface
from ddd4j-boot-cache.
Verdict: REJECTED — Boot modules implement the Cache SPI; they do not
extend it. A boot-local interface forks the domain boundary.

Handoff: Cache SPI change → `ddd4j-cache` (with `ddd4j-core` if the
domain contract is affected).
Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cache

Compliant path: boot-cache helper composing SPI get/put/cas — domain
keeps depending on the unchanged Cache interface.

missing: the call sites that would use getOrLoad; how to provide: the
services and lines involved, so the helper (or SPI change) is verified
per implementation.
```

## Failure the skill must avoid

Adding the method to the interface from the boot module because it compiles and every service compiles too. The fork appears when the Quarkus or Javalin runtime loads the same domain and its Cache has no such method.
