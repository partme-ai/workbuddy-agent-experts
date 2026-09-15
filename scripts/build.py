#!/usr/bin/env python3
"""workbuddy-agents 组装器：独立智能体 → WorkBuddy 智能体团队插件 → 本地 marketplace。

用法：
    python3 scripts/build.py [teams/3d-production.yaml ...] [--out dist]

流程：
    1. 读团队定义（members/lead/skills/harness 来源）
    2. 从 agents/*.md（独立智能体，单一事实源）读取正文与 frontmatter
    3. 生成 avatars（纯色 PNG，无外部依赖）与项目 logo（缺失时自动生成）
    4. 按 harness.repo 配置 vendor 执行面（scripts/bin/config/schemas）
       并把 harness 仓库 skills/*/SKILL.md 收进 blender-production/references/
    5. 产出目录型 marketplace：<out>/<marketplace>/{.codebuddy-plugin/marketplace.json, plugins/<team>/}

安装（build 之后的动作，见 README）：
    rm -rf ~/.workbuddy/plugins/marketplaces/<marketplace>
    cp -R <out>/my-experts/.codebuddy-plugin <out>/my-experts/plugins/... ~/.workbuddy/plugins/marketplaces/my-experts/
    # WorkBuddy 启动时由 SessionPluginSwitcher 扫描 plugins/marketplaces/* 注册
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def load_yaml(path: Path):
    if yaml is None:
        raise SystemExit("PyYAML is required: python3 -m pip install pyyaml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def solid_png(path: Path, colour: str, size: int = 128) -> None:
    rgb = tuple(int(colour[i:i + 2], 16) for i in (1, 3, 5))
    raw = b"".join(b"\x00" + bytes(rgb) * size for _ in range(size))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b""))


def init_logo() -> Path:
    logo = ROOT / "assets" / "logo.png"
    if not logo.is_file():
        logo.parent.mkdir(parents=True, exist_ok=True)
        solid_png(logo, "#111827", size=256)
        print(f"logo generated: {logo}")
    return logo


def parse_agent(agent_md: Path) -> dict:
    text = agent_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise SystemExit(f"agent has no frontmatter: {agent_md}")
    meta = yaml.safe_load(match.group(1))
    return {"meta": meta, "body": text[match.end():]}


def copy_tree(src: Path, dst: Path, exclude: set[str] = {"__pycache__", ".DS_Store"}) -> int:
    count = 0
    for item in src.rglob("*"):
        if any(part in exclude for part in item.parts):
            continue
        target = dst / item.relative_to(src)
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        count += 1
    return count


# ---------------------------------------------------------------------------
# Codex 特有内容中性化：技能改名 blender-<domain>，改写主体引用；
# 白名单里保留的是"事实标识符"——线上协议串与 Blender 内真实 UI 面板名。
# ---------------------------------------------------------------------------
PROTO_STRING = "codex-blender/v1"
CODEX_ALLOWLIST = (
    PROTO_STRING,                       # 线上协议标识符（闭合契约校验，改动即断链）
    "Sidebar → Codex",                  # Blender Connector 插件的真实面板路径
    "Codex Live Session panel",         # 前台会话在 Blender 内创建的真实面板名
    "Codex panel",                      # 同上（简写形态）
    "codex-dreamina-3d",                # 兄弟插件的真实插件 id
)

_TEXT_RULES = (
    ("Codex Blender Connector", "Blender Connector"),
    ("Codex-launched", "agent-launched"),
    ("wants Codex to", "wants to"),
    ("asks Codex to", "asks to"),
    ("before Codex designs", "before the agent designs"),
    ("outside Codex", "outside the session"),
    ("design session from Codex without", "design session without"),
    ("from Codex without installing", "without installing"),
    ("Connect Codex to a Blender window", "Connect to a Blender window"),
    ("Codex Blender Router", "Blender Router"),
    ("the Codex Maya and Dreamina 3D plugins", "the Maya and Dreamina 3D sibling plugins"),
    ("codex-blender-", "blender-"),
)


def neutralize_skill_text(text: str) -> str:
    token = "\x00PROTO\x00"
    text = text.replace(PROTO_STRING, token)
    for old, new in _TEXT_RULES:
        text = text.replace(old, new)
    return text.replace(token, PROTO_STRING)


def vendor_neutral_skill(skill_dir: Path, target_root: Path) -> Path:
    """vendor 单个 harness 技能：目录与 frontmatter name 去掉 codex- 前缀，正文中性化。"""
    neutral_name = neutralize_skill_text(skill_dir.name)
    target = target_root / neutral_name
    copy_tree(skill_dir, target)
    for md in target.rglob("*.md"):
        md.write_text(neutralize_skill_text(md.read_text(encoding="utf-8")), encoding="utf-8")
    return target


def assert_no_codex_residue(plugin_dir: Path) -> None:
    """白名单之外的 codex 残留直接让构建失败，逼着未来新增内容被处理。"""
    problems = []
    for md in plugin_dir.rglob("*.md"):
        remaining = md.read_text(encoding="utf-8")
        for allowed in CODEX_ALLOWLIST:
            remaining = remaining.replace(allowed, "")
        for i, line in enumerate(remaining.splitlines(), 1):
            if "codex" in line.lower():
                problems.append(f"{md}: {line.strip()[:110]}")
    if problems:
        raise SystemExit("codex residue outside allowlist:\n" + "\n".join(problems[:12]))


def parse_skill_frontmatter(skill_md: Path) -> dict:
    """name + 单行 description（缺一即视为无效技能，构建失败）。"""
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    meta = yaml.safe_load(match.group(1)) or {}
    return meta if meta.get("name") and meta.get("description") else {}


def generate_production_routing(plugin_dir: Path) -> int:
    """blender-production/SKILL.md 的路由表从实际技能清单生成，不手写技能名。"""
    skills_dir = plugin_dir / "skills"
    rows = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name in {"blender-production", "blender-capabilities"}:
            continue
        meta = parse_skill_frontmatter(skill_dir / "SKILL.md")
        if not meta:
            raise SystemExit(f"skill without valid frontmatter: {skill_dir}")
        desc = " ".join(str(meta["description"]).split())
        rows.append((skill_dir.name, desc))
    table = "\n".join(f"| `{name}` | {desc} |" for name, desc in rows)
    content = f"""---
