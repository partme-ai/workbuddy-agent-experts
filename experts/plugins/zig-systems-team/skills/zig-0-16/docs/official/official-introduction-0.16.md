# Zig 0.16 Introduction (Official Distillation)

Source: https://ziglang.org/documentation/0.16.0/#Introduction

## What Zig is (official framing)

Zig is a general-purpose programming language and toolchain for building robust, optimal, and reusable software.

It aims to keep programs understandable and maintainable by avoiding hidden behavior and by making control flow and memory management explicit.

## Core ideas

- No implicit control flow.
- No implicit memory allocation.
- No preprocessor and no macros.
- `comptime` enables type-level programming and zero-cost code generation.

## Zig as a toolchain

The official docs frame Zig as both:

- A language: write Zig programs and libraries.
- A toolchain: build Zig, C, and C++ projects with a consistent cross-platform development experience.

Practical implications:

- Prefer `zig build` for a consistent build workflow across platforms.
- Use Zig’s dependency-free tooling to reduce environment drift between contributors.

## How this maps to this repository

- Language and semantics: `../../references/language.md`
- Practical coding patterns: `../../references/patterns.md`
- Build system: `../../references/std-build.md`
- Comptime and generics: `../../references/comptime.md`, `../../references/std-meta.md`
- C interop: `../../references/c-interop.md`, `../../references/std-c.md`
