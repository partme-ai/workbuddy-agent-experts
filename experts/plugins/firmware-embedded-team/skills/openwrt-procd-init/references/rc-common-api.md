# rc.common API

Source of truth: OpenWrt `package/base-files/files/etc/rc.common` (local snapshot, walkthrough 2026-09-02, baseline 25.12.5). Line numbers below refer to that file.

## Execution model

- Init scripts are not executed directly. The shebang `#!/bin/sh /etc/rc.common` means the kernel execs `/etc/rc.common <initscript> <action>`; `rc.common` sets `initscript=$1`, `action=${2:-help}`, then sources the initscript (L7-L9, L119) and finally runs `$action "$@"` (L190).
- Sourcing order defines override rules:
  1. rc.common defines default actions first (L11-L107).
  2. The initscript is sourced (L119) — definitions in the initscript replace the defaults.
  3. If `USE_PROCD` is non-empty, the procd block redefines `start/stop/reload/trace/info/status/running` afterwards (L121-L185) — the initscript's same-named functions are discarded.

## Default actions (plain scripts)

| Action | Default behavior | Line |
|---|---|---|
| `start` / `stop` | `return 0` (no-op) | L11-L16 |
| `reload` | `restart` | L19-L21 |
| `restart` | `stop` then `start` (TERM trapped during stop) | L23-L28 |
| `boot` | `start` | L30-L32 |
| `shutdown` | `stop` | L34-L36 |
| `depends` | `return 0` | L66-L68 |

`extra_command "<cmd>" "<help>"` registers additional actions and help text (L72-L79). The procd block uses it to add `running`, `status`, `trace`, `info` (L122-L125).

## enable / disable / enabled

```sh
enable() {
	err=1
	name="$(basename "${initscript}")"
	[ "$START" ] && ln -sf "../init.d/$name" "$IPKG_INSTROOT/etc/rc.d/S${START}..." && err=0
	[ "$STOP" ] && ln -sf "../init.d/$name" "$IPKG_INSTROOT/etc/rc.d/K${STOP}..." && err=0
	return $err
}
```

(L44-L54, names elided; see source for exact link-name arithmetic.)

- `S<START><name>` is created only if `START` is set; `K<STOP><name>` only if `STOP` is set; `enable` fails (rc=1) when neither is set.
- `disable()` removes both link families (L38-L42).
- `enabled()` re-checks link existence for the declared `START`/`STOP` (L56-L64) — use `/etc/init.d/<name> enabled; echo $?` as the idempotence gate.
- `$IPKG_INSTROOT` lets the same calls run against a staged rootfs (build-time) instead of the live system.

## USE_PROCD=1 overrides (what actually runs)

| Command | Implementation | Line |
|---|---|---|
| `start` | `rc_procd start_service` (builds the ubus service blob around `start_service()`), then optional `service_started` hook | L128-L142 |
| `stop` | `procd_lock`, `stop_service()`, then `procd_kill <service>` | L156-L163 |
| `reload` | `reload_service()` if defined, else `start` | L165-L172 |
| `running` | `service_running()` → `procd_running` | L174-L177 |
| `status` | `status_service()` if defined, else `_procd_status` (prints `running` / `not running` / `inactive` with rc 0/5/3) | L178-L184, procd.sh L557-L602 |
| `trace` | sets `TRACE_SYSCALLS=1` then starts (syscall tracing of the instance) | L144-L147 |
| `info` | dumps the service JSON from ubus `service list` | L149-L154 |

`rc_procd` names the service after the realpath of the init script (`basename $(readlink ...)`), so symlinked duplicates map to one service (L128-L135).

## Required function set for procd scripts

Author-provided: `start_service()` (mandatory to do anything), optional `stop_service()`, `reload_service()`, `service_triggers()`, `service_running()`, `service_started`, `service_stopped`, `status_service()`, `service_data()`. Defaults are no-ops (L90-L101).
