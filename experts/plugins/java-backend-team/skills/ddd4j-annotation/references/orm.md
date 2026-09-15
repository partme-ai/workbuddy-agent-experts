# ORM Annotations

> Collection date: 2026-09-11.

- **`DomainField`** — Domain field to PO property / column mapping.
- **`BizKey`** — business key.
- **`TenantId` / `SystemId`** — isolation fields.
- **`OnCreate` / `OnUpdate`** — audit population.
- **`OrderBy`** — default ordering metadata.

Verification chain: annotation → `DomainModelInfo` / `TableInfo` → repository / interceptor → actual database behavior.
