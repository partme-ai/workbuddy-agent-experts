# Deep FAQ

> Collection date: 2026-09-11.

1. **Where do interfaces and implementations go?** Ports in core, bindings in the runtime.
2. **Can two CommandBuses be registered at once?** Only with explicit routing; avoid conflicts by default.
3. **Who registers the SubjectProvider?** The target runtime.
4. **Is Guice the same as Spring?** No.
5. **When does Quarkus register?** Per the current CDI observer/producer implementation.
6. **Is ready the same as started?** No.
7. **How does rollback work?** Record completed items and close them in reverse order.
8. **Can close throw?** Exceptions are aggregated while other resources continue closing.
9. **What about async Context?** Use the runtime propagation mechanism and restore.
10. **What proves completion?** runtime-testkit plus real framework startup/shutdown tests.
