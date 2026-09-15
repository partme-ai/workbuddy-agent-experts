#!/usr/bin/env python3
"""workbuddy-agent-experts 组装器：独立智能体 → WorkBuddy 智能体团队插件 → 本地 marketplace。

用法：
    python3 scripts/build.py [teams/*.yaml ...] [--out experts]

流程：
    1. 读团队定义（members/lead/skills/harness 来源）
    2. 从 agents/*.md（独立智能体，单一事实源）读取正文与 frontmatter
    3. 生成 avatars（纯色 PNG，无外部依赖）与项目 logo（缺失时自动生成）
    4. 按 harness.repo 配置 vendor 执行面（scripts/bin/config/schemas）
       并把 harness 仓库 skills/*/SKILL.md 收进 blender-production/references/
    5. 产出目录型 marketplace：<out>/{.codebuddy-plugin/marketplace.json, plugins/<team>/}（默认 experts/）

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


COLOR_NAME_HEX = {
    "red": "#B91C1C", "blue": "#1D4ED8", "green": "#047857", "yellow": "#A16207",
    "orange": "#C2410C", "purple": "#6D28D9", "pink": "#BE185D", "cyan": "#0E7490",
    "teal": "#0F766E", "lime": "#4D7C0F", "amber": "#B45309", "indigo": "#4338CA",
    "violet": "#7C3AED", "magenta": "#A21CAF", "crimson": "#9F1239", "brown": "#78350F",
    "gray": "#4B5563", "grey": "#4B5563", "slate": "#334155", "black": "#111827",
    "white": "#E5E7EB", "navy": "#1E3A5F", "olive": "#585D34", "sky": "#0369A1",
    "emerald": "#065F46", "rose": "#9F1239", "fuchsia": "#A21CAF", "salmon": "#C2410C",
    "turquoise": "#0E7490", "aqua": "#0E7490",
}


def resolve_color(colour) -> str:
    """色名/hex/缺省 → 生成头像用的 hex。"""
    colour = str(colour or "").strip().lower()
    if colour.startswith("#") and len(colour) == 7:
        return colour
    return COLOR_NAME_HEX.get(colour, "#334155")


_AGENT_INDEX: dict[str, Path] | None = None


def agent_index() -> dict[str, Path]:
    """构建/返回 agents/ 全树索引；同名 id 视为定义冲突，直接失败。"""
    global _AGENT_INDEX
    if _AGENT_INDEX is None:
        index: dict[str, Path] = {}
        collisions = []
        for path in sorted((ROOT / "agents").rglob("*.md")):
            if path.stem in index:
                collisions.append(f"{index[path.stem]} <-> {path}")
            index[path.stem] = path
        if collisions:
            raise SystemExit("duplicate agent ids:\n" + "\n".join(collisions[:8]))
        _AGENT_INDEX = index
    return _AGENT_INDEX


def find_agent(agent_id: str) -> Path:
    """在 agents/ 全树（含类目子目录）里找 <id>.md。"""
    path = agent_index().get(agent_id)
    if path is None:
        raise SystemExit(f"agent not found: {agent_id}")
    return path


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
    ("Codex Image Factory", "Image Factory"),
    ("codex-image-factory-", "image-factory-"),
    ("codex-video-factory-", "video-factory-"),
    ("codex-processon-", "processon-"),
    ("codex-dreamina-3d-", "dreamina-3d-"),
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


def assert_no_codex_residue(plugin_dir: Path, *, allow_factual: bool = False) -> None:
    """白名单之外的 codex 残留直接让构建失败，逼着未来新增内容被处理。

    allow_factual：团队声明其执行面**事实上依赖本地 Codex CLI**（如 image-factory 经
    Codex 账户出图）时，放行裸 Codex 互操作引用——这是事实声明，不是品牌残留；
    前缀/主体改写规则仍然生效。
    """
    if allow_factual:
        return
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


def team_sources(team: dict) -> list[dict]:
    """统一多源：sources: [{repo, vendor[], licenses[], docsTo}] ；harness 为单源旧形态。"""
    if team.get("sources"):
        return list(team["sources"])
    if team.get("harness"):
        return [team["harness"]]
    return []


def build_team(team_path: Path, out: Path) -> dict:
    team = load_yaml(team_path)
    team_id = team["id"]
    marketplace = team["marketplace"]
    sources = team_sources(team)
    for source in sources:
        repo = (ROOT / source["repo"]).resolve()
        source["_repo_path"] = repo
        if not repo.is_dir():
            raise SystemExit(f"source repo not found: {source['repo']} -> {repo}")

    members = []
    for entry in team["members"]:
        agent_md = find_agent(entry["id"])
        parsed = parse_agent(agent_md)
        meta = parsed["meta"]
        wb = meta.get("workbuddy", {})
        members.append({"entry": entry, "meta": meta, "wb": wb, "body": parsed["body"]})

    lead = team["lead"]
    if lead not in {m["entry"]["id"] for m in members}:
        raise SystemExit(f"lead {lead} is not a member")

    plugin_dir = out / "plugins" / team_id
    if plugin_dir.exists():
        shutil.rmtree(plugin_dir)

    # agents → WorkBuddy 格式（frontmatter：name/description/displayName/profession/maxTurns）
    for m in members:
        wb = m["wb"]
        front = (
            f"---\nname: {m['meta']['name']}\n"
            f"description: {json.dumps(m['meta']['description'], ensure_ascii=False)}\n"
            f"displayName:\n  en: {json.dumps(wb['displayName']['en'], ensure_ascii=False)}\n"
            f"  zh: {json.dumps(wb['displayName']['zh'], ensure_ascii=False)}\n"
            f"profession:\n  en: {json.dumps(wb['profession']['en'], ensure_ascii=False)}\n"
            f"  zh: {json.dumps(wb['profession']['zh'], ensure_ascii=False)}\n"
            f"maxTurns: {wb.get('maxTurns', 120)}\n---\n")
        target = plugin_dir / "agents" / f"{m['meta']['name']}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(front + m["body"], encoding="utf-8")

    # 本项目自带技能（调用规范等）
    skill_paths: list[str] = []
    for skill_rel in team.get("skills", []):
        src = ROOT / skill_rel
        copy_tree(src, plugin_dir / "skills" / Path(skill_rel).name)

    # 多源 vendor：skills 一等化（中性化）、其余目录/文档照搬、许可随行
    vendored: dict[str, int] = {}
    for source in sources:
        repo = source["_repo_path"]
        for rel in source.get("vendor", []):
            src = repo / rel
            if rel == "skills" and src.is_dir():
                for skill_dir in sorted(src.iterdir()):
                    if (skill_dir / "SKILL.md").is_file():
                        vendor_neutral_skill(skill_dir, plugin_dir / "skills")
            elif src.is_dir():
                dest = rel if not source.get("docsTo") else Path(source["docsTo"]) / rel
                vendored[f"{source['repo']}::{rel}"] = copy_tree(src, plugin_dir / dest)
        for lic in source.get("licenses", []):
            lic_file = repo / lic
            if lic_file.is_file():
                shutil.copy2(lic_file, plugin_dir / f"{source.get('licensePrefix', '')}{lic}")

    # 能力目录 + 路由：仅显式声明的团队生成（blender）
    catalog, n_routed = {}, 0
    if team.get("capabilities"):
        main_repo = sources[0]["_repo_path"]
        catalog = generate_capability_catalog(plugin_dir, main_repo)
        n_routed = generate_production_routing(plugin_dir)
    skill_paths = ([f"./skills/{d.name}" for d in sorted((plugin_dir / "skills").iterdir())
                    if d.is_dir() and (d / "SKILL.md").is_file()]
                   if (plugin_dir / "skills").is_dir() else [])

    # avatars：项目 logo 作为团队头像，成员用各自 color（色名映射为 hex）
    avatars = plugin_dir / "avatars"
    avatars.mkdir(parents=True, exist_ok=True)
    shutil.copy2(init_logo(), avatars / "team.png")
    for m in members:
        solid_png(avatars / f"{m['meta']['name']}.png", resolve_color(m["meta"].get("color")))

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
            "name": {"en": m["entry"].get("persona", {}).get("en", m["meta"]["name"]),
                     "zh": m["entry"].get("persona", {}).get("zh", m["meta"].get("title", m["meta"]["name"]))},
            "profession": {"en": m["wb"]["profession"]["en"], "zh": m["wb"]["profession"]["zh"]},
            "avatar": f"avatars/{m['meta']['name']}.png",
            "role": "lead" if m["meta"]["name"] == lead else "member",
        } for m in members],
    }
    meta_dir = plugin_dir / ".codebuddy-plugin"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "plugin.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    assert_no_codex_residue(plugin_dir, allow_factual=bool(team.get("allowCodexReferences")))
    return {"plugin": team_id, "kind": "team", "marketplace": marketplace,
            "version": team["version"], "agents": len(members),
            "firstClassSkills": len(skill_paths),
            "capabilities": catalog, "routingEntries": n_routed,
            "description": manifest["description"]}


def build_single(agent_id: str, out: Path, marketplace: str, version: str, *, single_allow: bool = False) -> dict:
    """独立智能体 → 单专家插件（expertType: agent，形态对照 experts 市场的 ui-designer）。"""
    parsed = parse_agent(find_agent(agent_id))
    meta, body = parsed["meta"], parsed["body"]
    wb = meta.get("workbuddy", {})
    plugin_dir = out / "plugins" / agent_id
    if plugin_dir.exists():
        shutil.rmtree(plugin_dir)

    front = (
        f"---\nname: {meta['name']}\n"
        f"description: {json.dumps(meta['description'], ensure_ascii=False)}\n"
        f"displayName:\n  en: {json.dumps(wb['displayName']['en'], ensure_ascii=False)}\n"
        f"  zh: {json.dumps(wb['displayName']['zh'], ensure_ascii=False)}\n"
        f"profession:\n  en: {json.dumps(wb['profession']['en'], ensure_ascii=False)}\n"
        f"  zh: {json.dumps(wb['profession']['zh'], ensure_ascii=False)}\n"
        f"maxTurns: {wb.get('maxTurns', 120)}\n---\n")
    (plugin_dir / "agents").mkdir(parents=True)
    (plugin_dir / "agents" / f"{agent_id}.md").write_text(front + body, encoding="utf-8")

    avatars = plugin_dir / "avatars"
    avatars.mkdir()
    solid_png(avatars / "expert.png", resolve_color(meta.get("color")))

    manifest = {
        "name": agent_id,
        "version": version,
        "description": meta["description"],
        "expertType": "agent",
        "agentName": agent_id,
        "agents": [f"./agents/{agent_id}.md"],
        "displayName": {"en": wb["displayName"]["en"], "zh": wb["displayName"]["zh"]},
        "profession": {"en": wb["profession"]["en"], "zh": wb["profession"]["zh"]},
        "displayDescription": {"en": meta["description"], "zh": meta["description"]},
        "avatar": "avatars/expert.png",
        "categoryId": wb.get("categoryId", "12-IndustryConsultant"),
        "defaultInitPrompt": {"zh": f"我是{wb['displayName']['zh']}，请介绍你的专业能力并开始协助我。",
                              "en": f"I am {wb['displayName']['en']}. Introduce your expertise and help me."},
        "tags": [{"en": meta.get("category", "agent"), "zh": meta.get("category", "agent")}],
    }
    meta_dir = plugin_dir / ".codebuddy-plugin"
    meta_dir.mkdir()
    (meta_dir / "plugin.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert_no_codex_residue(plugin_dir, allow_factual=bool(single_allow))
    return {"plugin": agent_id, "kind": "single", "marketplace": marketplace,
            "version": version, "description": meta["description"]}


def write_marketplace_manifest(out: Path, marketplace: str, plugins: list[dict]) -> None:
    """marketplace 名只进清单字段；目录树直接是 out 根（experts/）。"""
    """聚合清单：所有已构建插件一次写入（修掉逐团队覆盖的旧 bug）。"""
    market_meta = out / ".codebuddy-plugin"
    market_meta.mkdir(parents=True, exist_ok=True)
    (market_meta / "marketplace.json").write_text(json.dumps({
        "name": marketplace,
        "description": f"{marketplace} marketplace (built by workbuddy-agent-experts)",
        "plugins": [{"name": p["plugin"], "source": f"./plugins/{p['plugin']}",
                     "description": p["description"]} for p in plugins],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def install_my_experts(dist_market: Path) -> Path:
    """部署到 WorkBuddy 官方自定义专家通道（非破坏式：只替换本构建管理的插件）。

    my-experts 是应用与本项目共用的通道：应用 UI 创建的专家也会落在
    plugins/my-experts/plugins/ 下，并由 scanCustomExperts 自动对账清单。
    因此安装时只删除/覆盖本次构建产出的插件目录，保留其它目录与清单条目。
    """
    import time
    home = Path.home()
    market = home / ".workbuddy" / "plugins" / "marketplaces" / "my-experts"
    ours = {e["name"] for e in json.loads(
        (dist_market / ".codebuddy-plugin/marketplace.json").read_text())["plugins"]}
    market_plugins = market / "plugins"
    if market_plugins.is_dir():
        for existing in market_plugins.iterdir():
            if existing.name in ours:
                shutil.rmtree(existing)
    if market_plugins.is_dir():
        for our in sorted(ours):
            src = dist_market / "plugins" / our
            if src.is_dir():
                shutil.copytree(src, market_plugins / our)
    else:
        shutil.copytree(dist_market / "plugins", market_plugins, dirs_exist_oks=False)             if False else (market_plugins.mkdir(parents=True, exist_ok=True),
                           [shutil.copytree(dist_market / "plugins" / o, market_plugins / o)
                            for o in sorted(ours)])
    # 清单：保留外部条目，合并本构建条目
    manifest_path = market / ".codebuddy-plugin/marketplace.json"
    foreign = []
    if manifest_path.is_file():
        try:
            existing = json.loads(manifest_path.read_text())
            foreign = [e for e in existing.get("plugins", []) if e.get("name") not in ours]
        except Exception:
            foreign = []
    ours_entries = json.loads(
        (dist_market / ".codebuddy-plugin/marketplace.json").read_text())["plugins"]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({
        "name": "my-experts",
        "description": "my-experts marketplace (built by workbuddy-agent-experts)",
        "plugins": foreign + ours_entries,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    now = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
    ip_path = home / ".workbuddy" / "plugins" / "installed_plugins.json"
    ip = json.loads(ip_path.read_text())
    manifest = json.loads((dist_market / ".codebuddy-plugin/marketplace.json").read_text())
    cache_root = home / ".workbuddy" / "plugins" / "cache" / "my-experts"
    for entry in manifest["plugins"]:
        name, version = entry["name"], "1.0.0"
        pj = dist_market / "plugins" / name / ".codebuddy-plugin" / "plugin.json"
        if pj.is_file():
            version = json.loads(pj.read_text()).get("version", "1.0.0")
        cache = cache_root / name / version
        if cache.exists():
            shutil.rmtree(cache)
        cache.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(dist_market / "plugins" / name, cache)
        ip["plugins"][f"{name}@my-experts"] = [{
            "scope": "user", "installPath": str(cache), "version": version,
            "installedAt": now, "lastUpdated": now,
        }]
    ip_path.write_text(json.dumps(ip, ensure_ascii=False, indent=2) + "\n")
    km_path = home / ".workbuddy" / "plugins" / "known_marketplaces.json"
    km = json.loads(km_path.read_text())
    if "my-experts" in km:
        km["my-experts"]["lastUpdated"] = now
        km_path.write_text(json.dumps(km, ensure_ascii=False, indent=2) + "\n")
    return market


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Assemble agents into WorkBuddy team/single-expert plugins")
    parser.add_argument("teams", nargs="*", default=None)
    parser.add_argument("--out", default=str(ROOT / "experts"))
    parser.add_argument("--install", action="store_true",
                        help="deploy experts/ into ~/.workbuddy/plugins/marketplaces/my-experts (official channel)")
    args = parser.parse_args(argv)
    out = Path(args.out).resolve()
    team_paths = [Path(t) for t in args.teams] or sorted((ROOT / "teams").glob("*.yaml"))
    if not team_paths:
        raise SystemExit("no team definitions found under teams/")

    results = [build_team(p, out) for p in team_paths]

    singles_path = ROOT / "singles.yaml"
    if singles_path.is_file():
        singles = load_yaml(singles_path)
        selector = singles.get("singles", [])
        ids = sorted(agent_index()) if selector == "*" else list(selector)
        version = singles.get("version", "1.0.0")
        team_plugin_ids = {r["plugin"] for r in results}
        for agent_id in ids:
            if agent_id in team_plugin_ids:
                continue
            results.append(build_single(agent_id, out, "my-experts", version))

    marketplaces = sorted({r["marketplace"] for r in results})
    for marketplace in marketplaces:
        write_marketplace_manifest(out, marketplace,
                                   [r for r in results if r["marketplace"] == marketplace])

    installed = None
    if args.install:
        installed = str(install_my_experts(out))
    print(json.dumps({"plugins": len(results), "installed": installed, "detail": results},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
