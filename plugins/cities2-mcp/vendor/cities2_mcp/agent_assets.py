from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from . import package_root

SKILL_NAMES = (
    "cities2-knowledge",
    "cities2-modding",
    "cities2-mod-review",
    "cities2-mod-debugging",
    "cities2-mod-release",
)
LEGACY_ASSET_NAMES = ("cities2-game-updates",)

CLAUDE_COMMANDS = {
    "cities2-knowledge": """---
description: "Ask Cities2-MCP about Cities: Skylines II gameplay, systems, patches, or updates"
argument-hint: [question]
---

Use the connected `cities2-mcp` MCP server to answer this Cities: Skylines II gameplay, city-system, patch, or update question:

$ARGUMENTS

        Follow the bundled `cities2-knowledge` source workflow: call `source_status()` first, search both the wiki corpus and local game encyclopedia when available, fetch full pages or entries for important claims, and end with compact source notes.
""",
    "cities2-modding": """---
description: "Ask Cities2-MCP about Cities: Skylines II modding or local mod project workflows"
argument-hint: [question or task]
---

Use the connected `cities2-mcp` MCP server to answer this Cities: Skylines II modding question or help with this local mod project task:

$ARGUMENTS

Follow the bundled `cities2-modding` source workflow: use wiki retrieval for modding concepts and APIs, use workflow tools only inside configured workspaces, and make any local file, build, package, or launch action explicit before doing it.
""",
    "cities2-mod-review": """---
description: "Review a Cities: Skylines II mod for quality, safety, maintainability, and readiness"
argument-hint: [project or review request]
---

Use the connected `cities2-mcp` MCP server and bundled `cities2-mod-review` skill to review this Cities: Skylines II mod:

$ARGUMENTS

Focus on safety, documented best practices, negative constraints, maintainability, user value, packaging hygiene, attribution, and verification gaps.
""",
    "cities2-mod-debugging": """---
description: "Debug a Cities: Skylines II mod build, package, runtime, log, or in-game behavior issue"
argument-hint: [bug or failure]
---

Use the connected `cities2-mcp` MCP server and bundled `cities2-mod-debugging` skill to debug this Cities: Skylines II mod issue:

$ARGUMENTS

Inspect project evidence, relevant docs, build output, logs, installed files, UI debugger output, and playtesting results before claiming a fix is verified.
""",
    "cities2-mod-release": """---
description: "Check a Cities: Skylines II mod before packaging, publishing, uploading, or distributing it"
argument-hint: [release request]
---

Use the connected `cities2-mcp` MCP server and bundled `cities2-mod-release` skill to check this Cities: Skylines II mod before distribution:

$ARGUMENTS

Require local playtesting or an explicit untested override before packaging or publishing. Label untested output as not gameplay-verified.
""",
}


@dataclass(frozen=True)
class InstallResult:
    client: str
    installed: tuple[Path, ...]
    removed_legacy: tuple[Path, ...]


def source_skills_dir() -> Path:
    packaged = package_root() / "skills"
    if packaged.exists():
        return packaged
    return package_root().parent / "skills"


def _copy_skill(skill_name: str, target_root: Path) -> Path:
    src = source_skills_dir() / skill_name
    if not src.is_dir():
        raise FileNotFoundError(f"Bundled skill not found: {src}")
    dst = target_root / skill_name
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return dst


def _remove_legacy(paths: Iterable[Path]) -> tuple[Path, ...]:
    removed: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        if path.name not in LEGACY_ASSET_NAMES and path.stem not in LEGACY_ASSET_NAMES:
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        removed.append(path)
    return tuple(removed)


def install_codex_assets(home: Path, *, remove_legacy: bool = True) -> InstallResult:
    skills_dir = home / ".codex" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    installed = tuple(_copy_skill(name, skills_dir) for name in SKILL_NAMES)
    removed = _remove_legacy(skills_dir / name for name in LEGACY_ASSET_NAMES) if remove_legacy else ()
    return InstallResult(client="codex", installed=installed, removed_legacy=removed)


def install_claude_assets(
    home: Path,
    *,
    scope: str = "user",
    project_dir: Path | None = None,
    remove_legacy: bool = True,
) -> InstallResult:
    if scope not in {"user", "project"}:
        raise ValueError("Claude asset scope must be 'user' or 'project'")

    base = home / ".claude" if scope == "user" else (project_dir or Path.cwd()) / ".claude"
    skills_dir = base / "skills"
    commands_dir = base / "commands"
    skills_dir.mkdir(parents=True, exist_ok=True)
    commands_dir.mkdir(parents=True, exist_ok=True)

    installed: list[Path] = []
    installed.extend(_copy_skill(name, skills_dir) for name in SKILL_NAMES)
    for command_name, command_text in CLAUDE_COMMANDS.items():
        command_path = commands_dir / f"{command_name}.md"
        command_path.write_text(command_text, encoding="utf-8")
        installed.append(command_path)

    removed: tuple[Path, ...] = ()
    if remove_legacy:
        legacy_paths = []
        legacy_paths.extend(skills_dir / name for name in LEGACY_ASSET_NAMES)
        legacy_paths.extend(commands_dir / f"{name}.md" for name in LEGACY_ASSET_NAMES)
        removed = _remove_legacy(legacy_paths)

    return InstallResult(client="claude", installed=tuple(installed), removed_legacy=removed)


def install_agent_assets(
    clients: Iterable[str],
    *,
    home: Path | None = None,
    claude_scope: str = "user",
    claude_project_dir: Path | None = None,
    remove_legacy: bool = True,
) -> tuple[InstallResult, ...]:
    resolved_home = (home or Path.home()).expanduser().resolve()
    client_list = tuple(clients)
    requested = tuple(dict.fromkeys("codex" if client == "all" else client for client in client_list))
    if "all" in client_list:
        requested = ("codex", "claude")

    results: list[InstallResult] = []
    for client in requested:
        if client == "codex":
            results.append(install_codex_assets(resolved_home, remove_legacy=remove_legacy))
        elif client == "claude":
            results.append(
                install_claude_assets(
                    resolved_home,
                    scope=claude_scope,
                    project_dir=claude_project_dir,
                    remove_legacy=remove_legacy,
                )
            )
        else:
            raise ValueError(f"Unsupported client: {client}")
    return tuple(results)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cities2-mcp install-agent-assets",
        description="Install bundled Cities2-MCP agent skills and Claude slash commands.",
    )
    parser.add_argument(
        "--client",
        action="append",
        choices=("all", "codex", "claude"),
        default=None,
        help="Client assets to install. Repeat to install multiple clients. Defaults to all.",
    )
    parser.add_argument("--home", type=Path, help="Override the user home directory for installation.")
    parser.add_argument(
        "--claude-scope",
        choices=("user", "project"),
        default="user",
        help="Install Claude assets under ~/.claude or under <project>/.claude.",
    )
    parser.add_argument(
        "--claude-project-dir",
        type=Path,
        help="Project directory for --claude-scope project. Defaults to the current directory.",
    )
    parser.add_argument(
        "--keep-legacy",
        action="store_true",
        help="Do not remove old agent asset names such as cities2-game-updates.",
    )
    args = parser.parse_args(argv)

    clients = args.client or ["all"]
    results = install_agent_assets(
        clients,
        home=args.home,
        claude_scope=args.claude_scope,
        claude_project_dir=args.claude_project_dir,
        remove_legacy=not args.keep_legacy,
    )

    for result in results:
        print(f"{result.client}: installed {len(result.installed)} asset(s)")
        for path in result.installed:
            print(f"  installed {path}")
        for path in result.removed_legacy:
            print(f"  removed legacy {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
