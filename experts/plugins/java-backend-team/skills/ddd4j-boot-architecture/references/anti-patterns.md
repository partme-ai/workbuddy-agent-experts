# Anti-Patterns

> Collection date: 2026-09-11.

1. **Flattening across lines**: unifying JDK/Maven; keep the matrix.
2. **Module as behavior**: reading artifacts only; verify auto-configuration and run tests.
3. **Dependency overreach**: concrete modules owning platform versions; return them to the corresponding BOM.
4. **Defaults overriding user configuration**: missing MissingBean checks; verify user overrides.
5. **Evidence conflation**: counting local success as CI/publish; report in layers.
