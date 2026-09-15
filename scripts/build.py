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
    cp -R <out>/<marketplace> ~/.workbuddy/plugins/marketplaces/
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

    # skills（本项目自带）+ harness 仓库的技能作为 references
    n_refs = 0
    skill_paths = []
    for skill_rel in team["skills"]:
        src = ROOT / skill_rel
        skill_name = Path(skill_rel).name
        dst = plugin_dir / "skills" / skill_name
        copy_tree(src, dst)
        skill_paths.append(f"./skills/{skill_name}")
    for vendor_rel in team["harness"]["vendor"]:
        if vendor_rel == "skills":
            refs = plugin_dir / "skills" / "blender-production" / "references"
            refs.mkdir(parents=True, exist_ok=True)
            for skill_dir in sorted((harness / "skills").iterdir()):
                skill_md = skill_dir / "SKILL.md"
                if skill_md.is_file():
                    shutil.copy2(skill_md, refs / f"{skill_dir.name}.md")
                    n_refs += 1

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
            "agents": n_agents, "references": n_refs,
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
