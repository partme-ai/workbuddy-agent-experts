# ID, Function, and Reflection

> Collection date: 2026-09-11.

- **`IdKit`** — identifier generation and conversion entry point.
- **`FunctionKit`** — controlled type-conversion functions.
- **`ReflectKit` and metadata utilities** — use only when type information cannot be expressed statically.

Reflection failures must carry the target type and member information. Do not swallow exceptions or bypass access safety.
