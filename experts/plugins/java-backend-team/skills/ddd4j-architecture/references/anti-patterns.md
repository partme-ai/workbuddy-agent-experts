# Anti-Patterns

> Collection date: 2026-09-11.

1. **Directory equals completion** — A module's existence does not mean the capability works. Require an entry point, registration, and behavior tests.
2. **Broken dependency inversion** — Core imports concrete frameworks. Move implementations to the adapter layer.
3. **Static facade without registration** — Code calls Registry/Contexts before any wiring has happened. The runtime layer must perform registration.
4. **Lost lifecycle** — Connections or thread pools are created but never closed. Define an owner and reverse-close it.
5. **Cross-line copy-paste** — Higher-line APIs ported directly to older JDKs. Adapt per line.
