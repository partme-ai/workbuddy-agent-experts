#!/usr/bin/env python3
"""Generate agents/ + teams/*.yaml from team-compositions.yaml.

Reads:
  team-compositions.yaml                  — single source of truth (21 teams)
  agency-agents-zh/<domain>/<role>.md     — agent role source files
  ../workspace-agent-skills/full-{aigc,stack}-skills-repositories/<pkg>/skills/
                                            — skills alias source packages

Writes:
  agents/<domain>/<role-id>.md            — vendored agent role files
  teams/<team-id>.yaml                    — team plugin definitions

Build contract: produced teams/*.yaml must pass `python3 scripts/build.py
teams/<team-id>.yaml --out /tmp/test` (parallel to the existing manually-
curated teams).

Idempotency: re-running on the same team-compositions.yaml produces a
byte-identical set of files (modulo header comments).

CLI:
  --dry-run              write to /tmp/composed-teams/{agents,teams}
                          instead of agents/ and teams/, and print a diff
                          summary against the current tracked files
  --output-dir=PATH      override the output directory (default: repo root)
"""
from __future__ import annotations

import json
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

# Per-domain color used for solid-PNG avatars (must match build.py's palette).
DOMAIN_COLORS = {
    "engineering": "blue",
    "design": "purple",
    "testing": "green",
    "marketing": "pink",
    "sales": "orange",
    "finance": "yellow",
    "data-remediation": "teal",
    "support": "gray",
    "product": "indigo",
    "security": "red",
    "misc": "gray",
}

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


def _domain_for_agent(agent_id: str) -> str:
    """Find which agency-agents-zh domain directory the agent lives in.

    Used to mirror the hand-curated agents/ layout (e.g. agents/design/,
    agents/engineering/, agents/testing/), which build.py's agent_index
    rglob handles transitively — agents are deduped across teams by stem.
    """
    for d in AGENTS_SRC.iterdir():
        if d.is_dir() and d.name not in AGENT_SKIP_DIRS:
            if (d / f"{agent_id}.md").is_file():
                return d.name
    return "misc"  # synthetic lead agents that don't have an upstream file


def _extract_zh_displayname(text: str) -> tuple[str, str]:
    """Read the original (zh) name and description from upstream frontmatter
    for use in build.py's workbuddy.displayName.{zh} / profession.{zh}.

    Returns (name_zh, desc_zh); empty strings if not parseable.
    """
    name = ""
    desc = ""
    for line in text.splitlines():
        if line.startswith("name:") and not name:
            name = line.split(":", 1)[1].strip()
        elif line.startswith("description:") and not desc:
            desc = line.split(":", 1)[1].strip()
    return name, desc


