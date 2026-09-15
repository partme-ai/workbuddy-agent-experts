# uHTTPd Config: Key UCI Options and Reachability

Sources: `package/network/services/uhttpd/files/uhttpd.config` + `uhttpd.init`, `package/network/config/firewall/files/firewall.config` (local snapshot, walkthrough 2026-09-02).

## Option → init flag mapping (uhttpd.init start_instance, L107-L223)

| UCI option | Flag | Default in uhttpd.config | Note |
|---|---|---|---|
| `listen_http` | `-p` (repeatable) | `0.0.0.0:80`, `[::]:80` | multiple list entries allowed |
| `listen_https` | `-s` | `0.0.0.0:443`, `[::]:443` | only active with ustream-ssl + cert/key present |
| `home` | `-h` | `/www` | docroot |
| `cgi_prefix` | `-x` | `/cgi-bin` | CGI searched under docroot |
| `rfc1918_filter` | `-R` | `1` | DNS-rebinding countermeasure (init passes flag only when value=1) |
| `max_requests` | `-n` | `3` | init fallback default is 3 (init L166) — CGI is serial; do not raise casually |
| `max_connections` | `-N` | `100` | queued beyond limit |
| `script_timeout` | `-t` | `60` | 504 when CGI/Lua/ucode writes nothing this long |
| `network_timeout` | `-T` | `30` | stalled connection kill |
| `http_keepalive` | `-k` | `20` | 0 disables persistent HTTP |
| `index_page` | `-I` (repeatable) | not set in config | init reads it (init L189-L192); binary default index file is not pinned by config — verify on target |
| `cert` / `key` | `-C` / `-K` | `/etc/uhttpd.crt` / `.key` | auto-generated via px5g/openssl when absent (init L34-L66) |
| `redirect_https` | `-q` | `0` | |
| `interpreter` | `-i` | — | extension→interpreter, usable outside cgi_prefix |
| `lua_prefix` / `ucode_prefix` | `-l/-L` / `-o/-O` | shipped: `/cgi-bin/luci` → LuCI Lua handler (config L58) | invalid handler files are skipped with a warning (init L83-L105) |

## Handler precedence gotcha

uhttpd.config comments (L52-L66) state it directly: Lua and ucode prefix matches **have precedence over the CGI prefix**. With LuCI installed, requests to `/cgi-bin/luci` are dispatched to the LuCI handler, not to a CGI script of yours — do not place a custom `cgi-bin/luci` script and expect it to run. Pick a different prefix for custom CGI.

## Firewall reachability (firewall.config)

```sh
config zone
	option name		lan
	list   network		'lan'
	option input		ACCEPT
	...
config zone
	option name		wan
	...
	option input		REJECT
```

(L9-L22.) Consequences: HTTP 80/443 and SSH 22 answer from LAN with zero additional rules; WAN input is REJECT, so external reachability requires an explicit rule or redirect — out of scope for defaults work.

## TinyNAS first-boot example (overlay, verified)

`50-tinynas-uhttpd` sets `rfc1918_filter=1`, `cgi_prefix=/cgi-bin`, `home=/www` only when missing, commits, exits 0. `index_page` is intentionally NOT set here: the S99 `tinynas-boot` state machine flips it between `tinynas-wizard.html` (unactivated) and `index.html` (activated) via `uci set uhttpd.main.index_page=...` + uHTTPd restart (tinynas-boot L11/L18). Two owners for one key would fight at every boot — keep single ownership.

## Debug checklist

- `uci show uhttpd.main` — confirm effective values, not the config file's comments.
- `/etc/init.d/uhttpd info` — dumps the procd instance JSON: the actual argv uHTTPd runs with.
- `logread | grep uhttpd` — start failures and skipped handlers show here.
- `netstat -lntp | grep -E ':80|:443'` — confirm listeners.
