# Example 1 — ORM annotations on a PO

## Prompt

> We have an `OrderPO` for the 2.0.x line. Mark the order number as the business key, add tenant isolation, and auto-populate created/updated timestamps. What ddd4j annotations do I use and what else do I need?

## What the skill should do

1. Confirm the maintenance line and the ORM annotation package from the current source.
2. Map each requirement to an annotation: `@BizKey` for the order number, `@TenantId` for tenant isolation, `@OnCreate` / `@OnUpdate` for timestamps.
3. State for each annotation which consumer must be present: `DomainModelHelper`, the repository, or the interceptor chain.
4. Warn that `@TenantId` only populates when a tenant is actually bound in the request context.
5. Specify the test set: presence, default-value, independence, and consumer behavior tests.

## Expected output

```java
public final class OrderPO {
    @BizKey
    private String orderNo;

    @TenantId
    private String tenantId;

    @OnCreate
    private Instant createdAt;

    @OnUpdate
    private Instant updatedAt;
}
```

Plus a consumer checklist: the data adapter must run the interceptor that fills `@OnCreate` / `@OnUpdate`, and the request context must carry the tenant before the repository writes. Evidence tier: SOURCE read; adapter behavior test NOT RUN until the interceptor is exercised against a real database.

## Failure the skill must avoid

Listing the annotations and stopping there. The annotations are metadata only — without the data-side consumer, `createdAt` stays null and `tenantId` never gets populated, which is exactly the "annotation equals implementation" trap.
