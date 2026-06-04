from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path

from .models import CheckRecord, Phase


def _is_wsl_bash() -> bool:
    result = subprocess.run(
        ["bash", "-lc", "uname -r"],
        text=True,
        capture_output=True,
    )
    return result.returncode == 0 and "microsoft" in result.stdout.lower()


def _bash_path(path: Path, *, wsl: bool) -> str:
    value = path.resolve().as_posix()
    if len(value) >= 2 and value[1] == ":":
        drive = value[0].lower()
        if wsl:
            return f"/mnt/{drive}{value[2:]}"
        return value
    return value


def _source_command(checks: Path, *, wsl: bool) -> str:
    source_path = _bash_path(checks, wsl=wsl)
    source = f"source <(tr -d '\\r' < {shlex.quote(source_path)})"
    if wsl or not (len(source_path) >= 2 and source_path[1] == ":"):
        return source

    msys_path = f"/{source_path[0].lower()}{source_path[2:]}"
    msys_source = f"source <(tr -d '\\r' < {shlex.quote(msys_path)})"
    return (
        f"{{ {source} 2>/dev/null "
        f"|| {msys_source}; }}"
    )


def _read_records(path: Path) -> list[CheckRecord]:
    if not path.is_file():
        return []

    records: list[CheckRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        data = json.loads(line)
        if not isinstance(data, dict):
            raise TypeError(f"check record must be an object: {data!r}")
        records.append(
            CheckRecord(
                name=data["name"],
                phase=data["phase"],
                status=data["status"],
                detail=data["detail"],
            )
        )
    return records


def run_checks_phase(
    checks: Path,
    phase: Phase,
    *,
    run_dir: Path,
    workdir: Path,
    agent_home: Path,
    condition: str,
    repo_root: Path,
) -> list[CheckRecord]:
    sink = run_dir / f"{phase}-checks.jsonl"
    wsl = _is_wsl_bash()
    env = dict(os.environ)
    check_env = {
        "EVAL_RUN_DIR": _bash_path(run_dir, wsl=wsl),
        "EVAL_WORKDIR": _bash_path(workdir, wsl=wsl),
        "EVAL_AGENT_HOME": _bash_path(agent_home, wsl=wsl),
        "EVAL_CONDITION": condition,
        "EVAL_CHECK_PHASE": phase,
        "EVAL_RECORD_SINK": _bash_path(sink, wsl=wsl),
        "PYTHONPATH": _bash_path(repo_root, wsl=wsl),
    }
    env.update(check_env)
    if wsl:
        check_env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        env["PATH"] = check_env["PATH"]
    exports = "".join(
        f"export {name}={shlex.quote(value)}; "
        for name, value in check_env.items()
    )
    python_shim = 'python() { python3 "\\$@"; }; ' if wsl else ""
    cd_workdir = f"cd {shlex.quote(_bash_path(workdir, wsl=wsl))}; " if wsl else ""
    command = f"{exports}{python_shim}{cd_workdir}{_source_command(checks, wsl=wsl)}; {phase}"
    result = subprocess.run(
        ["bash", "-lc", command],
        cwd=repo_root if wsl else workdir,
        env=env,
        text=True,
        capture_output=True,
    )

    records = _read_records(sink)
    if result.returncode != 0 and not records:
        detail = (
            f"exit={result.returncode}; stdout={result.stdout.strip()}; "
            f"stderr={result.stderr.strip()}"
        )
        records.append(
            CheckRecord(
                name=f"{phase}-checks",
                phase=phase,
                status="fail",
                detail=detail,
            )
        )
    return records
