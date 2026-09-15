# Anti-Patterns

> Collection date: 2026-09-11.

1. **Framework intrusion into core**: keep adapters in the runtime.
2. **Duplicate overrides**: later SPI registration silently overwriting; fail fast/use scopes.
3. **Partial startup leakage**: no rollback on failure; close in reverse order.
4. **Hardcoded readiness**: aggregate real dependencies.
5. **Context residue**: restore on every terminal state.
