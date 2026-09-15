# Example 5 — Runtime config change that silently does nothing

## Prompt

> We tried to switch the Hibernate dialect per environment by setting `quarkus.hibernate-orm.dialect` in the prod runtime profile. The app starts fine but still uses the default dialect. Is the property name wrong?

## What the skill should do

1. Recognize the real cause: `quarkus.hibernate-orm`-style configuration is build-time fixed — the dialect is locked when the application is built, not when it starts.
2. Explain why nothing errored: runtime profiles re-read runtime-reconfigurable keys only; build-time keys keep their build value and the override is ignored silently.
3. Give the correct options: set the dialect per build (per-environment builds or build-time config sources), or pick a dialect-detected setup that does not need the override.
4. Generalize the check: classify each data config key as build-time or runtime before promising environment-specific behavior.
5. Name the verification: rebuild with the intended dialect and confirm the effective configuration in the startup log of the target environment.

## Expected output

```
Cause: quarkus.hibernate-orm.dialect is a BUILD-TIME fixed property. A prod
runtime-profile override cannot change it — the value is locked at build and the
runtime override is ignored (no error).

Options:
  1. Build per environment with the dialect in the build-time config.
  2. Omit the dialect and let the engine detection choose it (if the line supports it).

General rule: classify every quarkus.* data key as build-time or runtime before
promising per-environment behavior. Runtime overrides of build-time keys fail silently.

Verify: rebuild for the target env; confirm the effective dialect in startup logs.
```

## Failure the skill must avoid

Trying more runtime-profile spellings (`%prod.quarkus...`, env var forms) hoping one takes — none will. The property class is the problem, not the syntax.
