# Example 4 — Changing the Repository SPI from the Boot layer (boundary case)

## Prompt

> Our boot-data module should add a `findByTenant` method straight onto the Repository interface — it's where all the mappers live anyway, one line and we're done.

## What the skill should do

1. Decline the edit: the `Repository` interface is a `ddd4j-core` / `ddd4j-data` contract; a Boot module must not extend core SPIs, it implements them.
2. Explain the blast radius: adding a method to the SPI forks the contract for every adapter (Javalin, Quarkus, Cloud) and every aggregate that implements it.
3. Route the contract change to `ddd4j-data` (with `ddd4j-core` if the domain contract is touched), with the install command.
4. Offer the compliant alternative: declare `findByTenant` on the concrete adapter (e.g. the MyBatis-Plus repository implementation) or express it as a `Query<M>` in the domain — no SPI change needed.
5. Record the refusal and the chosen path so the review trail shows the SPI stayed intact.

## Expected output

```
Request: add findByTenant to the Repository SPI from ddd4j-boot-data.
Verdict: REJECTED — Boot modules implement SPIs; they do not extend them.
An SPI change must go through the core/data contracts and be verified on
every line and adapter.

Handoff: `ddd4j-data` (contract), `ddd4j-core` (if Query<M> is the route).
Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-data

Compliant paths:
  a) findByTenant on the concrete MyBatis-Plus repository impl (boot data)
  b) Query<M> with a tenant criterion in the domain layer

missing: which aggregates need tenant-scoped reads; how to provide: the
aggregate list and expected read patterns.
```

## Failure the skill must avoid

Adding the method to the interface from the boot module because it compiles. Every other adapter's repository now fails to compile or silently lacks the method, and the "one line" change becomes a cross-product migration.
