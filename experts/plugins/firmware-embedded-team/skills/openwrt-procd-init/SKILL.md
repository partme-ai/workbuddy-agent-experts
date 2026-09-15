---
name: openwrt-procd-init
license: Apache-2.0
description: Write, register, and debug OpenWrt init scripts in /etc/init.d using rc.common and the procd service manager. Cover the #!/bin/sh /etc/rc.common shebang contract, START/STOP boot-order wiring, enable/disable autostart semantics, USE_PROCD=1 services with procd_open_instance and procd_set_param (command array, respawn, env, file, limits), service_triggers with PROCD_RELOAD_DELAY, and S00-S99 startup-order placement relative to boot(S10), uhttpd(S50), and done/rc.local(S95). Use when the user asks how to 写开机自启脚本 / 写 init.d 服务 / 让服务开机自动运行, when a procd instance keeps respawning, when /etc/init.d/<name> start works manually but not at boot, or when choosing a START number for a custom service. Route first-boot UCI configuration in /etc/uci-defaults to openwrt-uci-defaults, and Image Builder overlay packaging, auto-enable internals, or DISABLED_SERVICES to openwrt-image-build.
---

# OpenWrt procd Init Scripts

Author init scripts against the actual `rc.common` + `procd.sh` contract, not generic SysV assumptions. All mechanics below were verified against the local OpenWrt source snapshot on 2026-09-02 (see Offline Baseline); cite line numbers when they drive a decision.

## Determine Task Type

| If the user wants to... | Path |
|---|---|
| Run a daemon at boot with supervision | procd service (`USE_PROCD=1`) → Workflow A |
| Run a one-shot boot action (state fixup, license check) | plain rc.common script with `boot()` override → Workflow B |
| Make an existing script start at boot / diagnose "not effective at boot" | Workflow C (troubleshooting) |
| Configure UCI defaults on first boot | Hand-off → `openwrt-uci-defaults` |
| Package the script into an image / control auto-enable | Hand-off → `openwrt-image-build` |

## Prerequisites / Preflight

Run on the target device (or confirm from its image manifest):

```bash
cat /etc/openwrt_release          # confirm release matches the baseline below
head -n1 /etc/rc.common           # expect: #!/bin/sh
command -v procd ubus             # procd runtime must exist
ls -l /etc/rc.d/                  # current boot-order links (read-only inspection)
/etc/init.d/uhttpd info 2>/dev/null | head -5   # sanity: procd ubus service listing
```

If you cannot reach a device, produce scripts + validation commands and mark the result `Build Verification Only` until run on hardware. Do not claim boot-tested behavior.

## Offline Baseline

Verified 2026-09-02 against local OpenWrt source snapshot (workspace `upstream-refs/openwrt`, Luci `128a7812f4be`, packages `5caa62e0bc`), convention baseline OpenWrt 25.12.5. This skill does not auto-update. Key sources: `package/base-files/files/etc/rc.common`, `package/system/procd/files/procd.sh`, `package/base-files/files/etc/init.d/{boot,done}`, `package/base-files/files/etc/inittab`.

## Contracts

- Init scripts are BusyBox ash (`/bin/sh`), not bash. No arrays, no `local -n`, no bashisms.
- A valid init script starts with `#!/bin/sh /etc/rc.common`. The kernel interprets this as `/etc/rc.common <script> <action>` (rc.common L7-L9, L119).
- `enable()` creates `/etc/rc.d/S<START><name>` only when `START` is set; it returns error 1 when neither `START` nor `STOP` is set (rc.common L44-L54).
- `USE_PROCD=1` hands execution to procd via ubus; `start()` is redefined to call `start_service()` (rc.common L121-L142). procd supervises, respawns, and reports the process.
- Examples in this skill are source-verified; end-to-end boot behavior is `Pending HIL` until exercised on the target device.

## Capability Boundaries and Hand-off

Read only the reference needed for the current task:

| Task | Reference |
|---|---|
| Action names, override order, enable/disable/enabled semantics, extra_command | [rc.common API](references/rc-common-api.md) |
| procd_set_param parameter table, respawn defaults, triggers, PROCD_RELOAD_DELAY | [procd Instance Params](references/procd-instance.md) |
| Picking START/STOP numbers, S00-S99 anchor map, TinyNAS S98/S99 case study | [Start Order](references/start-order.md) |

Beyond-scope intents route to another skill:

| User intent | Route to |
|---|---|
| First-boot UCI changes, /etc/uci-defaults scripts, uHTTPd/firewall defaults | `openwrt-uci-defaults` |
| Overlay layout, `DISABLED_SERVICES`, IB auto-enable internals, image reproducibility | `openwrt-image-build` |
| Amlogic box flashing/recovery, U-Boot, TTL console | `openwrt-serial-recovery` |
| Board-specific bring-up verification on real hardware | `fw-hil-testing` |

Command mechanics stay in this skill even when the higher-level decision belongs elsewhere.

## Workflow A — procd-managed daemon

1. **Choose the START number** from the anchor table ([Start Order](references/start-order.md)). Daemons needing network/disks: `START=95`..`START=99` is safe; set `STOP` lower than `START` so shutdown stops them early.
2. **Write the script** — every command-line argument is one shell argument (procd.sh L28):

