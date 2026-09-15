# Example 4 — Porting MyBatis-Plus mappers to Quarkus

## Prompt

> We have 40 MyBatis-Plus mappers in our Spring Boot service and we're moving this service to ddd4j-quarkus. Just tell me the Quarkus equivalents of `BaseMapper` and `LambdaQueryWrapper` so we can port them one-to-one.

## What the skill should do

1. Decline the one-to-one port: `BaseMapper`/`LambdaQueryWrapper` are MyBatis-Plus contracts; the Quarkus line's supported stacks are Panache, JPA, JDBI, and R2DBC — there is no wrapper-for-wrapper translation, and the skill should not invent one.
2. Note the destination skill for the source side: the existing mappers belong to the Spring Boot world (`ddd4j-boot-data`); a service-by-service move is a migration, not a mapper swap.
3. Redirect the design question: in ddd4j-quarkus the domain depends on the `Repository` SPI and the queries are implemented in the chosen adapter — the port should start from the aggregate's query needs, not from the 40 mapper signatures.
4. Flag the version prerequisite: the line must be fixed first (`ddd4j-quarkus-version-selection`), since supported stacks are per line.
5. Do not fabricate API mappings — do not use this skill to produce a fake translation table.

## Expected output

```
Boundary: no one-to-one BaseMapper/LambdaQueryWrapper equivalent exists on the
ddd4j-quarkus line; the supported stacks are Panache, JPA, JDBI, R2DBC. The
source side (MyBatis-Plus) is ddd4j-boot-data territory.

Recommended path:
  1. Fix the target line (ddd4j-quarkus-version-selection).
  2. Inventory the queries the domain actually needs (Repository SPI + Query<M>).
  3. Implement those in the chosen adapter; port by capability, not by mapper.

Do not use this skill for a 40-row fake translation table — that invents APIs.
```

## Failure the skill must avoid

Producing a made-up mapping ("`LambdaQueryWrapper` ≈ Panache `Query` with these semantics") that looks authoritative. The invented equivalences would silently change query behavior during the migration.
