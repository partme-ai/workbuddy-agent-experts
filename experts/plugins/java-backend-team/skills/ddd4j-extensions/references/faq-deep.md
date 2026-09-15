# Deep FAQ

> Collection date: 2026-09-11.

1. **Is Jackson a standalone extension?** The core capability currently lives in kit/core.
2. **Where is Akka?** Currently mainly in the Boot extension.
3. **Can PF4J plugins be trusted?** Origin and permission policies are required.
4. **Can QLExpress execute arbitrary code?** Restrict it with builder permissions and function allowlists.
5. **Can the license be bypassed?** No.
6. **Is OTel the same as the metrics module?** It is an adapter/export relationship with different responsibilities.
7. **Does disabling an extension affect core?** It should degrade optionally.
8. **Who implements configuration switches?** The specific runtime/auto-configuration.
9. **Do extensions need the BOM?** ddd4j-bom manages consumed versions.
10. **What proves completion?** Module tests, runtime assembly, and external behavior.