```sh
#!/bin/sh /etc/rc.common
# /etc/init.d/myagent — minimal procd service
USE_PROCD=1
START=99
STOP=10

start_service() {
    procd_open_instance
    procd_set_param command /usr/bin/myagent
    procd_append_param command --config /etc/myagent.toml   # one arg per call
    procd_set_param respawn                                  # defaults: 3600 5 5
    procd_set_param stdout 1                                 # mirror stdout to syslog
    procd_set_param stderr 1
    procd_close_instance
}

service_triggers() {
    procd_add_reload_trigger "myagent"                       # config change -> reload
}
```

3. **Register and start on-device**:

```bash
/etc/init.d/myagent enable       # needs START, else fails silently with rc=1
ls -l /etc/rc.d/S99myagent       # expect the symlink
/etc/init.d/myagent restart
/etc/init.d/myagent status       # expect: running
logread | grep -i procd | tail
```

4. **Reload path**: define `reload_service()` for a no-restart reload; with only `service_triggers()` + `reload_trigger`, a config change calls `/etc/init.d/<name> reload`, which defaults to `start()` (rc.common L165-L172).

## Workflow B — one-shot boot action (no procd)

Plain rc.common scripts may override `boot()`/`start()` directly; definitions in the script replace rc.common defaults because the script is sourced last (rc.common L119). Verified pattern from the TinyNAS overlay (`tinynas-boot`, `tinynas-license-check`): no `USE_PROCD`, `boot(){ ... }`, idempotent body, `logger -t <tag>` for observability, defensive `2>/dev/null` on restarts of optional services. See [Start Order](references/start-order.md) for the S98/S99 ordering rationale. Do not block forever in these functions; boot waits on them.

## Workflow C — "my init script did not take effect at boot"

Check in this order; each step maps to a verified mechanism:

1. `head -n1 /etc/init.d/<name>` — must be `#!/bin/sh /etc/rc.common`. Scripts without this shebang are not init scripts at all.
2. Is `START` (or `STOP`) assigned? Without them `enable()` returns 1 and creates no link (rc.common L44-L54).
3. `ls -l /etc/rc.d/ | grep <name>` and `/etc/init.d/<name> enabled; echo $?` — the link must exist before boot will run it.
4. Starts manually but not at boot → it is an enable/order problem, not a script problem. Re-check START against dependencies ([Start Order](references/start-order.md)).
5. Starts then dies → `logread | grep procd`; inspect respawn behavior ([procd Instance Params](references/procd-instance.md)); run `/etc/init.d/<name> trace` for syscall tracing.

## Validation Gates

```bash
sh -n /etc/init.d/<name>                          # syntax gate (host or device)
command -v shellcheck >/dev/null && shellcheck -s sh /etc/init.d/<name>
/etc/init.d/<name> enable && [ -L "/etc/rc.d/S$(sed -n 's/^START=//p' /etc/init.d/<name>)<name>" ]
/etc/init.d/<name> status                         # expect "running" after start
```

Build-side gate: the image overlay must NOT contain `/etc/rc.d/` entries. The Image Builder auto-enables init scripts that carry the rc.common shebang during rootfs preparation; disabling is done via `DISABLED_SERVICES`, not by hand-creating links. Deep dive → `openwrt-image-build`.

## Pitfalls

- Do not pass a whole command line as one quoted string to `procd_set_param command`; arrays take one function argument per argv element (procd.sh L28). Do not assume space splitting.
- Do not define `start()`/`stop()` in a `USE_PROCD=1` script — the procd block redefines them after sourcing your script, so your versions are silently discarded (rc.common L121-L185). Write `start_service()`/`stop_service()`/`reload_service()`.
- Do not call `/etc/init.d/<name> enable` on a script without `START` and expect success; it fails by design.
- Do not hand-write `/etc/rc.d/S..` links into an image overlay or commit them to the build tree; Image Builder auto-enable is the mechanism, `DISABLED_SERVICES` is the opt-out.
- Do not assume `reload` is lighter than `restart` by default: rc.common's default `reload()` is `restart` (L19-L21); only a `reload_service()` definition changes that.
- Do not tune respawn blindly: `procd_set_param respawn` with no values falls back to `system.@service[0]` UCI or 3600/5/5 (threshold/timeout/retry) (procd.sh L496-L511). A crash-looping service gives up after 5 failures — do not "fix" that by disabling respawn.
- Do not sleep inside `service_triggers()` to delay reload; set `PROCD_RELOAD_DELAY` (default 1000 ms) which procd.sh appends to every trigger (procd.sh L45, L276-L279).
- Do not block in a one-shot `boot()` override waiting on network or disks; the boot chain is sequential.

## Official Sources

- procd init scripts guide: https://openwrt.org/docs/guide-developer/procd-init-scripts
- Init script reference: https://openwrt.org/docs/techref/initscripts
- rc.common source: https://github.com/openwrt/openwrt/blob/main/package/base-files/files/etc/rc.common
- procd.sh source: https://github.com/openwrt/openwrt/blob/main/package/system/procd/files/procd.sh

## Privacy

This skill does not collect, store, or transmit user data. Init scripts may embed hostnames, network topology, or credentials in UCI/config files — treat device logs (`logread`), overlays, and configs as sensitive and never paste secrets into issues or examples.
