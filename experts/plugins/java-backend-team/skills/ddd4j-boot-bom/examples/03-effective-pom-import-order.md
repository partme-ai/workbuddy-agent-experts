# Example 3 — Effective POM import-order proof

## Prompt

> Our parent imports the Spring Boot BOM and the ddd4j BOM. We argue about which one wins for overlapping coordinates. Settle it with evidence.

## What the skill should do

1. Refuse to answer from reading the import block alone — order questions are only provable in the effective POM.
2. Fix the maintenance line, then run `mvn help:effective-pom` on the target module.
3. Resolve a deliberately overlapping coordinate and show which BOM's version won.
4. Explain the precedence rule in effect for this line's import order.
5. Record the evidence status and what was not tested.

## Expected output

```
Question: for coordinates managed by both BOMs, which import wins?

Evidence (effective POM of ddd4j-boot-web, line 3.x):
  import order: Spring Boot BOM, then ddd4j BOM
  probe coordinate resolved to: <winning version, source BOM named>

Conclusion: <which import takes precedence on this line and why>.
To change the winner, reorder imports in the parent — never re-pin the
coordinate in a module.

Evidence status: SOURCE + effective-POM RESOLVED. Downstream consumer
builds NOT RUN.
```

## Failure the skill must avoid

Settling the argument with "last import wins, always" quoted from general Maven lore. Precedence behavior must be shown from this line's effective POM; the reading of the source POM proves nothing.
