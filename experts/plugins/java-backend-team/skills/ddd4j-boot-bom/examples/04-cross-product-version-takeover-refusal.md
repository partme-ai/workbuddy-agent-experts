# Example 4 — Cross-product version takeover (boundary case)

## Prompt

> We want to bump Jackson for our boot service only, directly in ddd4j-boot-dependencies. It also affects the cloud product, but we'll deal with that later.

## What the skill should do

1. Decline the local bump: Jackson is an ordinary third-party version governed by ddd4j-dependencies at the product-family level, not by the Boot layer.
2. Explain that owning it in `ddd4j-boot-dependencies` forks the version across products — the cloud and other runtimes would silently resolve a different Jackson.
3. Route the actual bump to the `ddd4j-bom` skill (cross-product ownership), with the install command.
4. If a Boot-specific override is genuinely required, show the compliant path: document the Boot-ecosystem override scope and verify consumers on every line it ships to.
5. List what must be verified before any such change: effective POMs per line and consumer builds.

## Expected output

```
Request: bump Jackson in ddd4j-boot-dependencies (boot-only).
Verdict: do not use the Boot layer for this. Jackson is ordinary
third-party scope → owned by ddd4j-dependencies across products.
A boot-local pin forks the version for every other runtime.

Handoff: version bump goes through `ddd4j-bom`.
Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-bom

If a temporary Boot override is unavoidable:
  missing: consumer list for the override; how to provide: the products
  and lines consuming ddd4j-boot-dependencies, so each consumer's
  effective POM can be verified.
```

## Failure the skill must avoid

Making the boot-local bump because it fixes this service today. The other products keep the old version, and the first cross-product integration to touch Jackson serializes differently on each side.
