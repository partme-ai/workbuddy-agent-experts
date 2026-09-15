# Deep FAQ

> Collection date: 2026-09-11.

1. **Is MQClient a broker client?** It is a unified port; concrete adapters implement it.
2. **Can ACK be automatic?** It depends on the adapter/configuration and needs testing.
3. **Does failure always requeue?** Policy decides.
4. **Does the Outbox belong to MQ?** It is stored in data and solves reliable publishing.
5. **What mode does NATS use?** Check the current Core/JetStream implementation.
6. **Does SQS have topics?** The semantics differ; do not apply them mechanically.
7. **RocketMQ naming restrictions?** Illegal characters require conversion.
8. **Can ONS/TDMQ be tested in containers?** Managed services need an explicit substitute or exclusion.
9. **Where is Spring Cloud Stream?** ddd4j-cloud-stream owns the Binder.
10. **What proves completion?** Real broker round-trip, reliability, and lifecycle tests.
