# Deep FAQ

> Collection date: 2026-09-11.

1. **Are all runtime APIs the same?** No — only the behavior contract is.
2. **Does Context live in Domain?** Domain reads through an abstraction; it does not depend on a framework.
3. **How do 401 and 403 differ?** Unauthenticated versus insufficient permission.
4. **Is Validation a domain rule?** It only protects the input boundary.
5. **Can Caffeine serve as production idempotency?** Not across multiple instances.
6. **Can readiness be hardcoded?** No.
7. **Does WebFlux Context use ThreadLocal?** No — needs reactive propagation.
8. **How is async cleaned up?** Restore in completion and exception callbacks.
9. **Can RawResponse bypass authentication?** It can only affect the response wrapper.
10. **What counts as proof of completion?** Each adapter's real HTTP contract tests.
