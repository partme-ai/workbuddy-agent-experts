# Serialization and Keys

> Collection date: 2026-09-11.

- Keys include the business domain, tenant, version, and stable identifier.
- Avoid writing PII into observable keys.
- Redis JSON uses a trusted data boundary.
- Schema changes require versioning or compatible reads.
- Deletion/invalidation uses precise prefixes; never flush an entire production database.
