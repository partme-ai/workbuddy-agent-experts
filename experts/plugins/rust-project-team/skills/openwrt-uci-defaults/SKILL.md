---
name: openwrt-uci-defaults
license: Apache-2.0
description: Author idempotent first-boot configuration for OpenWrt images via /etc/uci-defaults scripts, and choose between uci-defaults deltas and preseeded final /etc/config files. Cover the init.d/boot lifecycle (executed at S10 on first boot, deleted on success, kept and re-run on failure), numeric-prefix ordering, uHTTPd key UCI options (docroot /www, cgi_prefix, rfc1918_filter, max_requests, script_timeout, lua/ucode prefix precedence over CGI), and firewall lan-zone defaults that make ports 80/22 reachable with zero extra config. Use when the user asks how to 首次开机改默认配置 / set factory defaults / preseed UCI config in an image, when a uci-defaults script runs on every boot or is never deleted, or when uHTTPd does not serve or reach the web root as expected. Route init.d/procd service scripts to openwrt-procd-init, and Image Builder overlay layout, FILES= handling, and image reproducibility to openwrt-image-build.
---

# OpenWrt uci-defaults and First-Boot Config

First-boot configuration must be deterministic and idempotent: `/etc/uci-defaults` scripts run at boot S10 and are deleted only when they exit success (boot `uci_apply_defaults`, boot L7-L20). Anything non-idempotent will re-run forever. All mechanics below are verified against the local OpenWrt source snapshot (see Offline Baseline).

## Determine Task Type

| If the user wants to... | Path |
|---|---|
| Change default UCI values on first boot of a flashed image | uci-defaults script → Workflow A |
| Ship a complete known-good `/etc/config/<pkg>` from scratch | Preseeded final file → Workflow B |
| Diagnose "my uci-defaults runs every boot" | Workflow C |
| Make uHTTPd serve a custom docroot/CGI | Workflow A + [uHTTPd Config](references/uhttpd-config.md) |
| Write an init.d service script | Hand-off → `openwrt-procd-init` |

## Prerequisites / Preflight

On the target device (or its image manifest):

```bash
cat /etc/openwrt_release                  # release matches baseline below
ls -l /etc/uci-defaults/                  # leftover scripts = pending/failed work
uci show uhttpd.main 2>/dev/null | head   # current uHTTPd state
uci -q get firewall.@zone[0].name         # expect: lan (input ACCEPT)
```

No device in hand → deliver scripts + verification commands marked `Build Verification Only`. Do not claim first-boot-tested behavior.

## Offline Baseline

Verified 2026-09-02 against the local OpenWrt source snapshot (workspace `upstream-refs/openwrt`; convention baseline OpenWrt 25.12.5). Key sources: `package/base-files/files/etc/init.d/boot` (uci_apply_defaults), `package/network/services/uhttpd/files/uhttpd.config` + `uhttpd.init`, `package/network/config/firewall/files/firewall.config`. TinyNAS overlay samples: `openwrt-imagebuilder/common/tinynas-files/`. This skill does not auto-update.

## Contracts

- `/etc/uci-defaults/<NN-name>` scripts are plain `#!/bin/sh`, run once at boot S10 in `ls` (lexicographic) order, inside a subshell per file (boot L14-L16).
- Success = the file's exit status is 0. Only then is it appended to the delete list; `uci commit` runs once after all files, then `sync`, then successful files are removed (boot L14-L19). Failures stay and re-run next boot.
- Idempotence is mandatory: every script must tolerate being executed any number of times, and must end with `exit 0` even on "already done" paths.
- The lan firewall zone ships `input ACCEPT` (firewall.config L9-L14): uHTTPd 80/443 and dropbear 22 are reachable from LAN with zero extra firewall config. Do not add redundant "allow 80 from lan" rules.
- First-boot behavior claims without a device test are `Pending HIL`.

## Capability Boundaries and Hand-off

Read only the reference needed for the current task:

| Task | Reference |
|---|---|
| Lifecycle details, failure semantics, ordering, why files re-run | [uci-defaults Lifecycle](references/uci-defaults-lifecycle.md) |
| uHTTPd UCI option table, handler precedence, firewall reachability | [uHTTPd Config](references/uhttpd-config.md) |
| Preseeded final file vs uci-defaults delta trade-offs | [Preset vs Defaults](references/preset-vs-defaults.md) |

Beyond-scope intents route to another skill:

| User intent | Route to |
|---|---|
| init.d service scripts, procd instances, START ordering | `openwrt-procd-init` |
| Overlay layout, `FILES=`, `DISABLED_SERVICES`, image build determinism | `openwrt-image-build` |
| Device flashing/recovery, U-Boot, TTL console | `openwrt-serial-recovery` |

## Workflow A — idempotent uci-defaults script

1. Name it `<NN>-<purpose>` (e.g. `50-tinynas-uhttpd`); order matters only between your own scripts — they run in `ls` order.
2. Guard what you touch, write only missing values, and always exit 0 (verified TinyNAS pattern, `etc/uci-defaults/50-tinynas-uhttpd`):

