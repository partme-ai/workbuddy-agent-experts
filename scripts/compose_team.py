#!/usr/bin/env python3
"""Generate agents/ + teams/*.yaml from team-compositions.yaml.

Reads:
  team-compositions.yaml                  — single source of truth (21 teams)
  agency-agents-zh/<domain>/<role>.md     — agent role source files
  ../workspace-agent-skills/full-{aigc,stack}-skills-repositories/<pkg>/skills/
                                            — skills alias source packages

Writes:
  agents/<role-id>.md                    — vendored agent role files
  teams/<team-id>.yaml                    — team plugin definitions

Build contract: produced teams/*.yaml must pass `python3 scripts/build.py
teams/<team-id>.yaml --out /tmp/test` (parallel to the existing manually-
curated teams).

Idempotency: re-running on the same team-compositions.yaml produces a
byte-identical set of files (modulo header comments).
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPOSITIONS = ROOT / "team-compositions.yaml"
AGENTS_SRC = Path("/Users/wandl/workspaces/workspace-tinyclaw-ai/agency-agents-zh")
SKILLS_ROOTS = [
    Path("/Users/wandl/workspaces/workspace-agent-skills/full-aigc-skills-repositories"),
    Path("/Users/wandl/workspaces/workspace-agent-skills/full-stack-skills-repositories"),
]
SKIP_PKGS = {"boss-skills", "reelbench-skills"}
AGENT_SKIP_DIRS = {".git", ".github", "assets", "examples", "integrations", "scripts"}

# ────────────────────────── skill alias resolution ──────────────────────────

_skill_index: dict[str, tuple[Path, str]] | None = None


def build_skill_index() -> dict[str, tuple[Path, str]]:
    global _skill_index
    if _skill_index is not None:
        return _skill_index
    idx: dict[str, tuple[Path, str]] = {}
    for root in SKILLS_ROOTS:
        for pkg in sorted(p for p in root.iterdir() if p.is_dir() and p.name not in SKIP_PKGS):
            if (pkg / "skills").is_dir() and (pkg / ".claude-plugin" / "plugin.json").is_file():
                # store under both package name and package-base alias (full-aigc/full-stack -> full-{org}-skills)
                idx[pkg.name] = (root, pkg.name)
                # also short alias: java-skills -> "java" alias
                if pkg.name.endswith("-skills"):
                    short = pkg.name[: -len("-skills")]
                    if short not in idx:
                        idx[short] = (root, pkg.name)
    _skill_index = idx
    return idx


def resolve_skill(alias: str) -> tuple[Path, str, list[str]] | None:
    """Return (skills_repo, package_name, skill_names) for the given alias.

    skill_names: list of every skill name under skills/ in the package
    (empty list = all skills, since the lockfile-vendor model vendors the
    whole directory wholesale). For per-skill precision, callers can
    post-filter against the package's plugin.json skills[].
    """
    idx = build_skill_index()
    entry = idx.get(alias)
    if not entry:
        return None
    root, pkg_name = entry
    skills_dir = root / pkg_name / "skills"
    skill_names = sorted(d.name for d in skills_dir.iterdir() if d.is_dir())
    return (root, pkg_name, skill_names)


# ────────────────────────── agent vendoring ──────────────────────────

def collect_agent_ids() -> set[str]:
    found: set[str] = set()
    for d in AGENTS_SRC.iterdir():
        if d.is_dir() and d.name not in AGENT_SKIP_DIRS:
            for f in d.glob("*.md"):
                found.add(f.stem)
    return found


def vendor_agent(agent_id: str, out_dir: Path) -> Path:
    """Copy the upstream agent .md into agents/, strip codex-/codexX- prefix
    in frontmatter name field so it's neutral (build.py vendor_neutral_skill
    only handles skills/<id>/, not agents/, so we sanitize here).
    """
    # find source file
    sources = list(AGENTS_SRC.rglob(f"{agent_id}.md"))
    sources = [s for s in sources if ".git" not in s.parts]
    if not sources:
        raise FileNotFoundError(f"agent not found: {agent_id}")
    src = sources[0]
    target = out_dir / f"{agent_id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8", errors="replace")
    # strip known host prefixes from the frontmatter name field
    text = re.sub(r"^name:\s*codex[a-z-]*-(.+)$", r"name: \1", text, count=1, flags=re.M)
    target.write_text(text, encoding="utf-8")
    return target


# ────────────────────────── team yaml rendering ──────────────────────────

def render_team_yaml(team: dict) -> str:
    """Render a single team yaml compatible with scripts/build.py.

    Shape (matches the existing hand-curated teams):
      id, version, marketplace, category, allowCodexReferences,
      display { name {zh,en}, description {zh,en} },
      lead: <id>-lead,
      members: [list of {id: <role>}],
      sources: [list of {repo, vendor, licensePrefix?}],
      quickPrompts: [2-3 sample prompts]
    """
    tid = team["id"]
    members = team.get("members", [])

    # resolve skills → source repos with licensePrefix
    sources: list[dict] = []
    seen_pkgs: set[tuple[str, str]] = set()  # (root_str, pkg_name)
    for skill_alias in team.get("skills", []):
        res = resolve_skill(skill_alias)
        if not res:
            print(f"  WARN: {tid}: skill alias {skill_alias!r} not found, skipping",
                  file=sys.stderr)
            continue
        root, pkg_name, _ = res
        root_str = str(root)
        # rel path from workbuddy-agent-experts/ to the package
        if "full-aigc-skills-repositories" in root_str:
            rel_repo = "../../workspace-agent-skills/full-aigc-skills-repositories/" + pkg_name
        else:
            rel_repo = "../../workspace-agent-skills/full-stack-skills-repositories/" + pkg_name
        if (root_str, pkg_name) in seen_pkgs:
            continue
        seen_pkgs.add((root_str, pkg_name))
        sources.append({
            "repo": rel_repo,
            "vendor": ["skills"],
            "licensePrefix": f"{pkg_name}-",
        })

    # lead = the team's `lead` (or first member if missing)
    lead = f"{tid}-lead"
    members_yaml = "\n".join(f"  - {m}" for m in members)

    sources_yaml_lines = ["sources:"]
    for s in sources:
        sources_yaml_lines.append(f"  - repo: {s['repo']}")
        sources_yaml_lines.append(f'    vendor: {s["vendor"]}')
        if s.get("licensePrefix"):
            sources_yaml_lines.append(f"    licensePrefix: {s['licensePrefix']}")
    sources_yaml = "\n".join(sources_yaml_lines)

    return f"""# AUTO-GENERATED by scripts/compose_team.py from team-compositions.yaml
