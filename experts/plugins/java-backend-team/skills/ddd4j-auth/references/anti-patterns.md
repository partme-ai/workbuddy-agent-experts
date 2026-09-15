# Anti-Patterns

1. **Framework leakage**: domain services read StpUtil/SecurityContext directly; use Subject instead.
2. **Multiple Provider contention**: all three frameworks registered at once; define exactly one primary implementation.
3. **Context residue**: cleanup on the success path but missed on the exception path; use finally/scope.
4. **Credential logging**: printing tokens/API keys; keep only redacted fingerprints.
5. **Testing success only**: add anonymous, expired, insufficient-permission, logout, and thread-reuse cases.
