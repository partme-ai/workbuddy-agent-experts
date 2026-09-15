# procd Instance Params

Source of truth: OpenWrt `package/system/procd/files/procd.sh` (local snapshot, walkthrough 2026-09-02). Line numbers refer to that file.

## Instance skeleton

```sh
procd_open_instance [name]      # name defaults to instance1, instance2, ... (L143-L150)
procd_set_param <type> [args]   # see table below
procd_append_param <type> [args] # append to an existing array/table param (L473-L494)
procd_close_instance
```

## procd_set_param types (from `_procd_set_param`, L245-L274)

| Type | JSON shape | Notes |
|---|---|---|
| `command` | array | The argv. **One shell argument per argv element — no space splitting** (file header L28). |
| `respawn` | array (3 values) | `$fail_threshold $restart_timeout $max_fail` (header L15). |
| `env` | table | `KEY=value` string args, passed to the process. |
| `data` | table | Arbitrary name/value pairs for config-change detection. |
| `file` | array | Config files watched for changes. |
| `netdev` | array | Bound network devices (ifindex change detection). |
| `limits` | table | Resource limits passed to the process. |
| `user` / `group` | string | Drop privileges to this user/group. |
| `pidfile` | string | File to write the pid into. |
| `stdout` / `stderr` | boolean | Mirror process stdout/stderr into syslog (default 0, header L24-L25). |
| `facility` | string | Syslog facility, default `daemon` (header L26). |
| `nice`, `term_timeout` | int | Process priority; graceful-TERM timeout. |
| `reload_signal` | int (signal) | Signal used on reload (`kill -l` name or number, L263-L265). |
| `seccomp`, `capabilities`, `no_new_privs` | string/bool | Sandbox knobs; pair with jail usage. |

Respawn default: an empty `respawn` falls back to `system.@service[0]` UCI values `respawn_threshold/respawn_timeout/respawn_retry`, else `3600 5 5` (L496-L511).

## Canonical example (mapped from uhttpd.init, upstream-refs)

```sh
procd_open_instance
procd_set_param respawn                       # accept the 3600/5/5 defaults
procd_set_param stderr 1
procd_set_param command /usr/sbin/uhttpd -f   # argv: [uhttpd, -f]
procd_append_param command -h /www            # argv grows: [-h, /www]
procd_append_param command -x /cgi-bin
procd_append_param file /etc/uhttpd.crt       # watched file
procd_close_instance
```

The helper pattern `append_arg`/`append_bool` in `uhttpd.init` (L12-L32) is the standard way to translate UCI options into argv: omit the flag when the option is unset.

## Triggers and PROCD_RELOAD_DELAY

- `PROCD_RELOAD_DELAY=1000` (ms) is the module default (L45); `_procd_add_timeout` appends it to every generated trigger (L276-L279). Override the variable in your script before defining triggers to change the debounce.
- `service_triggers()` is called during `procd_close_service` (rc.common L99-L101, procd.sh L99-L110) — it only declares triggers, it never runs service code.
- Common builders (all wrapped as public functions, L686-L714):
  - `procd_add_reload_trigger <uci-package>` — fires `reload` on `config.change` of that package (L455-L465).
  - `procd_add_reload_interface_trigger <ifname>` — fires on interface events (L303-L310).
  - `procd_add_reload_mount_trigger <dir>...` / `..._restart_mount_trigger` — block-mount events (L429-L435).
  - `procd_add_raw_trigger <event> <timeout-ms> <script...>` — raw ubus event with custom handler (L437-L453).

## Validation helpers

- `uci_load_validate <pkg> <type> <sec> [<fn>] <opt:type>...` validates a UCI section and either returns or calls `<fn>` with the section name and validation result (L669-L684). Use it at the top of `start_instance()` style loops to fail fast on malformed config.
- `procd_running <service> [<instance>]` — true when the instance reports running via ubus (L519-L529).

## Debugging

- `PROCD_DEBUG=1` dumps the JSON message to stderr before the ubus call (L78-L84).
- `/etc/init.d/<svc> info` prints the live service JSON; `/etc/init.d/<svc> trace` enables syscall tracing of the next start (rc.common L144-L154).
