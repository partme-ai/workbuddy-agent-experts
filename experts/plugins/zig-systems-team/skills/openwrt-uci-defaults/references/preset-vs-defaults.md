# Preset Final Files vs uci-defaults Deltas

Verified overlay samples: `openwrt-imagebuilder/common/tinynas-files/etc/config/{samba4,minidlna}` and `etc/uci-defaults/50-tinynas-uhttpd`. Walkthrough 2026-09-02.

## The two routes

| Route | What ships | TinyNAS example |
|---|---|---|
| A. Preseeded final file | Complete `/etc/config/<pkg>` in the overlay; package default is replaced wholesale | `etc/config/samba4`, `etc/config/minidlna` |
| B. uci-defaults delta | Small script patching only chosen keys onto the package's own default config | `etc/uci-defaults/50-tinynas-uhttpd` |

## Decision table

| Situation | Use |
|---|---|
| Package config is entirely yours from day one; you can author every needed section | A |
| You only tweak a few keys of a package default (e.g. uhttpd basics) | B |
| Keys are re-managed at runtime by a boot-order init script | B (and exclude those keys) — or own them fully in A + remove the runtime manager |
| Config must not fight sysupgrade-merge behavior or package upgrades that extend defaults | B |
| Config must be bit-for-bit deterministic across builds (reviewable diffs, no script execution risk) | A |

## Route A mechanics and gotchas

- The overlay file replaces the package's `/etc/config/<pkg>` at image assembly. Anything the package's default config provided (sections,注释-level documentation values) is gone — you must ship every section the init script reads.
- Verified sample (`etc/config/minidlna`): `enabled '1'`, `friendly_name`, multiple `media_dir` list entries, `db_dir` under `/etc/tinynas`, `port '8200'`. Note the list syntax: repeated `option media_dir` lines are a UCI list.
- Verified sample (`etc/config/samba4`): `read_only 'yes'` at the `[0]` samba section is a *default-locked* posture that the S99 `tinynas-boot` flips at runtime (`uci -q set samba4.@samba[0].read_only=...`). This is Route A plus a runtime owner — acceptable because ownership is explicit and single.
- Package upgrades that add new default options will not retrofit your preseeded file; audit on upgrade.

## Route B mechanics and gotchas

- Guard-then-set (`uci -q get ... || uci set ...`) keeps the script idempotent and preserves anything the user changed after install — but remember the script only runs until first success; later user edits are never touched by it again.
- One global `uci commit` happens at the end of `uci_apply_defaults`; per-package commits inside scripts are fine (see lifecycle reference).
- Keep keys owned by init scripts out of Route B (the TinyNAS `index_page` rule).

## Mixed mode (TinyNAS reality)

TinyNAS uses A for samba4/minidlna (full ownership, deterministic share layout) and B for uhttpd (patch a few keys of a package default, leave runtime-owned keys alone). The mixing rule: per package, every key has exactly one owner (preseed file, uci-defaults script, or boot-order init script) — never two.
