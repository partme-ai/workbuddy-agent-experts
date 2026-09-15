# UART Basics for Box Recovery

Honesty note: host-side commands below are generic tooling; every board-side value (pin location, voltage tolerance, even baud) must be confirmed per board. Common Amlogic defaults are labeled as such. Walkthrough 2026-09-02; no board verified on hardware in this skill — `Pending HIL`.

## Electrical contract

- Adapter: USB-TTL (CP2102/CH340/FT232 class), logic level **3.3 V**.
- Never connect a 5 V TX to a board RX pad — level damage is immediate and irreversible.
- Wiring: adapter TX → board RX, adapter RX → board TX (crossed), GND ↔ GND. Do not connect the adapter's 3.3 V rail to the board unless a procedure explicitly requires it.
- Board-side pad locations are device-specific: use the board schematic or device-wiki photos; do not guess. Unverified pin claims must be marked `Pending HIL`.

## Connection parameters

| Parameter | Common Amlogic default | Confidence |
|---|---|---|
| Baud | 115200 | 常见值 — `Pending HIL / 需按板实测` |
| Format | 8N1 (8 data bits, no parity, 1 stop) | 常见值 — same caveat |
| Flow control | off | 常见值 — same caveat |

If the console prints garbage, step through common baud rates (115200, 1500000 — some Amlogic boot ROMs use 1.5 Mbaud) before concluding the board is dead. 1500000 is a known Amlogic alternative — treat as 常见值 to test, not a fact about any given board.

## Host-side terminal commands

```bash
ls /dev/ttyUSB*                     # find the adapter
screen /dev/ttyUSB0 115200          # macOS/Linux; detach: Ctrl-A k
picocom -b 115200 /dev/ttyUSB0      # alternative; exit: Ctrl-A Ctrl-X
# Windows: PuTTY → Serial → COMx, 115200, 8N1, flow none
```

Capture evidence to a file for later analysis: `screen /dev/ttyUSB0 115200 | tee boot-log.txt` or run picocom with `--logfile`.

## What the console tells you

| Console shows | Meaning | Next move |
|---|---|---|
| Nothing at power-on | No early boot output; wrong pads/baud, or boot ROM not talking | Re-check wiring/baud; then Tier 3 routing |
| Boot ROM + U-Boot logs, then kernel, then OpenWrt | System actually boots | Back to runtime triage (`logread`/`dmesg`) |
| Stops at a prompt ending `=>` | U-Boot alive, no kernel loaded | U-Boot command line (Tier 2); see mainline-U-Boot resistor note in the ladder reference |
| Repeated reset loop | Kernel panic / power issue | Capture the panic text; check power supply rating first |

## Runtime-period diagnosis (device boots, serial or SSH available)

- `logread | tail -50` — userspace/service failures (procd respawn messages appear here).
- `dmesg | tail -50` — kernel-side: storage errors, USB resets, thermal throttling.
- `ubus call system board; uptime` — confirm which image/kernel actually booted (catches "booted from USB, edited eMMC" confusion).
- Config-layer fixes belong to `openwrt-procd-init` / `openwrt-uci-defaults`; this reference only localizes the failing layer.
