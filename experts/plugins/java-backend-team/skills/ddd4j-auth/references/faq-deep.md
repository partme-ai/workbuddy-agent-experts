# Deep FAQ

> Collection date: 2026-09-11.

1. **Must all three frameworks be enabled?** No — choose the primary implementation per project.
2. **Is the ddd4j Subject the same as the framework Subject?** No — it is a unified abstraction.
3. **How do I read Sa-Token extras?** Through the AuthConstants/StpKit wrappers.
4. **Does the Shiro Realm belong in core?** No.
5. **Can SecurityContext enter the domain layer?** It should not.
6. **Does OIDC register the SubjectProvider automatically?** No.
7. **Is Same-Token user authentication?** No.
8. **Can a temporary token be permanent?** Not with safe defaults.
9. **How does identity propagate across async boundaries?** Through the controlled Context propagation provided by the runtime, then restore.
10. **What counts as completion evidence?** Provider, exception, lifecycle, and real request tests.
