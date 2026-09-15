# Example 5 — Arc unsatisfied dependency for SubjectProvider

## Prompt

> Our build broke overnight: `Unsatisfied dependency for type SubjectProvider`. Nothing in our code changed except a refactor that moved some classes into a new package. What happened?

## What the skill should do

1. Read the failure correctly: Arc validation runs at build time, so this is a discovery failure introduced by the refactor, not a runtime regression.
2. Check what the move broke: a class moved out of a discovered package often loses its bean-defining annotation path or its `@Produces` class was not moved/discovered with it.
3. Verify whether the producer method (or the class annotation) still exists and whether the new package is included in discovery at build time.
4. Distinguish the fix from anti-fixes: adding a runtime null-check or optional injection hides the broken port; the fix is restoring discovery/registration.
5. Name the verification: rerun the build (Arc validation passes) and the QuarkusTest suite covering the port.

## Expected output

```
Failure: build-time Arc validation — no bean exists for injection point SubjectProvider.

Diff review:
  - SubjectProviderProducer moved packages; @Produces method still present.
  - NEW package lacks a bean-defining marker on the producer class → class present
    in source but never discovered → no bean at build time.

Why "nothing changed" is misleading: discovery is resolved at build; moving classes
changes what Arc discovers even when behavior is untouched.

Fix: restore the bean-defining annotation on the producer class in its new package.
Anti-fix rejected: Optional<SubjectProvider> injection would silently disable the port.
Verify: build passes Arc validation + subject tests green.
```

## Failure the skill must avoid

Treating it as a transient failure or papering over it with optional injection. The port must be discovered at build time — an optional injection point just moves the failure to a runtime null at request handling.
