# Example 3 — Three-state extension verification

## Prompt

> We claim our extensions are all optional: enable them per environment, disable without downtime, and slim deploys can drop the libraries. Prove each claim per extension.

## What the skill should do

1. Fix the line and enumerate the assembled extensions with their guards and switches read from that line's source.
2. Run the enabled state: context green, beans present, one real behavior per extension (an export, a QR render, an actor round-trip).
3. Run the disabled state: switch off, assert zero extension beans — including indicators, filters, and threads — and core still assembles.
4. Run the classpath-missing state: remove the third-party library and assert graceful skip, no `ClassNotFoundException`, no startup failure.
5. Report per extension and per state; anything not run is NOT RUN, and a claim backed by a failed state is withdrawn, not softened.

## Expected output

```
Three-state matrix (line 3.x):

            enabled        disabled           classpath-missing
  Excel     PASS export    PASS 0 beans       PASS graceful skip
  QRCode    PASS render    PASS 0 beans       NOT RUN (library kept)
  Monitor   PASS counter   FAIL indicator bean
                           survives the switch ← assembly not skipped
  Akka      PASS round-trip PASS 0 beans/threads PASS

Verdict: "disable without downtime" holds for 3 of 4; Monitor's off
switch skips one bean, not the assembly. Fix before shipping the claim.

Evidence: behavior TEST RUN (states as marked). CI: NOT RUN.
```

## Failure the skill must avoid

Testing only the enabled state and declaring the extensions optional. The disabled and classpath-missing states are where the claims actually live — and where Monitor's half-off switch fails.
