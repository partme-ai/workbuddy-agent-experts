# Example 3 — Verifying a utility's null and exception semantics

## Prompt

> Before we standardize on `StrKit` across all our services: what actually happens on null and empty input? The Javadoc is one line and nobody wrote tests for the edge cases.

## What the skill should do

1. Refuse to answer from the name or the one-line Javadoc — read the signature, the implementation, and the existing tests in the target line.
2. Determine null behavior: exception, `false`, `true`, `Optional.empty()`, or empty-string pass-through.
3. Determine the exception contract: checked, unchecked, or swallowed into a default value.
4. Check the maintenance line: the same-named method may behave differently (or not exist) on 1.0.x/2.0.x.
5. Report the semantics with evidence and name the boundary cases the existing tests do not cover.

## Expected output

```
Method: StrKit.isBlank (2.0.x, checked in current source)
  - null        → true
  - ""          → true
  - "  "        → true (whitespace-only)
  - non-string  → compile-time impossible (String parameter)

Exception contract: never throws; total function.
Existing tests cover: null, "", "x". NOT COVERED: whitespace-only, unicode
whitespace (\u00A0), very large input.

Line check: method exists on 1.0.x/2.0.x/3.0.x; semantics compared identical
on the two lines read. 3.0.x NOT re-read — flagged unverified.
Evidence: SOURCE.
```

## Failure the skill must avoid

Answering "it returns true for null-ish input, standard stuff" from the method name. The whole point of reading the source is that `\u00A0`-style edge cases and swallowed-exception contracts differ between plausible implementations — and between lines.