name: blender-production
description: Domain reference library routing into every Blender production skill (modeling, retopology, UV, rigging, animation, hair, simulation, Grease Pencil, materials, render/compositing, VSE, export, jobs, recovery, connector, Jimeng upload). Read the routing table, then only the skill matching your task.
---

# Blender 生产参考库（路由）

本技能是**按需阅读的路由**：先在下表找到你的领域，再去读对应的一等技能（`skills/` 目录内全部可用）。
**动手前不读对应技能 = 大概率返工。** 命令参数与验收阈值以各技能文档为准。

| 技能 | 覆盖 |
|---|---|
{table}

## 通用纪律（所有领域共用）

1. **闭合契约**：命令参数以技能文档的参数表为准；多余参数会被拒绝，这不是 bug。
2. **回执审计**：产物核对存在性、非零大小、SHA-256、格式；模型格式要求隔离重导入验证，媒体走探测。
3. **测量优先**：验收断言必须是测量值（计数、误差、比率、哈希），并配有能失败的对照。
4. **成熟度门槛**：交付物只能来自 L3+ 命令；L1 输出仅供探索（查 `blender-capabilities`）。
5. **revision 链**：快照 → 修改 → 导出的 `expectedSceneRevision` 链必须连贯，断链即重做。
6. **如实申报**：没验证的写"未验证"，没跑的平台写"未运行"，阈值没触发的写"未触发"。
"""
    target = skills_dir / "blender-production"
    target.mkdir(parents=True, exist_ok=True)
    (target / "SKILL.md").write_text(content, encoding="utf-8")
    return len(rows)


def generate_capability_catalog(plugin_dir: Path, harness: Path) -> dict:
    """从真实 registry 生成 blender-capabilities 技能（全命令目录 + 按领域分表）。"""
    sys.path.insert(0, str(harness))
    try:
        from scripts.harness.runtime_catalog import _registration_only_bpy
        from scripts.harness.runtime import build_registry
        registry = build_registry(_registration_only_bpy(), runtime_mode="managed")
        items, offset = [], 0
        while True:
            page = registry.list_capabilities({"offset": offset, "limit": 100})
            items += page["items"]
            if page.get("nextOffset") is None:
                break
            offset = page["nextOffset"]
    finally:
        sys.path.remove(str(harness))

    by_domain: dict[str, list] = {}
    for item in items:
        by_domain.setdefault(item.get("domain") or "general", []).append(item)

    skill_dir = plugin_dir / "skills" / "blender-capabilities"
    refs = skill_dir / "references"
    refs.mkdir(parents=True, exist_ok=True)
    for domain, entries in sorted(by_domain.items()):
        lines = [f"# {domain} 命令目录", "",
                 "| 命令 | 成熟度 | 风险 |", "|---|---|---|"]
        for entry in sorted(entries, key=lambda e: e["id"]):
            lines.append(f"| `{entry['id']}` | {entry['maturity']} | {entry['risk']} |")
        (refs / f"{domain}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    counts = {d: len(v) for d, v in sorted(by_domain.items())}
    summary = "\n".join(f"| {d} | {c} |" for d, c in counts.items())
    (skill_dir / "SKILL.md").write_text(f"""---
