# Example 4 — Bumping Spring Cloud in one service POM

## Prompt

> Our service needs a Spring Cloud fix that landed in a newer release train. Can I just bump the Spring Cloud version in my service POM and keep the rest of the ddd4j line as is?

## What the skill should do

1. Refuse the piecemeal bump: the Cloud→Boot→ddd4j tuple is chosen together, and version ownership lives in the line's BOMs — not in service POMs.
2. Explain the two failure modes: a mixed tuple that the matrix never validated, and an ownership violation where the service overrides a managed version.
3. Route correctly: if a newer Cloud line is genuinely needed, re-select the whole combination with `ddd4j-cloud-version-selection` and adopt it via the line's BOM update.
4. If the fix is urgent, propose the sanctioned path (line-level BOM change + release) with the evidence steps, rather than a local override.

## Expected output

```
Verdict: do not bump Spring Cloud inside the service POM.

Why:
  1. The tuple Cloud→Boot→ddd4j is validated as a unit by the matrix;
     half-bumping it creates an untested combination.
  2. Version ownership is BOM-owned; a service-local override re-pins a
     managed version and splits the line's resolution.

Sanctioned path:
  - Select the newer combination (ddd4j-cloud-version-selection).
  - Move the line's BOM imports/parent accordingly (this skill).
  - Validate build + CI + clean-cache consumption before consumer upgrade.
```

## Failure the skill must avoid

Writing the local `<version>` override that makes the immediate build pass. The service then sits on an unvalidated Cloud/Boot/ddd4j mix and diverges from every other service on the line.
