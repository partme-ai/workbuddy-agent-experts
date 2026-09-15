# Start Order: S00-S99 Anchors and TinyNAS Case

Sources: `package/base-files/files/etc/inittab`, `package/base-files/files/etc/init.d/{boot,done}`, upstream `uhttpd.init`, plus the TinyNAS overlay (`openwrt-imagebuilder/common/tinynas-files/etc/init.d/`). Walkthrough 2026-09-02.

## How ordering works (verified chain)

1. `inittab` runs `::sysinit:/etc/init.d/rcS S boot`; shutdown runs `rcS K shutdown`.
2. `rcS` executes the `/etc/rc.d/S[0-9][0-9]*` symlinks created by `enable()` in lexicographic order; `K*` links run in reverse sense at shutdown.
3. Consequence: ordering is **string** ordering — `S10` < `S50` < `S95` < `S98` < `S99`. Boot is sequential; a blocking S99 delays everything after it.

## Verified anchors

| Seq | Script | Verified fact |
|---|---|---|
| S10 | `boot` | `START=10`, `STOP=90`; runs `mount_root`, kmodloader, then `uci_apply_defaults` (all /etc/uci-defaults), then `reload_config` (boot L4, L52-L56) |
| S50 | `uhttpd` | `START=50`, `USE_PROCD=1` (uhttpd.init L4-L6) |
| S95 | `done` | `START=95`; `mount_root done`, then executes `/etc/rc.local`, then LEDs (done L4-L17) |
| S98 | `tinynas-license-check` | `START=98`, `STOP=10`; fingerprint re-check before the S99 state machine |
| S99 | `tinynas-boot` | `START=99`, `STOP=90`; applies activation state, restarts uhttpd/samba4/minidlna |

Anything else on a given device (network, firewall, dnsmasq numbers) must be read from `ls /etc/rc.d/` on that device — do not assume a universal table.

## Choosing START for a custom service

- Daemon needing network + disks: `START=96`..`START=99` keeps it after uHTTPd (S50) and after rc.local (S95). `STOP=10`..`STOP=90` so shutdown tears it down before core services.
- One-shot state fixup that other S9x scripts depend on: place it immediately before its consumer (the TinyNAS pattern: S98 check → S99 state apply).
- If the action is "user commands after everything else", prefer appending to `/etc/rc.local` (runs inside S95 `done`) instead of a new S96+ script.
- Do not pick START numbers below 50 for services that call `uci commit` + service restarts; they run before uci-defaults consumers are up. (boot S10 owns `uci_apply_defaults`.)

## TinyNAS S98/S99 case study (overlay-verified)

- `tinynas-license-check` (S98, STOP=10): plain rc.common script, `boot(){ start; }`, no USE_PROCD. Exits 0 immediately when unactivated; logs via `logger -t tinynas`; a missing helper tool logs an error and keeps state instead of failing.
- `tinynas-boot` (S99, STOP=90): plain rc.common, overrides `boot()`/`start()`/`restart()` to one idempotent `apply_state`; restarts optional services with `2>/dev/null`; every path ends in a `logger` line.

Lessons: one-shot scripts stay plain rc.common; idempotence and logging are mandatory; ordering encodes the dependency (check → apply), not convenience.

## Image Builder auto-enable (conclusion only)

The Image Builder auto-enables overlay init scripts that carry the `#!/bin/sh /etc/rc.common` shebang during rootfs preparation, and `DISABLED_SERVICES` disables listed services instead. Never hand-place `/etc/rc.d/` links inside a `files/` overlay — the build treats that directory as build-managed. Internals and reproducing this behavior are the deep-dive area of the `openwrt-image-build` skill; this skill only relies on the conclusion above.
