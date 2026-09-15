# Deep FAQ

> Collection date: 2026-09-11.

1. **Does `Retention.RUNTIME` mean auto-activation?** No.
2. **What does `Contract` do?** Marks an annotation as an auditable contract.
3. **Is `DDDAnnotation` a Spring Bean?** Cannot be assumed.
4. **Who executes `@ApiIdempotent`?** The Web / Runtime idempotency handler.
5. **Who reads `@DomainField`?** Domain metadata and data adapters.
6. **Does `@TenantId` auto-isolate?** Requires tenant context and an interceptor.
7. **Does `@OnCreate` auto-write the timestamp?** Requires repository or interceptor implementation.
8. **Does `RawResponse` bypass security checks?** It should only affect the response wrapper.
9. **Can annotation defaults be changed?** This is a public-contract change — cross-line testing required.
10. **What is the minimum test set for a new annotation?** Retention, Target, default value, independence, and consumer behavior.
