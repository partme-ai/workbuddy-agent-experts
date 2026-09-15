# Example 4 — Authoring a Quarkus extension

## Prompt

> Same goals as our Javalin extensions, but for our Quarkus services — build a Quarkus extension with the same override semantics. You did the Javalin one, so do this next.

## What the skill should do

1. Recognize the boundary: Quarkus extensions are build-time-augmented artifacts with their own authoring model — a different contract from Javalin runtime composition via Guice.
2. Hand off to `ddd4j-quarkus-extension-authoring` for the Quarkus extension build, deployment model, and test conventions.
3. State what transfers conceptually (unique SPI providers, explicit lifecycle owners, default-versus-override test paths) so the handoff keeps the hard-won lessons.
4. Keep this skill's scope: the Javalin lines' extension composition remains here, including any shared business module both runtimes consume.

## Expected output

```
Boundary: Quarkus extension authoring is its own skill.
Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-extension-authoring

What carries over as design rules (not as code):
  - One provider per SPI contract; duplicates resolve nondeterministically.
  - Overrides must apply after their defaults exist (Quarkus: build-time ordering).
  - Test both branches: extension present and absent.

This skill remains responsible for Javalin composition (6.7.x/7.1.x/7.2.x),
including the shared BusinessPricingModule both runtimes consume.
```

## Failure the skill must avoid

Reusing the Guice `Modules.override` composition as the Quarkus extension's wiring model because "we solved this already". Quarkus resolves extensions at build time with a different override mechanism — porting the Javalin composition produces an artifact that builds but never overrides.
