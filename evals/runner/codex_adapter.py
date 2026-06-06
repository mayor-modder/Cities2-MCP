from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


class CodexAdapterError(RuntimeError):
    """Raised when the Codex clean-room adapter cannot prepare or run."""


def _toml_string(value: object) -> str:
    return json.dumps(str(value))


def _copy_skill(repo_root: Path, codex_home: Path, skill_name: str) -> None:
    if (
        Path(skill_name).name != skill_name
        or "/" in skill_name
        or "\\" in skill_name
        or skill_name in ("", ".", "..")
    ):
        raise CodexAdapterError(f"invalid skill name: {skill_name}")
    source = repo_root / "skills" / skill_name
    if not source.is_dir():
        raise CodexAdapterError(f"missing source skill: {skill_name}")
    target = codex_home / "skills" / skill_name
    shutil.copytree(source, target)


def _write_mcp_config(codex_home: Path, workspace: Path) -> None:
    resolved_workspace = workspace.resolve()
    config = "\n".join(
        [
            "[mcp_servers.cities2-mcp]",
            f"command = {_toml_string(sys.executable)}",
            (
                "args = ["
                '"-m", '
                '"cities2_mcp.mcp_server", '
                '"--workspace", '
                f"{_toml_string(resolved_workspace)}"
                "]"
            ),
            "",
        ]
    )
    (codex_home / "config.toml").write_text(config, encoding="utf-8")


def prepare_codex_home(
    *,
    repo_root: Path,
    codex_home: Path,
    skills: tuple[str, ...],
    workspace: Path | None = None,
) -> None:
    codex_home.mkdir(parents=True, exist_ok=False)
    (codex_home / "skills").mkdir()
    for skill_name in skills:
        _copy_skill(repo_root, codex_home, skill_name)
    _write_mcp_config(codex_home, workspace if workspace is not None else repo_root)


def _host_env_value(name: str) -> str | None:
    if name in os.environ:
        return os.environ[name]
    for existing_name, value in os.environ.items():
        if existing_name.upper() == name:
            return value
    return None


def _default_host_codex_home() -> Path:
    configured = _host_env_value("CODEX_HOME")
    return Path(configured) if configured else Path.home() / ".codex"


def minimal_codex_env(
    *, codex_home: Path, repo_root: Path, include_auth: bool
) -> dict[str, str]:
    env = {
        "CODEX_HOME": str(codex_home),
        "PYTHONPATH": str(repo_root),
    }
    for name in ("PATH", "PATHEXT", "COMSPEC", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"):
        value = _host_env_value(name)
        if value is not None:
            env[name] = value
    if include_auth and "OPENAI_API_KEY" in os.environ:
        env["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]
    return env


def seed_codex_auth(
    *,
    codex_home: Path,
    env: dict[str, str],
    host_codex_home: Path | None = None,
) -> None:
    api_key = env.get("OPENAI_API_KEY")
    if not api_key:
        source_auth = (host_codex_home or _default_host_codex_home()) / "auth.json"
        if not source_auth.is_file():
            raise CodexAdapterError(
                "OPENAI_API_KEY or local Codex auth is required for live Codex evals"
            )
        shutil.copy2(source_auth, codex_home / "auth.json")
        return
    command_env = dict(env)
    command_env["CODEX_HOME"] = str(codex_home)
    command_env.pop("OPENAI_API_KEY", None)
    result = subprocess.run(
        ["codex", "login", "--with-api-key"],
        input=api_key,
        text=True,
        capture_output=True,
        env=command_env,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip().replace(api_key, "[REDACTED]")
        raise CodexAdapterError(
            f"codex login failed with exit {result.returncode}: {stderr}"
        )


def build_codex_exec_command(
    *, codex_command: str, workdir: Path, prompt: str
) -> list[str]:
    return [
        codex_command,
        "exec",
        "--json",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--dangerously-bypass-approvals-and-sandbox",
        "-C",
        str(workdir),
        prompt,
    ]
