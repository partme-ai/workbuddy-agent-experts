# Example 4 — Same endpoints, but plain Boot without Cloud

## Prompt

> One of our internal tools needs the same kind of endpoints — unified errors, i18n, readiness — but it's a plain Spring Boot service, no Spring Cloud, no ddd4j-cloud. Can we just add the ddd4j-cloud webmvc extension dependency?

## What the skill should do

1. Say plainly: do not drop the ddd4j-cloud webmvc extension into a non-Cloud project — it wires against ddd4j context/tenant contracts and Cloud configuration the tool does not have.
2. Refuse the "just this one dependency" pattern: the extension drags the Cloud→Boot→ddd4j tuple in through its BOM and silently re-pins the tool's Boot version.
3. Route inside the package: for ddd4j-based plain Boot wiring, the matching skill is `ddd4j-boot-web`; if ddd4j is not wanted at all, generic Spring Boot guidance applies (no install command).
4. Note what carries over conceptually (unified error contract, readiness aggregation, i18n fallback) versus what does not (the Cloud context/tenant filter chain).

## Expected output

```
Verdict: do not add the ddd4j-cloud webmvc extension to a plain Boot tool.

Why: the extension assembles ddd4j context/tenant filters and Cloud
configuration; on a non-Cloud project it is unverified wiring, and its
BOM re-pins the tool's Boot version.

Handoff:
  - ddd4j wanted, no Cloud → ddd4j-boot-web. Install:
    `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-web`
  - no ddd4j at all        → generic Spring Boot guidance (no install).

Concepts that transfer either way: unified error contract, readiness
aggregating real deps, i18n fallback rules.
```

## Failure the skill must avoid

Handing over the extension snippet "since it's only web MVC glue". The glue is coupled to the Cloud context chain, and the BOM import quietly upgrades the tool's Boot parent — the exact tuple drift this package exists to prevent.
