from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


class ClaudeAdapterError(RuntimeError):
    """Raised when the Claude clean-room adapter cannot prepare or run."""


@dataclass(frozen=True)
class ClaudeRunConfig:
    mcp_config: Path
    plugin_dir: Path | None


def _copy_skill(repo_root: Path, plugin_root: Path, skill_name: str) -> None:
    if (
        Path(skill_name).name != skill_name
        or "/" in skill_name
        or "\\" in skill_name
        or skill_name in ("", ".", "..")
    ):
        raise ClaudeAdapterError(f"invalid skill name: {skill_name}")
    source = repo_root / "skills" / skill_name
    if not source.is_dir():
        raise ClaudeAdapterError(f"missing source skill: {skill_name}")
    target = plugin_root / "skills" / skill_name
    shutil.copytree(source, target)


def _host_env_value(name: str) -> str | None:
    if name in os.environ:
        return os.environ[name]
    for existing_name, value in os.environ.items():
        if existing_name.upper() == name:
            return value
    return None


def _default_host_claude_home() -> Path:
    configured = _host_env_value("CLAUDE_CONFIG_DIR")
    return Path(configured) if configured else Path.home() / ".claude"


def _mcp_server_env(repo_root: Path) -> dict[str, str]:
    env = {"PYTHONPATH": str(repo_root.resolve())}
    for name in ("SYSTEMROOT", "WINDIR"):
        value = _host_env_value(name)
        if value is not None:
            env[name] = value
    return env


def _write_mcp_config(config_path: Path, workspace: Path, repo_root: Path) -> None:
    config = {
        "mcpServers": {
            "cities2-mcp": {
                "command": sys.executable,
                "args": [
                    "-m",
                    "cities2_mcp.mcp_server",
                    "--workspace",
                    str(workspace.resolve()),
                ],
                "env": _mcp_server_env(repo_root),
            }
        }
    }
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def prepare_claude_home(
    *,
    repo_root: Path,
    claude_home: Path,
    skills: tuple[str, ...],
    workspace: Path,
) -> ClaudeRunConfig:
    claude_home.mkdir(parents=True, exist_ok=False)
    mcp_config = claude_home / "mcp.json"
    _write_mcp_config(mcp_config, workspace, repo_root)

    plugin_dir: Path | None = None
    if skills:
        plugin_dir = claude_home / "plugins" / "cities2-mcp-eval"
        (plugin_dir / ".claude-plugin").mkdir(parents=True)
        (plugin_dir / "skills").mkdir()
        plugin = {
            "name": "cities2-mcp-eval",
            "displayName": "Cities2 MCP Eval Skills",
            "version": "0.0.0",
            "description": "Clean-room Cities2 skill subset for eval runs.",
        }
        (plugin_dir / ".claude-plugin" / "plugin.json").write_text(
            json.dumps(plugin, indent=2) + "\n",
            encoding="utf-8",
        )
        for skill_name in skills:
            _copy_skill(repo_root, plugin_dir, skill_name)

    return ClaudeRunConfig(mcp_config=mcp_config, plugin_dir=plugin_dir)


def minimal_claude_env(
    *, claude_home: Path, repo_root: Path, include_auth: bool
) -> dict[str, str]:
    env = {
        "CLAUDE_CONFIG_DIR": str(claude_home.resolve()),
        "PYTHONPATH": str(repo_root.resolve()),
    }
    for name in (
        "PATH",
        "PATHEXT",
        "COMSPEC",
        "SYSTEMROOT",
        "WINDIR",
        "APPDATA",
        "LOCALAPPDATA",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
    ):
        value = _host_env_value(name)
        if value is not None:
            env[name] = value
    if include_auth and "ANTHROPIC_API_KEY" in os.environ:
        env["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]
    return env


def seed_claude_auth(
    *,
    claude_home: Path,
    env: dict[str, str],
    host_claude_home: Path | None = None,
) -> None:
    if "ANTHROPIC_API_KEY" in env:
        return

    source_credentials = (host_claude_home or _default_host_claude_home()) / ".credentials.json"
    if not source_credentials.is_file():
        raise ClaudeAdapterError(
            "ANTHROPIC_API_KEY or local Claude OAuth credentials are required for live Claude evals"
        )
    shutil.copy2(source_credentials, claude_home / ".credentials.json")


def build_claude_print_command(
    *,
    claude_command: str,
    workdir: Path,
    prompt: str,
    mcp_config: Path,
    plugin_dir: Path | None,
) -> list[str]:
    command = [
        claude_command,
        "-p",
        "--verbose",
        "--output-format",
        "stream-json",
        "--permission-mode",
        "bypassPermissions",
        "--no-session-persistence",
        "--strict-mcp-config",
        "--mcp-config",
        str(mcp_config.resolve()),
        "--add-dir",
        str(workdir.resolve()),
    ]
    if plugin_dir is not None:
        command.extend(["--plugin-dir", str(plugin_dir.resolve())])
    command.append(prompt)
    return command
