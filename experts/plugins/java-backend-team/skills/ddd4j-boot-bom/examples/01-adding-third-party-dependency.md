# Example 1 — Adding a third-party dependency the right way

## Prompt

> We need to add a new HTTP client library to ddd4j-boot on the 3.x line. Which POM gets the version — the module's own pom, boot-dependencies, or somewhere else?

## What the skill should do

1. Fix the maintenance line first, then read `ddd4j-boot-parent`, `ddd4j-boot-dependencies`, and `ddd4j-boot-bom` on that line.
2. Apply the ownership rule: ordinary third-party versions are governed by ddd4j-dependencies; the Boot layer only overrides the Boot ecosystem.
3. If the client is part of the Boot ecosystem (for example a Spring-managed client), manage it through the Boot alignment; otherwise inherit from ddd4j-dependencies.
4. Show the module consuming the dependency without any version declaration of its own.
5. Verify the result in the effective POM and run the module build.

## Expected output

```
Ownership decision:
  - Is it Boot-ecosystem-aligned? no → version entry goes in
    ddd4j-dependencies (not boot-dependencies, not the module POM)
  - ddd4j-boot-bom imports it for Boot consumers (no version pin)
  - ddd4j-boot-<module> declares the dependency with NO <version>

Verification:
  mvn help:effective-pom → resolves to the ddd4j-dependencies version
  module build: REACHED
```

## Failure the skill must avoid

Putting the version in the module POM "so it's next to the code". That re-pins an ownership-managed coordinate and diverges for every other consumer the first time ddd4j-dependencies bumps.
