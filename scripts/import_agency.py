#!/usr/bin/env python3
"""把 agency-agents-zh 的全部智能体定义导入为独立智能体（我们的格式）。

源格式（agency-agents-zh）          → 目标格式（本项目 agents/<category>/<id>.md）
  name:     中文名                  → title（中文名）
  文件名 stem                        → name（英文 id，插件系统需要）
  description（可能多行）            → 单行 description
  color:    色名（cyan/purple/...）  → 原样保留（build 时映射为 hex 生成头像）
  emoji                             → 原样保留
  （无）                            → category + workbuddy 适配块（含 WorkBuddy categoryId 映射）

正文原样保留。已存在的目标文件不覆盖（--force 可覆盖）。

用法：
    python3 scripts/import_agency.py [--source <agency-agents-zh 路径>] [--force]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path("/Users/wandl/workspaces/workspace-tinyclaw-ai/agency-agents-zh")

# agency 类目 → WorkBuddy 专家市场 categoryId（形态对照 experts 市场实测值）
CATEGORY_ID_MAP = {
    "engineering": "02-Engineering", "testing": "02-Engineering", "security": "02-Engineering",
    "integrations": "02-Engineering",
    "design": "01-ProductDesign", "gis": "01-ProductDesign", "spatial-computing": "01-ProductDesign",
    "game-development": "01-ProductDesign",
    "marketing": "07-SalesCommerce", "paid-media": "07-SalesCommerce", "sales": "07-SalesCommerce",
    "support": "07-SalesCommerce",
    "finance": "12-IndustryConsultant", "legal": "12-IndustryConsultant", "hr": "12-IndustryConsultant",
    "academic": "12-IndustryConsultant", "specialized": "12-IndustryConsultant",
    "supply-chain": "12-IndustryConsultant", "strategy": "12-IndustryConsultant",
    "product": "01-ProductDesign", "project-management": "02-Engineering",
}

AGENT_FILE = re.compile(r"^[a-z0-9][a-z0-9-]*\.md$")


def single_line(text: str) -> str:
    return " ".join(str(text).split())


def convert(source_md: Path, category: str) -> tuple[str, str] | None:
    """返回 (英文 id, 目标 markdown)；非智能体文件（文档/README）返回 None。"""
    if not AGENT_FILE.match(source_md.name):
        return None
    text = source_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None
    meta = yaml.safe_load(match.group(1)) or {}
    if not (meta.get("name") and meta.get("description")):
        return None
    agent_id = source_md.stem
    zh_name = single_line(meta["name"])
    description = single_line(meta["description"])
    color = meta.get("color") or "slate"
    emoji = meta.get("emoji") or "🤖"
    workbuddy = {
        "displayName": {"en": agent_id, "zh": zh_name},
        "profession": {"en": agent_id, "zh": zh_name},
        "maxTurns": 120,
        "categoryId": CATEGORY_ID_MAP.get(category, "12-IndustryConsultant"),
    }
    front = {
        "name": agent_id, "title": zh_name, "description": description,
        "color": color, "emoji": emoji, "category": category,
        "workbuddy": workbuddy,
    }
    fm = yaml.safe_dump(front, allow_unicode=True, sort_keys=False, default_flow_style=False).strip()
    return agent_id, f"---\n{fm}\n---\n{text[match.end():]}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Import agency-agents-zh agents")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    source = Path(args.source).resolve()
    if not source.is_dir():
        raise SystemExit(f"source not found: {source}")

    stats, skipped = {}, []
    for category_dir in sorted(p for p in source.iterdir() if p.is_dir()
                               and not p.name.startswith(".")):
        for source_md in sorted(category_dir.glob("*.md")):
            converted = convert(source_md, category_dir.name)
            if converted is None:
                skipped.append(source_md.relative_to(source).as_posix())
                continue
            agent_id, markdown = converted
            target = ROOT / "agents" / category_dir.name / f"{agent_id}.md"
            if target.exists() and not args.force:
                skipped.append(f"{target.relative_to(ROOT)} (exists)")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(markdown, encoding="utf-8")
            stats[category_dir.name] = stats.get(category_dir.name, 0) + 1

    total = sum(stats.values())
    print(f"imported {total} agents across {len(stats)} categories:")
    for category, count in sorted(stats.items()):
        print(f"  {category:<20} {count}")
    if skipped:
        print(f"skipped {len(skipped)} files (docs/invalid/exists):")
        for item in skipped[:8]:
            print(f"  - {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
