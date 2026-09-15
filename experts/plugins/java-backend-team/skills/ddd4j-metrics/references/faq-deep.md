# Deep FAQ

> Collection date: 2026-09-11.

1. **Are metrics the same as tracing?** No.
2. **Is Noop an error?** It is an allowed degradation, but it provides no observability.
3. **Can tenantId be a label?** Usually high-cardinality and sensitive.
4. **How is projection lag computed?** An authoritative head and position are required.
5. **Can metric names change?** That is a monitoring contract change.
6. **Do tests need a collector?** Unit tests exercise the API; integration tests exercise the exporter.
7. **Can logs replace metrics?** No.
8. **Can readiness be derived from error rates?** Not as a direct substitute.
9. **How are MQ retries counted?** With stable attempt/result labels.
10. **What is the completion evidence?** Unit behavior, the export chain, and an alerting drill.
