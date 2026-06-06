from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from .models import CheckRecord, CheckStatus, Phase


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _tool_names(run_dir: Path) -> list[str]:
    path = run_dir / "coding-agent-tool-calls.jsonl"
    if not path.is_file():
        return []

    names: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict) and isinstance(record.get("name"), str):
            names.append(record["name"])
    return names


def _skill_dirs(agent_home: Path) -> list[str]:
    skills = agent_home / "skills"
    if not skills.is_dir():
        return []
    return sorted(child.name for child in skills.iterdir() if child.is_dir())


def _record(name: str, phase: Phase, status: CheckStatus, detail: str) -> CheckRecord:
    return CheckRecord(name=name, phase=phase, status=status, detail=detail)


def run_check(
    name: str,
    args: list[str],
    *,
    run_dir: Path,
    workdir: Path,
    agent_home: Path,
    condition: str,
    phase: Phase,
) -> CheckRecord:
    if name == "agent-home-contained":
        contained = _is_relative_to(agent_home, run_dir)
        status: CheckStatus = "pass" if contained else "fail"
        return _record(name, phase, status, f"agent_home={agent_home}")

    if name == "condition-skill-set":
        expected_by_condition = {
            "no-skill": [],
            "with-cities2-knowledge": ["cities2-knowledge"],
        }
        expected = expected_by_condition.get(condition)
        actual = _skill_dirs(agent_home)
        if expected is None:
            return _record(
                name,
                phase,
                "indeterminate",
                f"unknown condition={condition}; actual={actual}",
            )
        status = "pass" if actual == expected else "fail"
        return _record(name, phase, status, f"expected={expected}; actual={actual}")

    if name == "skill-not-visible":
        needle = args[0] if args else ""
        actual = _skill_dirs(agent_home)
        visible = any(needle in skill_name for skill_name in actual)
        status = "pass" if needle and not visible else "fail"
        return _record(name, phase, status, f"needle={needle}; actual={actual}")

    if name == "git-branch":
        expected = args[0] if args else ""
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=workdir,
            text=True,
            capture_output=True,
        )
        actual = result.stdout.strip()
        status = "pass" if expected and result.returncode == 0 and actual == expected else "fail"
        detail = f"expected={expected}; actual={actual}; exit={result.returncode}"
        if result.stderr.strip():
            detail += f"; stderr={result.stderr.strip()}"
        return _record(name, phase, status, detail)

    if name in ("skill-called", "tool-called"):
        expected = args[0] if args else ""
        names = _tool_names(run_dir)
        status = "pass" if expected in names else "fail"
        return _record(name, phase, status, f"expected={expected}; names={names}")

    if name == "skill-not-called":
        prefix = args[0] if args else ""
        names = _tool_names(run_dir)
        called = any(tool_name.startswith(prefix) for tool_name in names)
        status = "pass" if prefix and not called else "fail"
        return _record(name, phase, status, f"prefix={prefix}; names={names}")

    if name == "not-tool-called":
        expected = args[0] if args else ""
        names = _tool_names(run_dir)
        status = "pass" if expected and expected not in names else "fail"
        return _record(name, phase, status, f"expected={expected}; names={names}")

    if name == "transcript-contains":
        needle = args[0] if args else ""
        transcript = run_dir / "transcript.txt"
        text = transcript.read_text(encoding="utf-8") if transcript.is_file() else ""
        status = "pass" if needle and needle.lower() in text.lower() else "fail"
        return _record(name, phase, status, f"needle={needle}")

    return _record(name, phase, "indeterminate", f"unknown check: {name}")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print("missing check name", file=sys.stderr)
        return 2

    phase = os.environ.get("EVAL_CHECK_PHASE", "post")
    if phase not in ("pre", "post"):
        print(f"invalid EVAL_CHECK_PHASE: {phase}", file=sys.stderr)
        return 2

    record = run_check(
        argv[0],
        argv[1:],
        run_dir=Path(os.environ["EVAL_RUN_DIR"]),
        workdir=Path(os.environ["EVAL_WORKDIR"]),
        agent_home=Path(os.environ["EVAL_AGENT_HOME"]),
        condition=os.environ.get("EVAL_CONDITION", ""),
        phase=phase,
    )

    line = json.dumps(record.to_dict(), sort_keys=True)
    sink = os.environ.get("EVAL_RECORD_SINK")
    if sink:
        with Path(sink).open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    print(line)
    return 0 if record.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
