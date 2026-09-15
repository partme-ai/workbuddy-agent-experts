# Example 1 — Sa-Token integration through ddd4j-boot

## Prompt

> Our Boot 3 service needs login and role checks. The team already knows Sa-Token. Wire it through ddd4j-boot so our domain code still sees the ddd4j Subject.

## What the skill should do

1. Fix the maintenance line, then read the auth AutoConfiguration and Properties on that line.
2. Select Sa-Token as the primary framework and assemble it via the boot auth configuration (artifact, prefix, default beans).
3. Bridge to the domain: the assembled `SubjectProvider` populates the ddd4j `Subject` so domain code stays framework-agnostic.
4. Map Sa-Token's auth exceptions onto the web error contract (401 for not-logged-in, 403 for insufficient role).
5. Prove it with the behavior matrix: anonymous, valid, expired, insufficient-role, logout, thread reuse.

## Expected output

```
Selection: Sa-Token (primary SubjectProvider), via ddd4j-boot auth
auto-configuration on line 3.x.

Wiring:
  - configuration prefix: <as defined by the line's Properties>
  - default beans assembled with @ConditionalOnMissingBean (user can replace)
  - SubjectProvider bridges Sa-Token session → ddd4j Subject
  - exception mapping: NotLoginException → 401, role deficiency → 403

Behavior matrix: anonymous PASS, valid PASS, expired PASS,
insufficient-role PASS, logout PASS, thread-reuse (no leak) PASS.

Evidence: SOURCE + context/behavior TEST RUN.
```

## Failure the skill must avoid

Letting domain code call Sa-Token APIs directly "since it's simpler". The SubjectProvider bridge is the whole point — without it, the account model is welded to Sa-Token and the next framework swap is a rewrite.
