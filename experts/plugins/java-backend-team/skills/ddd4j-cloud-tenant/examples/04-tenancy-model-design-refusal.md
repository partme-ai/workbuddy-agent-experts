# Example 4 — Designing a tenancy model from scratch, no ddd4j

## Prompt

> We're designing a new SaaS product: shared database, tenant column per table, RLS maybe later. No ddd4j anywhere. Give us your tenant isolation rules to copy.

## What the skill should do

1. Say plainly: do not use this skill — `TenantContextHolder`, the Tenant annotation, and the SQL filtering are ddd4j-cloud contracts with ddd4j context dependencies.
2. Do not transcribe the ddd4j rules as if they were generic; the mechanism only works inside the ddd4j context/propagation stack.
3. Route to generic multi-tenancy architecture guidance (no `npx skills add` command applies) for the general patterns: tenant discriminator columns, RLS, scoping at the data layer, token-bound tenant claims.
4. Offer the boundary the other way: if the product later adopts ddd4j (Cloud or Boot), this skill then governs the ignore rules, exemptions, and propagation — chosen together with the runtime tuple.

## Expected output

```
Verdict: this skill's contracts do not apply — project has no ddd4j.

Why: Tenant annotation, TenantContextHolder, and the SQL filter are
coupled to ddd4j context propagation; extracting "just the rules" ships
dependencies the product does not have.

Path forward (no ddd4j): generic multi-tenant design guidance —
tenant discriminator strategy, data-layer enforcement, token-bound
tenant identity. No ddd4j install command.

If adopting ddd4j later: pick the runtime tuple first; this skill then
covers holder wiring, ignore rules, and cross-service propagation.
```

## Failure the skill must avoid

Dumping the ddd4j ignore-rule list as a generic checklist. Without the ddd4j holder/propagation machinery those rules are inert text, and their exemptions are actively dangerous if re-implemented without the same scope discipline.