name: blender-capabilities
description: Full command catalog of the Blender harness generated from the live registry - every command grouped by domain with maturity (L1/L3/L4) and risk (read/standard/gated). Use this skill to check whether a command exists and whether its maturity is high enough for delivery.
---

# Blender 能力目录（构建时从真实 registry 生成）

共 {len(items)} 条命令、{len(by_domain)} 个领域。**交付物只能来自 L3+ 命令**；L1 仅可查询。
单命令详情用 `capability.describe` 查。

| 领域 | 命令数 |
|---|---|
{summary}

各领域明细：`references/<领域>.md`。
""", encoding="utf-8")
    return {"commands": len(items), "domains": len(by_domain)}


def build_team(team_path: Path, out: Path) -> dict:
    team = load_yaml(team_path)
    team_id = team["id"]
    marketplace = team["marketplace"]
    harness = (ROOT / team["harness"]["repo"]).resolve()
    if not harness.is_dir():
        raise SystemExit(f"harness repo not found: {harness}")

    members = []
    agents_meta = {}
    for entry in team["members"]:
        agent_md = ROOT / "agents" / f"{entry['id']}.md"
        if not agent_md.is_file():
            raise SystemExit(f"member agent missing: {agent_md}")
        parsed = parse_agent(agent_md)
        meta = parsed["meta"]
        agents_meta[entry["id"]] = parsed
        wb = meta.get("workbuddy", {})
        members.append({
            "entry": entry,
            "meta": meta,
            "wb": wb,
            "body": parsed["body"],
        })

    lead = team["lead"]
    if lead not in {m["entry"]["id"] for m in members}:
        raise SystemExit(f"lead {lead} is not a member")

    plugin_dir = out / marketplace / "plugins" / team_id
    if plugin_dir.exists():
        shutil.rmtree(plugin_dir)

    # agents → WorkBuddy 格式（frontmatter：name/description/displayName/profession/maxTurns）
    n_agents = 0
    for m in members:
        wb = m["wb"]
        front = (
            f"---\nname: {m['meta']['name']}\n"
            f"description: {m['meta']['description']}\n"
            f"displayName:\n  en: \"{wb['displayName']['en']}\"\n  zh: \"{wb['displayName']['zh']}\"\n"
            f"profession:\n  en: \"{wb['profession']['en']}\"\n  zh: \"{wb['profession']['zh']}\"\n"
            f"maxTurns: {wb['maxTurns']}\n---\n")
        target = plugin_dir / "agents" / f"{m['meta']['name']}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(front + m["body"], encoding="utf-8")
        n_agents += 1

    # skills：本项目自带技能 + harness 仓库全部技能一等化（不再压成 references）
    for skill_rel in team["skills"]:
        src = ROOT / skill_rel
        skill_name = Path(skill_rel).name
        copy_tree(src, plugin_dir / "skills" / skill_name)
    for vendor_rel in team["harness"]["vendor"]:
        if vendor_rel == "skills":
            for skill_dir in sorted((harness / "skills").iterdir()):
                if (skill_dir / "SKILL.md").is_file():
                    vendor_neutral_skill(skill_dir, plugin_dir / "skills")

    # 能力目录（真实 registry 生成）+ 路由表（实际技能清单生成）
    catalog = generate_capability_catalog(plugin_dir, harness)
    n_routed = generate_production_routing(plugin_dir)
    skill_paths = [f"./skills/{d.name}" for d in sorted((plugin_dir / "skills").iterdir())
                   if d.is_dir() and (d / "SKILL.md").is_file()]

    # harness 扐产物（执行面 + 许可）
    vendored = {}
    for rel in team["harness"]["vendor"]:
        if rel == "skills":
            continue
        src = harness / rel
        if src.is_dir():
            vendored[rel] = copy_tree(src, plugin_dir / rel)
    for lic in team["harness"].get("licenses", []):
        src = harness / lic
        if src.is_file():
            shutil.copy2(src, plugin_dir / lic)

    # avatars：项目 logo 作为团队头像，成员用各自 color
    avatars = plugin_dir / "avatars"
    avatars.mkdir(parents=True, exist_ok=True)
    shutil.copy2(init_logo(), avatars / "team.png")
    for m in members:
        solid_png(avatars / f"{m['meta']['name']}.png", m["meta"].get("color", "#334155"))

    # plugin.json（对照 ai-content-creator-team 的团队插件形态）
    member_ids = [m["meta"]["name"] for m in members]
    manifest = {
        "name": team_id,
        "version": team["version"],
        "description": team["display"]["description"]["en"],
        "author": {"name": "partme-ai"},
        "agents": [f"./agents/{i}.md" for i in member_ids],
        "skills": skill_paths,
        "expertType": "team",
        "agentName": lead,
        "teamInfo": {"leadAgent": lead, "memberAgents": [i for i in member_ids if i != lead]},
        "displayName": {"en": team["display"]["name"]["en"], "zh": team["display"]["name"]["zh"]},
        "profession": {"en": team["display"]["name"]["en"], "zh": team["display"]["name"]["zh"]},
        "displayDescription": {"en": team["display"]["description"]["en"],
                               "zh": team["display"]["description"]["zh"]},
        "avatar": "avatars/team.png",
        "categoryId": team["category"],
        "defaultInitPrompt": {
            "en": team["quickPrompts"][0]["en"],
            "zh": team["quickPrompts"][0]["zh"],
        },
        "quickPrompts": [{"en": q["en"], "zh": q["zh"]} for q in team["quickPrompts"]],
        "tags": [{"en": t["en"], "zh": t["zh"]} for t in team["tags"]],
        "members": [{
            "id": m["meta"]["name"],
            "name": {"en": m["entry"]["persona"]["en"], "zh": m["entry"]["persona"]["zh"]},
            "profession": {"en": m["wb"]["profession"]["en"], "zh": m["wb"]["profession"]["zh"]},
            "avatar": f"avatars/{m['meta']['name']}.png",
            "role": "lead" if m["meta"]["name"] == lead else "member",
        } for m in members],
    }
    meta_dir = plugin_dir / ".codebuddy-plugin"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "plugin.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    assert_no_codex_residue(plugin_dir)

    # marketplace 清单
    market_meta = out / marketplace / ".codebuddy-plugin"
    market_meta.mkdir(parents=True, exist_ok=True)
    (market_meta / "marketplace.json").write_text(json.dumps({
        "name": marketplace,
        "description": f"{marketplace} marketplace (built by workbuddy-agents)",
        "plugins": [{
            "name": team_id,
            "source": f"./plugins/{team_id}",
            "description": manifest["description"],
        }],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {"team": team_id, "marketplace": marketplace, "version": team["version"],
            "agents": n_agents, "firstClassSkills": len(skill_paths),
            "capabilities": catalog, "routingEntries": n_routed,
            **{f"vendor_{k}": v for k, v in vendored.items()}}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Assemble independent agents into a WorkBuddy team plugin")
    parser.add_argument("teams", nargs="*", default=None)
    parser.add_argument("--out", default=str(ROOT / "dist"))
    args = parser.parse_args(argv)
    team_paths = [Path(t) for t in args.teams] or sorted((ROOT / "teams").glob("*.yaml"))
    if not team_paths:
        raise SystemExit("no team definitions found under teams/")
    summary = [build_team(p, Path(args.out).resolve()) for p in team_paths]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