def vendor_agent(agent_id: str, out_root: Path) -> Path:
    """Copy the upstream agent .md into out_root/agents/<domain>/<id>.md,
    sanitize the frontmatter, and inject the workbuddy: block that
    build.py expects (displayName.{en,zh}, profession.{en,zh}, maxTurns).
    If the source file does not exist (e.g. <team-id>-lead), synthesize
    a minimal stub under misc/.
    """
    sources = list(AGENTS_SRC.rglob(f"{agent_id}.md"))
    sources = [s for s in sources if ".git" not in s.parts]
    domain = _domain_for_agent(agent_id) if sources else "misc"
    target = out_root / "agents" / domain / f"{agent_id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    if sources:
        src = sources[0]
        text = src.read_text(encoding="utf-8", errors="replace")
        # FORCE the frontmatter `name:` to the English agent_id — build.py
        # uses meta['name'] as the avatar filename, and the upstream Chinese
        # name ("后端架构师") would break avatar PNG writes on Chinese
        # subdir names. We preserve the upstream Chinese name via
        # workbuddy.displayName.zh below.
        text = re.sub(r"^name:\s.*$", f"name: {agent_id}", text, count=1, flags=re.M)
        # ensure emoji + color fields (build.py reads meta.get('color') and
        # meta.get('emoji'); missing color crashes the avatar PNG generator).
        if not re.search(r"^emoji:\s", text, re.M):
            text = re.sub(r"^---\n", f"---\nemoji: 🧩\n", text, count=1)
        if not re.search(r"^color:\s", text, re.M):
            color = DOMAIN_COLORS.get(domain, "gray")
            text = re.sub(r"^emoji:\s.*\n", f"\\g<0>color: {color}\n", text, count=1)
        zh_name, zh_desc = _extract_zh_displayname(text)
        en_name = agent_id.replace("-", " ").title()
        en_desc = (zh_desc or "Role-specific agent") + " (auto-vendored by compose_team.py)"
    else:
        zh_name = agent_id
        zh_desc = f"Team lead agent for the auto-generated {agent_id.rsplit('-lead', 1)[0]} team. Routes work to members and verifies outputs."
        en_name = agent_id.replace("-", " ").title()
        en_desc = zh_desc
        # minimal frontmatter for stub agents (no upstream source)
        text = (
            f"---\nname: {agent_id}\n"
            f"description: {zh_desc}\n"
            f"emoji: 🧩\ncolor: gray\n"
            f"---\n\n# {agent_id}\n\n## Role\n\n"
            f"This is the lead agent for the `{agent_id.rsplit('-lead', 1)[0]}` "
            "team. It routes work to the other members based on task type and "
            "verifies outputs against the team's quality gates.\n\n"
            "## Behavior\n\n"
            "- Always identify the task type before delegating\n"
            "- Use the member agent that best matches the task's primary domain\n"
            "- Verify deliverables before declaring done\n\n"
            "## Constraints\n\n"
            "- Does not perform direct code generation; delegates to specialist members\n"
            "- Escalates blockers to the user, never silently retries\n"
        )

    # inject/overwrite workbuddy: block at end of frontmatter (or create
    # frontmatter if missing). The block is required by build.py.
    wb_block = (
        "\nworkbuddy:\n"
        f"  displayName:\n"
        f"    en: {json.dumps(en_name, ensure_ascii=False)}\n"
        f"    zh: {json.dumps(zh_name, ensure_ascii=False)}\n"
        f"  profession:\n"
        f"    en: {json.dumps(en_desc, ensure_ascii=False)}\n"
        f"    zh: {json.dumps(zh_desc, ensure_ascii=False)}\n"
        f"  maxTurns: 120\n"
    )
    # remove any existing workbuddy: block
    text = re.sub(r"\nworkbuddy:\n(?:  .*\n)+", "", text)
    # insert before the closing ---
    text = re.sub(r"\n---\n", wb_block + "\n---\n", text, count=1)
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

    # resolve skills → source repos. Emit GitHub HTTPS URLs as the
    # repo field so the generated team is portable across machines —
    # build.py shallow-clones the URL on demand (see scripts/build.py
    # `_is_git_url`). Override to a local relative path via the
    # `WORKBUDDY_VENDOR_MODE=local` environment variable if you want to
    # bypass the clone (offline work, etc).
    sources: list[dict] = []
    seen_pkgs: set[tuple[str, str]] = set()
    import os
    vendor_mode = os.environ.get("WORKBUDDY_VENDOR_MODE", "git").lower()
    for skill_alias in team.get("skills", []):
        res = resolve_skill(skill_alias)
        if not res:
            print(f"  WARN: {tid}: skill alias {skill_alias!r} not found, skipping",
                  file=sys.stderr)
            continue
        root, pkg_name, _ = res
        # GitHub org lookup by root name
        if "full-aigc-skills-repositories" in str(root):
            org = "full-aigc-skills"
        else:
            org = "full-stack-skills"
        pkg_url = f"https://github.com/{org}/{pkg_name}.git"
        if (pkg_url, pkg_name) in seen_pkgs:
            continue
        seen_pkgs.add((pkg_url, pkg_name))
        if vendor_mode == "local":
            # fall back to the local checkout path (offline / dev mode)
            if "full-aigc-skills-repositories" in str(root):
                rel_repo = "../../workspace-agent-skills/full-aigc-skills-repositories/" + pkg_name
            else:
                rel_repo = "../../workspace-agent-skills/full-stack-skills-repositories/" + pkg_name
        else:
            rel_repo = pkg_url
        entry: dict = {
            "repo": rel_repo,
            "vendor": ["skills"],
            "licensePrefix": f"{pkg_name}-",
        }
        # include the ref so build.py's future clone step can pin a tag
        sources.append(entry)

    # lead = the team's `lead` (or first member if missing)
    lead = f"{tid}-lead"
    # lead must appear in members for build.py; use members[0] if no
    # explicit <team-id>-lead. The stub for <team-id>-lead is vendored
    # into agents/<domain>/ so build.py's agent_index can resolve it.
    lead_id = f"{tid}-lead"
    if lead_id not in members:
        members = [lead_id] + members

    members_yaml = "\n".join(f"  - id: {m}" for m in members)

    # The lead line intentionally references an explicit agent id
    # (e.g. java-backend-team-lead) so build.py validates it via
    # agent_index. The lead's source file is auto-vendored as a stub
    # under agents/misc/<team-id>-lead.md by vendor_agent() below.
    sources_yaml_lines = ["sources:"]
    for s in sources:
        sources_yaml_lines.append(f"  - repo: {s['repo']}")
        sources_yaml_lines.append(f'    vendor: {s["vendor"]}')
        if s.get("licensePrefix"):
            sources_yaml_lines.append(f"    licensePrefix: {s['licensePrefix']}")
    sources_yaml = "\n".join(sources_yaml_lines)

    # build.py requires lead to be a real agent id in members. Use the
    # synthetic <team-id>-lead (generated as an agent stub by vendor_agent)
    # as the explicit lead.
    lead_id = f"{tid}-lead"
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

