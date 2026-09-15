此文保留上游扩展流程及代码示例，属于按需参考。先读 [中文入口](../SKILL.md) 的范围、权限、来源和验证约束。历史工具名与参数必须以实际连接的 schema 和目标依赖版本核对；英文示例为结构演示，不是业务事实或已经执行的结果。

# Stitch to React + Vite Dashboard

You are a frontend engineer building **data-dense dashboards** from Stitch screens. Respect the target project's installed versions. Reference stack: **React**, **Vite**, **TypeScript**, **TanStack Query**, **React Router**, and optional **ethers v6** or **viem** for on-chain reads.

## Prerequisites

- Stitch MCP configured ([setup guide](https://stitch.withgoogle.com/docs/mcp/setup/))
- A project `DESIGN.md` (see the `stitch-design-md` skill) for token fidelity
- Vite + React + TypeScript scaffold (`npm create vite@latest`)

## Workflow

1. **Discover MCP prefix** — run `list_tools`, note the Stitch prefix (e.g. `stitch:`).
2. **Fetch screen** — construct `name: projects/{project}/screens/{screen}` from the string ID segments and call `[prefix]:get_screen`.
3. **Download assets** — persist HTML/screenshot under `.stitch/designs/{screen}.html` and `.png`.
4. **Read DESIGN.md** — map `colors.*`, `typography.*`, `spacing.*` to CSS variables in `src/index.css`.
5. **Generate components** — split into `src/components/`, `src/pages/`, `src/hooks/`.
6. **Wire data** — use TanStack Query for async fetches; keep presentational components pure.

## HTML → React mapping

| Pattern | Implementation |
|---------|----------------|
| Layout grid / flex | Tailwind utilities or CSS modules aligned to DESIGN.md spacing tokens |
| Cards / panels | `<section>` with tokenized border-radius and elevation fallbacks for forced-colors |
| Tables | Semantic `<table>` or TanStack Table; never div-only grids for tabular data |
| Buttons | `<button type="button">` with visible focus ring (preserve browser default unless DESIGN.md defines focus tokens) |
| Forms | `<label htmlFor>` + `<input id>`; associate errors with `aria-describedby` |
| Loading | Skeleton components; `aria-busy` on containers during fetch |
| Wallet connect | Isolate in `WalletProvider`; never embed private keys in generated code |

## DESIGN.md integration

```css
/* src/index.css — example token bridge */
:root {
  --color-primary: /* from DESIGN.md colors.primary */;
  --font-body: /* typography.body-md.fontFamily */;
}
```

Validate token names, actual color pairs and source references using the target project's existing checks and stitch-design-md's local semantic lint. No external design.md linter is bundled or assumed installed.

## Web3 dashboard conventions

- Read-only contract calls via `useReadContract` (viem/wagmi) or ethers `Contract` + TanStack Query `queryFn`.
- Format token amounts with `formatUnits`; show network name and chain ID in settings footer.
- Surface transaction errors in plain language; link to block explorer when `txHash` exists.
- Gas-sensitive flows: batch reads, avoid redundant `eth_call` in render loops.

## File structure

```
src/
├── components/     # Presentational UI from Stitch
├── pages/          # Route-level screens
├── hooks/          # useQuery wrappers, wallet hooks
├── lib/            # ABI helpers, formatters
└── styles/         # Token CSS variables
```

## Quality checklist

- [ ] WCAG 2.2 AA: measure contrast of actual component color pairs; a token document alone is insufficient
- [ ] Keyboard navigable: focus order matches visual order
- [ ] Responsive: test at 375px and 1280px widths
- [ ] No secrets in repo: RPC URLs from env (`VITE_*` prefix only for public endpoints)
- [ ] TypeScript strict: no `any` on contract ABIs

## Stitch docs note

When following links on [stitch.withgoogle.com/docs](https://stitch.withgoogle.com/docs/), use the full `https://stitch.withgoogle.com/docs/...` URL if relative navigation redirects incorrectly.
