# Example 3 — Prove a bean is actually registered

## Prompt

> A teammate says our extension's `RateLimiter` bean is wired because we import the extension BOM. I'm skeptical. Can you verify registration properly?

## What the skill should do

1. Affirm the skepticism: a BOM import registers nothing — verify beans/BuildItems at the source level.
2. Read the deployment module and locate the BuildItem production or synthetic bean registration for `RateLimiter`.
3. Confirm the runtime module declares the bean (or the Recorder produces a synthetic bean) with a defined CDI scope.
4. Name the behavioral proof: an Arc build-time validation plus a `@QuarkusTest` that injects `RateLimiter` and exercises it.
5. Return an evidence-status block separating SOURCE from TEST.

## Expected output

```
Question: is RateLimiter registered, or only version-managed by the BOM?

Evidence:
  - BOM import: present (proves version pinning only).
  - deployment module: RateLimiterProcessor produces SyntheticBeanBuildItem for RateLimiter (line NN).
  - runtime module: Recorder registers the bean, scope @Singleton.
  - Arc build validation: NOT RUN on this SHA.
  - @QuarkusTest injecting RateLimiter: NOT RUN.

Verdict: registration EXISTS at SOURCE level; bean presence UNPROVEN until the
Arc/QuarkusTest run passes. Missing: test run; how to provide: execute the
extension's test module on this SHA.
```

## Failure the skill must avoid

Reporting "yes, it's wired" from the BOM import. That is the exact "BOM as runtime" anti-pattern — the bean may never be assembled, and only build items and recorders (plus their tests) prove it.