lead: {lead_id}
members:
{members_yaml}

# ── 技能来源：vendor from skills organizations (resolved by compose_team.py) ──
{sources_yaml}

quickPrompts:
  - {{zh: "用 {tid} 的标准流程启动这个项目", en: "Bootstrap a new project in {tid}"}}
  - {{zh: "对这个代码库做一次健康检查", en: "Run a health check on this codebase"}}
  - {{zh: "升级到最新的 skills 快照", en: "Refresh to the latest vendored skills snapshot"}}

tags:
  - {{zh: "自动组装", en: "auto-assembled"}}
  - {{zh: "语言专家团", en: "language-specialist"}}
"""


# ────────────────────────── entry point ──────────────────────────

def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="write to /tmp/composed-teams/{agents,teams} for inspection "
                         "(does NOT touch the in-repo agents/ or teams/)")
    ap.add_argument("--output-dir", type=Path, default=None,
                    help="override the output directory (default: repo root)")
    args = ap.parse_args()

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

    out_root = args.output_dir or (Path("/tmp/composed-teams") if args.dry_run else ROOT)
    out_agents = out_root / "agents"
    out_teams = out_root / "teams"
    out_agents.mkdir(parents=True, exist_ok=True)
    out_teams.mkdir(parents=True, exist_ok=True)

    # vendor agents (deduped across teams) — mirror the hand-curated
    # agents/<domain>/<id>.md layout (build.py's agent_index rglob handles
    # subdirectories; files are deduped by stem so the same role agent
    # used by multiple teams only lives at one path).
    for t in teams:
        for aid in list(t.get("members", [])) + [f"{t['id']}-lead"]:
            vendor_agent(aid, out_root)
    print(f"vendored agents into {out_agents}/<domain>/")

    # render teams
    for t in teams:
        out = out_teams / f"{t['id']}.yaml"
        out.write_text(render_team_yaml(t), encoding="utf-8")
    print(f"rendered {len(teams)} team yamls into {out_teams}/")

    if args.dry_run:
        existing = sorted((ROOT / "teams").glob("*.yaml"))
        new = sorted(out_teams.glob("*.yaml"))
        existing_names = {p.name for p in existing}
        new_names = {p.name for p in new}
        print()
        print("=== dry-run summary (writes to /tmp, does NOT touch in-repo files) ===")
        print(f"  will create ({len(new_names - existing_names)}): {sorted(new_names - existing_names)[:8]}{'...' if len(new_names - existing_names) > 8 else ''}")
        print(f"  will overwrite ({len(new_names & existing_names)}): {sorted(new_names & existing_names)[:8]}{'...' if len(new_names & existing_names) > 8 else ''}")
        print(f"  no-change (manual teams): {sorted(existing_names - new_names)[:6]}")
        print()
        print(f"output: {out_root}")
        print()
        print("NOTE: dry-run does NOT build-verify because build.py reads")
        print("      agents/ from the in-repo tree only. To verify, run:")
        print("      python3 scripts/compose_team.py  (writes in-repo)")
        print("      python3 scripts/build.py teams/<tid>.yaml --out /tmp/x")

    return 0


if __name__ == "__main__":
    sys.exit(main())
