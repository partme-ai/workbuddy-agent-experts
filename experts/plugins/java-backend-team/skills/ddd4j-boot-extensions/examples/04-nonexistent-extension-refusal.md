# Example 4 — Requested extension does not exist (boundary case)

## Prompt

> We need a PDF watermark extension for ddd4j-boot. The extensions package probably has one — just tell us the config keys and we'll wire it.

## What the skill should do

1. Check the current line's extension submodules from the root POM before answering anything.
2. Report the honest finding: no PDF watermark submodule exists on this line — do not use this skill to invent config keys or a plausible module name.
3. Mark the request NOT IMPLEMENTED and state what does exist (e.g. Excel for document export) so the user can redirect.
4. Route "how would a new extension be structured" to the architecture skill; route Quarkus-side extension authoring to its own skill — never fabricate a Boot module that was never published.
5. Offer the compliant interim: integrate a PDF library directly in the application with generic Spring Boot skills until an official extension exists.

## Expected output

```
Request: PDF watermark extension config keys.
Evidence: root POM extension aggregator on line <L> lists:
  akka, excel, qlexpress, qrcode, monitor (+ line-specific modules)
  → no PDF watermark submodule. NOT IMPLEMENTED.

Do not use invented config keys — none exist to wire.

Paths:
  a) nearest existing capability: Excel extension (different format)
  b) interim: integrate a PDF library in your application via generic
     Spring Boot skills
  c) new extension proposal → `ddd4j-boot-architecture` for module
     placement, then the release skill for publication

missing: which line you target and whether an upstream extension was
published after the matrix snapshot; how to provide: the line number and
a re-run of the submodule listing.
```

## Failure the skill must avoid

Answering with plausible config keys for a module that does not exist. The user burns a day wiring `ddd4j.extension.pdf.*` settings that nothing reads — invented APIs are the canonical failure this skill's NOT IMPLEMENTED rule prevents.
