# Example 1 — Adding tenant SQL filtering

## Prompt

> We're enabling multi-tenancy in our ddd4j-cloud order service. Business tables must be tenant-filtered, but the system audit log must stay shared. Set it up.

## What the skill should do

1. Fix the combination with `ddd4j-cloud-version-selection`, then use the line's data tenant and MyBatis modules rather than hand-rolled SQL rewrites.
2. Bind the tenant id at entry (validated against the Subject/token, not trusted from the raw header) into `TenantContextHolder`.
3. Apply tenant SQL filtering to the business tables and register the audit log as a deliberate, documented exemption.
4. Wire propagation so the tenant survives async, Reactor, and Feign hops, and define system-context semantics for background jobs.
5. Specify the isolation tests: cross-tenant read blocked on filtered tables, exemption respected, all terminal paths.

## Expected output

```
Entry: tenant from token (validated) → TenantContextHolder at filter
SQL filtering: applied to order*, customer* tables
Exempt (documented): audit_log — reason: shared system log
Propagation: async + Feign carry tenant; system context only inside
  background scope, cleared on exit

Tests: cross-tenant read on orders → BLOCKED;
  audit_log shared read → OK; exception/async/Feign paths → pending run.
```

## Failure the skill must avoid

Filtering the tables but leaving the exemption undocumented, or worse, exempting "everything for the system user" to make the audit writer work — that ignore rule is the leak vector the isolation review hunts for.
