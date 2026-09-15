# Example 2 — Version ownership audit (read-only)

## Prompt

> Audit read-only: are any of our boot modules managing versions they shouldn't? We suspect some pins crept in over the years.

## What the skill should do

1. Stay read-only; produce findings, not patches.
2. Fix the line first, then read `ddd4j-boot-parent/pom.xml`, `ddd4j-boot-dependencies/pom.xml`, `ddd4j-boot-bom/pom.xml`.
3. Build the ownership map: which POM governs which coordinates on this line.
4. Scan every concrete module POM for `<version>` declarations that re-pin managed coordinates.
5. Output each violation with the governing POM it should be returned to.

## Expected output

| Module | Re-pinned coordinate | Governing POM | Action |
|---|---|---|---|
| `ddd4j-boot-data` | `jackson.version` | ddd4j-boot-dependencies | Remove pin, inherit |
| `ddd4j-boot-web` | `spring-framework.version` | Spring Boot BOM alignment | Remove pin |
| `ddd4j-boot-cache` | clean | — | — |

Summary: 2 violations across 11 module POMs. Returning both pins to their governing POMs changes no resolved versions today (effective POM identical) but restores single-point ownership.

Evidence: SOURCE (effective POMs compared). Consumer impact test NOT RUN.

## Failure the skill must avoid

Flagging only pins that currently resolve differently. A re-pin that happens to match today is still a defect — it diverges silently at the next BOM bump.
