# Example 2 — Read-only extension structure review

## Prompt

> Review our existing ddd4j cache extension read-only before the next release. Is it structured the way extensions in this repo should be?

## What the skill should do

1. Stay read-only and fix the line/SHA first — structure conventions differ per line.
2. Check the module pair exists and that `extension-parent` is the parent for both artifacts.
3. Read the `Processor`: are BuildItem consumptions/productions explicit? Are `Recorder` calls the only bridge into runtime bootstrap?
4. Check bean registration comes from BuildItems, with CDI scopes and config mappings defined in the runtime module.
5. Report native-readiness: reflection/serialization registrations present, Docker detection classloader-aware.

## Expected output

| Check | Finding | Status |
|---|---|---|
| runtime/deployment pair | both modules present under extension-parent | OK |
| Processor BuildItems | consumes `CacheBuildItem`, produces none; implicit production of config via recorder | OK with note |
| Bean registration | via BuildItem; runtime module defines `@ApplicationScoped` + config mapping | OK |
| Native registrations | reflection entry missing for `CacheEntryKey` used reflectively in eviction listener | **GAP** |
| Docker detection | classloader-aware helper reused | OK |

Not run: native build (gap above would likely fail it).

## Failure the skill must avoid

Passing the extension because JVM-mode tests are green. The missing reflection registration only surfaces at native build — the review must audit the native registration list, not just the JVM suite.