```sh
#!/bin/sh
# 50-tinynas-uhttpd — first-boot idempotent config (deleted by init.d/boot on success)
[ -f /etc/config/uhttpd ] || exit 0
uci -q get uhttpd.main.rfc1918_filter >/dev/null || uci set uhttpd.main.rfc1918_filter='1'
uci -q get uhttpd.main.cgi_prefix   >/dev/null || uci set uhttpd.main.cgi_prefix='/cgi-bin'
uci -q get uhttpd.main.home         >/dev/null || uci set uhttpd.main.home='/www'
uci commit uhttpd
exit 0
```

3. Do not hard-write keys that a boot-time init script owns. In the TinyNAS overlay, `index_page` is managed by the S99 `tinynas-boot` state machine; the uci-defaults script deliberately leaves it alone.
4. Place the script under `files/etc/uci-defaults/` in the Image Builder overlay. Packaging and `FILES=` mechanics → `openwrt-image-build`.
5. Verify on first boot: `ls /etc/uci-defaults/` no longer lists the script, `uci get uhttpd.main.home` returns the new value, and the web root answers on :80 from LAN.

## Workflow B — preseeded final /etc/config file

When a package's entire config is yours from day one (e.g. the overlay's `etc/config/samba4`, `etc/config/minidlna`), ship the final file directly instead of patching via uci-defaults. Decision criteria, upgrade interactions, and the mixed-mode rules are in [Preset vs Defaults](references/preset-vs-defaults.md).

## Workflow C — "my uci-defaults script runs every boot"

1. `ls -l /etc/uci-defaults/` — if the script is still there, it failed (or was never successful) and boot keeps it by design (boot L14-L19).
2. Run it by hand and check the exit code: `( . /etc/uci-defaults/50-mine ); echo $?`. Any non-zero command chain (missing file, failing `uci` on a package not yet installed, a stray `set -e`) aborts before `exit 0`.
3. Check idempotence: run it twice by hand; the second run must still exit 0 and produce no config drift.
4. Fix, then either let the next boot consume it or run `rm /etc/uci-defaults/<file>` after verifying the effect manually.
5. Do not "solve" re-runs by making the script delete itself — deletion is boot's job conditioned on success.

## Validation Gates

```bash
sh -n files/etc/uci-defaults/*                             # syntax gate (host)
for f in files/etc/uci-defaults/*; do sh -e "$f" && sh -e "$f"; done   # double-run = idempotence probe (staged env only)
# On device after first boot:
[ -d /etc/uci-defaults ] && ls /etc/uci-defaults           # expect empty (or only known-failed files)
uci get uhttpd.main.home                                   # expect the value you set
curl -sI http://<device-ip>/ | head -1                     # expect HTTP/1.1 200/301 from LAN
```

Host-side double-run is `Build Verification Only`; the authoritative gate is first boot on the target (`Pending HIL` until then).

## Pitfalls

- Do not write a script that exits non-zero on the "already configured" path; that is the classic every-boot re-run bug.
- Do not depend on network in uci-defaults (no curl/wget/opkg). First boot may have no WAN, and pulling remote content breaks image determinism; route such needs to build-time packaging.
- Do not commit secrets (keys, passwords) into uci-defaults; they live in the image and in every backup/sysupgrade archive unless overwritten.
- Do not assume per-file `uci commit` ordering across scripts: boot runs one global `uci commit` after all scripts (boot L17); per-package commits inside scripts are allowed but do not replace it.
- Do not patch keys owned by a boot-order init script (e.g. TinyNAS `index_page` owned by S99 `tinynas-boot`); encode ownership in comments and pick one owner.
- Do not add firewall "allow 80/22 from lan" rules — lan already has `input ACCEPT` (firewall.config L12); extra rules just mislead readers.
- Do not test uci-defaults with `uci set` on a live box and then reuse the same script unchanged: verify the script alone reproduces the state from the package default.

## Official Sources

- uci-defaults guide: https://openwrt.org/docs/guide-developer/uci-defaults
- uHTTPd documentation: https://openwrt.org/docs/guide-user/services/webserver/http.uhttpd
- Firewall configuration: https://openwrt.org/docs/guide-user/firewall/firewall_configuration
- boot script source: https://github.com/openwrt/openwrt/blob/main/package/base-files/files/etc/init.d/boot

## Privacy

This skill does not collect, store, or transmit user data. uci-defaults and preseeded configs are part of the distributed image — never embed credentials, license material, or personal endpoints in them; inject secrets at activation time instead.

> **供应链红线**：uci-defaults 脚本在首启以 **root**（S10）执行——任何“脚本里 curl 远程内容再执行/写入配置”的模式 = 以 root 运行不受审计的远程代码（供应链+隐私双重风险），且破坏镜像确定性。配置必须构建期内置。
