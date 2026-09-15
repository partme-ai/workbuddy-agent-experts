# Example 5 — Dependency present, bean absent

## Prompt

> We added the ddd4j-boot-cache starter to our POM and the build resolves it fine, but at runtime there's no cache bean and our Cache SPI calls blow up. The module exists, so why doesn't it work?

## What the skill should do

1. Name the false assumption immediately: a module existing in the dependency tree does not mean its auto-configuration has taken effect.
2. Verify the assembly chain on the current line — is the AutoConfiguration registered for that line's registration mechanism, and are its conditions satisfied?
3. Check whether a user-declared bean is accidentally satisfying a `@ConditionalOnMissingBean` guard and disabling the default.
4. Distinguish dependency resolution evidence from bean creation evidence, then run the module's context test to prove which one holds.
5. Report findings with the exact condition or registration that failed.

## Expected output

```
Symptom: ddd4j-boot-cache on the classpath, CacheManager bean absent.

Checks:
  1. Registration: AutoConfiguration imports file for this Boot line —
     entry present / ABSENT ← defect found here
  2. Conditions: <conditional evaluated and its outcome>
  3. Override shadowing: no user CacheManager bean found

Root cause: the starter POM resolves, but the configuration class is not
registered on this Boot line's mechanism, so no bean is ever created.

Fix: register the configuration per this line's convention; re-run the
module context test.

Evidence: SOURCE + context TEST RUN (before/after).
```

## Failure the skill must avoid

Answering "the dependency is there, so the bean must be there — check your code" and sending the user chasing their own application. Dependency resolution and bean creation are different evidence layers; this skill exists to keep them apart.
