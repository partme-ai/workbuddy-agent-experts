# Example 4 — Bean up but service down (evidence boundary)

## Prompt

> The context starts and our ddd4j-boot MQ beans are all created, so the broker integration is working now, right? We just need a sign-off.

## What the skill should do

1. Refuse the sign-off: bean creation proves assembly, not external-service availability — the configuration can be perfectly wired while the broker is unreachable.
2. Separate the evidence layers explicitly: configuration presence, bean creation, behavior tests, CI, publish.
3. Prescribe the missing behavior evidence: a real send/receive contract test against the broker (or an explicit statement that it was skipped and is NOT VERIFIED).
4. Do not fabricate a passing check; mark what was not run as NOT RUN or BLOCKED.
5. If connectivity is indeed broken, route diagnosis to the matching feature skill rather than to wiring changes.

## Expected output

```
Evidence ledger:
  configuration presence   REACHED  — registered for this Boot line
  bean creation            REACHED  — context starts, beans exist
  behavior (broker I/O)    NOT RUN  — no send/receive contract test executed
  CI                       NOT RUN for this SHA

Sign-off: DECLINED. Wiring evidence only. A green context cannot prove
broker availability — run the contract test, then re-request sign-off.
```

## Failure the skill must avoid

Signing off because "the context came up." The exact failure this skill prevents is treating dependency or bean presence as real behavior — the first production message would have been the actual test.
