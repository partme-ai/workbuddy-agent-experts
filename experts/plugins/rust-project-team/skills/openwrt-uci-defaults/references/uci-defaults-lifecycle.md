# uci-defaults Lifecycle

Source of truth: OpenWrt `package/base-files/files/etc/init.d/boot` (local snapshot, walkthrough 2026-09-02). Line numbers refer to that file.

## Where uci-defaults runs in the boot chain

- `boot` is `START=10`, `STOP=90` (boot L4-L5) — uci-defaults are applied very early, before uHTTPd (S50) and rc.local (S95).
- Inside `boot()`: mount_root, /var population, kmodloader, then `uci_apply_defaults`, `sync`, `reload_config` (boot L22-L57).

## uci_apply_defaults, verbatim semantics (L7-L20)

```sh
uci_apply_defaults() {
	. /lib/functions/system.sh
	cd /etc/uci-defaults || return 0
	files="$(ls)"
	[ -z "$files" ] && return 0
	applied=""
	for file in $files; do
		( . "./$(basename $file)" ) && applied="$applied $file"
	done
	uci commit
	sync
	rm -f $applied
}
```

Facts an author must design around:

1. **Order** is plain `ls` output — lexicographic. Numeric prefixes (`10-`, `50-`, `99-`) control sequencing between your scripts.
2. **Each file runs in a subshell** `( . file )`. The file is *sourced*, so it must be valid POSIX shell; its exit status decides success.
3. **Only successful files are deleted.** A file whose last effective exit status is non-zero is left in place and re-executed at the next boot. This is the root cause of "runs every boot".
4. **One global `uci commit`** runs after all files. Individual scripts may still `uci commit <pkg>` (common practice), but the final commit is what persists stragglers.
5. **`sync` before delete**: success is durable, not just page-cache-deep.
6. Files run once per boot until success — there is no marker database; the file's absence is the marker.

## Consequences for script authors

- End every path with `exit 0`; guard optional targets with `uci -q` / `[ -f ... ] || exit 0` (verified pattern: TinyNAS `50-tinynas-uhttpd`).
- Idempotence probe: sourcing the file twice from a clean and from an already-configured state must both exit 0 and converge to the same config.
- Do not use `set -e`-style aborts as control flow; any failing intermediate command marks the whole file failed.
- Missing packages are a failure mode: `uci set foo.bar.baz` on a package whose `/etc/config/foo` does not exist errors out — guard on the file, or ship a preseeded config instead.
- Scripts run as root at S10, before user services: do not restart daemons from uci-defaults and expect them to stay; S50+ init scripts define the final runtime state (TinyNAS splits ownership this way: uci-defaults sets uhttpd basics; S99 `tinynas-boot` owns `index_page` and restarts services).

## Image interaction (conclusion)

Scripts placed in the Image Builder overlay `files/etc/uci-defaults/` land verbatim in the image and execute on the first boot of the flashed device. Overlay packaging details are owned by `openwrt-image-build`; this skill relies only on the conclusion.

## 常用首启项：系统时区

```sh
uci set system.@system[0].timezone='CST-8'
uci set system.@system[0].zonename='Asia/Shanghai'
```
（时区串为 POSIX TZ 格式；各区域取值以 OpenWrt 官方 timezone 表为准，运行时核验。）
