# Example 2 — Auto-configuration review (read-only)

## Prompt

> Review our `XxxAutoConfiguration` before we ship. I care about whether users can override things and whether anything leaks at shutdown.

## What the skill should do

1. Stay read-only; findings with evidence, not patches.
2. Fix the line, then read the configuration class, its Properties, and the registration file appropriate for that Boot line.
3. Check every default bean for a `@ConditionalOnMissingBean` guard and every condition for a sensible `matchIfMissing`.
4. Check the lifecycle: explicit resource owner, `destroyMethod` declared and idempotent, rollback on failed creation.
5. Rate the override and disable paths as verified or unverified — never claimed without a test.

## Expected output

| Check | Finding | Severity |
|---|---|---|
| Registration | present in `AutoConfiguration.imports` (Boot 3.x mechanism) | OK |
| Default beans | `xClient` lacks `@ConditionalOnMissingBean` — user bean cannot replace it | High |
| Off switch | `xxx.enabled=false` skips the client but `xHealthIndicator` still assembles | High |
| Lifecycle | `destroyMethod` not declared; inference picks `close()` only if it exists | Medium |
| Override path | no context test exercises a user-provided bean | Unverified |

Evidence: SOURCE read on line <L>. Context tests NOT RUN.

## Failure the skill must avoid

Reporting "conditions look fine" from skimming annotations. The two classic defects — a missing MissingBean guard and an off switch that leaves helper beans alive — are invisible unless each bean's guards are read one by one.
