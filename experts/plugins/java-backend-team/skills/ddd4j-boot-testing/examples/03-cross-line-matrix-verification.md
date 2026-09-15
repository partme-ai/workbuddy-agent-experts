# Example 3 — Cross-line matrix verification

## Prompt

> We fixed a cache wiring bug and tested on the 3.5 line — all green. Do we really have to re-verify on the other lines before the fix ships? That's so much work.

## What the skill should do

1. Answer directly: yes for every line the fix ships to — the 13 maintenance lines span Boot 2.3–4.1 and do not share fixtures or APIs; the matrix exists because per-line verification is not optional.
2. Fix the applicable line set from the version-selection matrix (which lines consume the patched module).
3. Plan the minimal per-line suite: the `ApplicationContextRunner` wiring cases plus one behavior round-trip — not the entire suite on every line.
4. Execute per line and record line/JDK/Maven alongside each result; differences per line are findings, not noise.
5. Report the matrix with per-line evidence status; a line not yet run is UNVERIFIED, not assumed-fine.

## Expected output

```
Fix: cache off-switch assembly bug (ships to 2.7.x, 3.5.x, 4.0.x)

Per-line minimal suite (runner cases + one round-trip):
  2.7.x  JDK 8   Maven 3  wiring PASS  round-trip PASS
  3.5.x  JDK 17  Maven 3  wiring PASS  round-trip PASS
  4.0.x  JDK 21  Maven 4  wiring FAIL — Boot 4 reads the imports file
                          the 2.x fixture patches  ← real finding

The 4.0.x failure is the point: the fixture was line-specific. Without
the matrix run, that failure ships.

Evidence: TEST RUN on 3 of 3 shipping lines (after fixture fix).
```

## Failure the skill must avoid

Shipping on the strength of one line's green run. The Boot 4 registration mechanism differs from Boot 2/3 — exactly the kind of line-specific breakage the matrix pass exists to catch before release.