# Do not edit by hand; re-run the script to refresh.

id: {tid}
version: 1.0.0
marketplace: my-experts
allowCodexReferences: true   # cross-references to upstream plugins (skills aliases) are factual
category: {team.get('category', '02-Engineering')}

display:
  name: {{zh: "{team['display']['name']['zh']}", en: "{team['display']['name']['en']}"}}
  description:
    zh: "{team['display']['name']['zh']}：多智能体协作团队，由 scripts/compose_team.py 自动组装。"
    en: "{team['display']['name']['en']}: a multi-agent team auto-assembled by scripts/compose_team.py from team-compositions.yaml."

lead: {lead}
members:
{members_yaml}

# ── 技能来源：vendor from skills organizations (resolved by compose_team.py) ──
{sources_yaml}

quickPrompts:
  - {{zh: "用 {tid} 的标准流程启动这个项目", en: "Bootstrap a new project in {tid}"}}
  - {{zh: "对这个代码库做一次健康检查", en: "Run a health check on this codebase"}}
  - {{zh: "升级到最新的 skills 快照", en: "Refresh to the latest vendored skills snapshot"}}
"""


# ────────────────────────── entry point ──────────────────────────

def main() -> int:
    data = yaml.safe_load(COMPOSITIONS.read_text())
    teams = data.get("compositions", [])

    available_agents = collect_agent_ids()
    missing_agents: list[tuple[str, str]] = []
    for t in teams:
        for m in t.get("members", []):
            if m not in available_agents:
                missing_agents.append((t["id"], m))
    if missing_agents:
        print("ERROR: missing agents in agency-agents-zh:", file=sys.stderr)
        for tid, m in missing_agents[:30]:
            print(f"  {tid}: {m!r}", file=sys.stderr)
        return 1

    # vendor agents (deduped across teams)
    all_agents_needed: set[str] = set()
    for t in teams:
        all_agents_needed.update(t.get("members", []))
    for aid in sorted(all_agents_needed):
        vendor_agent(aid, ROOT / "agents")
    print(f"vendored {len(all_agents_needed)} agent roles into agents/")

    # render teams
    for t in teams:
        out = ROOT / "teams" / f"{t['id']}.yaml"
        out.write_text(render_team_yaml(t), encoding="utf-8")
    print(f"rendered {len(teams)} team yamls into teams/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
