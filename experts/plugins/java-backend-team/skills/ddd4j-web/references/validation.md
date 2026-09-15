# Validation

> Collection date: 2026-09-11.

Public constraints: `AllowableValues(allows, nullable)`, `PhoneNumber(lang)`, `NumberValue(regex)`, `StringDateValue(pattern)`.

`StringDateValue` currently passes empty strings and performs strict date parsing. `Number` and `Phone` null behavior requires `NotNull` and tests. 3.0.x uses `jakarta.validation`; older lines must be confirmed per line.
