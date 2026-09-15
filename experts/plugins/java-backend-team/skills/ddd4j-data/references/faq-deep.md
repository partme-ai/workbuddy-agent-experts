# Deep FAQ

> Collection date: 2026-09-11.

1. **Can snapshot and event sourcing mix?** The same aggregate must not mix them.
2. **Is a JPA Entity an AggregateRoot?** Keep them separate unless an explicit trade-off justifies the merge.
3. **Does native MyBatis support delete?** The default mapper does not define it; implement it explicitly.
4. **Can R2DBC join a blocking transaction?** Cannot be assumed.
5. **Is Panache only for Quarkus?** Yes — it is the matching runtime adapter.
6. **Is Projection always real-time?** No — define latency and recovery.
7. **Is Outbox equal to MQ?** No — it is a reliable-publish storage pattern.
8. **How does EventStore append handle concurrency?** Expected version and database constraints.
9. **When is tenant bypass allowed?** Only in controlled system operations with auditing.
10. **What counts as proof of completion?** Real-database, transaction, concurrency, and recovery tests.
