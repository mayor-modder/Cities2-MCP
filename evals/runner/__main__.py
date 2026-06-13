from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path

from evals.runner.checks import _bash_path, _is_wsl_bash, run_checks_phase
from evals.runner.conditions import CONDITION_SKILLS, condition_skills
from evals.runner.codex_adapter import (
    build_codex_exec_command,
    minimal_codex_env,
    prepare_codex_home,
    seed_codex_auth,
)
from evals.runner.models import CheckRecord, RunMetadata, RunPaths, Verdict
from evals.runner.scenario import Scenario, load_scenario
from evals.runner.summary import generate_digest, write_digest
from evals.runner.trace import normalize_codex_events


RUNNER_VERSION = "1"
KNOWLEDGE_MCP_PREFLIGHT_TOOLS = ("source_status", "search")
MCP_PREFLIGHT_TIMEOUT_SECONDS = 45


def _condition_skills(condition: str) -> tuple[str, ...]:
    return condition_skills(condition)


def _prompt_from_story(story: Path) -> str:
    text = story.read_text(encoding="utf-8")
    start_marker = "```text\n"
    start = text.find(start_marker)
    if start == -1:
        raise ValueError("story.md missing fenced text prompt")
    prompt_start = start + len(start_marker)
    end = text.find("\n```", prompt_start)
    if end == -1:
        raise ValueError("story.md has unclosed fenced text prompt")
    return text[prompt_start:end].strip()


def _repo_commit(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def _skill_checksums(repo_root: Path, skills: tuple[str, ...]) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for skill in skills:
        digest = hashlib.sha256()
        digest.update((repo_root / "skills" / skill / "SKILL.md").read_bytes())
        checksums[skill] = f"sha256:{digest.hexdigest()}"
    return checksums


def _utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _new_run_dir(
    results_root: Path, scenario_id: str, condition: str, trial: int
) -> Path:
    results_root.mkdir(parents=True, exist_ok=True)
    stamp = _utc_timestamp()
    candidate = results_root / f"{scenario_id}-{condition}-trial-{trial}-{stamp}"
    candidate.mkdir(exist_ok=False)
    return candidate


def _run_setup(setup: Path, workdir: Path) -> None:
    wsl = _is_wsl_bash()
    if wsl:
        command = (
            f"cd {shlex.quote(_bash_path(workdir, wsl=True))}; "
            f"bash {shlex.quote(_bash_path(setup, wsl=True))}"
        )
        args = ["bash", "-lc", command]
    else:
        args = ["bash", setup.as_posix()]
    try:
        result = subprocess.run(
            args,
            cwd=workdir,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError("scenario setup failed: bash executable not found") from error
    if result.returncode != 0:
        detail = (
            f"exit={result.returncode}; stdout={result.stdout.strip()}; "
            f"stderr={result.stderr.strip()}"
        )
        raise RuntimeError(f"scenario setup failed: {detail}")


def _metadata(
    *,
    scenario: Scenario,
    condition: str,
    trial: int,
    codex_command: str,
    repo_root: Path,
    skills: tuple[str, ...],
) -> RunMetadata:
    return RunMetadata(
        scenario_id=scenario.id,
        scenario_version="1",
        condition_id=condition,
        trial=trial,
        backend_name="codex",
        backend_executable=codex_command,
        repo_commit=_repo_commit(repo_root),
        runner_version=RUNNER_VERSION,
        run_started_at=dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        skill_checksums=_skill_checksums(repo_root, skills),
    )


def _final_status(
    pre_records: list[CheckRecord], all_records: list[CheckRecord]
) -> tuple[str, str]:
    if any(record.status == "indeterminate" for record in pre_records):
        return "indeterminate", "one or more pre-checks were indeterminate"
    if any(record.status != "pass" for record in pre_records):
        return "indeterminate", "one or more pre-checks failed"
    if any(record.status == "indeterminate" for record in all_records):
        return "indeterminate", "one or more checks were indeterminate"
    if all(record.status == "pass" for record in all_records):
        return "pass", "all checks passed"
    return "fail", "one or more post-checks failed"


def _codex_command_with_prefix(
    *, codex_command: str, codex_args_prefix: tuple[str, ...], workdir: Path, prompt: str
) -> list[str]:
    command = build_codex_exec_command(
        codex_command=codex_command, workdir=workdir, prompt=prompt
    )
    return [command[0], *codex_args_prefix, *command[1:]]


def _append_stderr(raw_events: Path, stderr: str) -> None:
    with raw_events.open("a", encoding="utf-8") as stream:
        stream.write(stderr)


def _mcp_preflight_tools(condition: str) -> tuple[str, ...]:
    if condition == "with-cities2-knowledge":
        return KNOWLEDGE_MCP_PREFLIGHT_TOOLS
    return ()


def _tool_name_matches(actual: str, expected: str) -> bool:
    return actual == expected or actual.endswith(f"__{expected}")


def _trace_tool_names(tool_calls: Path) -> list[str]:
    if not tool_calls.is_file():
        return []
    names: list[str] = []
    for line in tool_calls.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict) and isinstance(record.get("name"), str):
            names.append(record["name"])
    return names


def _mcp_error_messages(raw_events: Path) -> list[str]:
    if not raw_events.is_file():
        return []
    messages: list[str] = []
    for line in raw_events.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        error = item.get("error")
        if not isinstance(error, dict):
            continue
        message = error.get("message")
        if isinstance(message, str) and message:
            messages.append(message)
    return messages


def _run_codex_mcp_tool_preflight(
    *,
    paths: RunPaths,
    condition: str,
    repo_root: Path,
    codex_command: str,
    codex_args_prefix: tuple[str, ...],
    env: dict[str, str],
) -> CheckRecord | None:
    expected_tools = _mcp_preflight_tools(condition)
    if not expected_tools:
        return None

    raw_events = paths.run_dir / "codex-preflight-events.jsonl"
    tool_calls = paths.run_dir / "codex-preflight-tool-calls.jsonl"
    transcript = paths.run_dir / "codex-preflight-transcript.txt"
    prompt = (
        "Eval plumbing preflight. Use $cities2-knowledge and the cities2-mcp MCP "
        "server. Call source_status(), then call search(query=\"office demand\", "
        "limit=1). Do not run shell commands, inspect files, or diagnose the "
        "workspace. If either MCP tool is unavailable or fails, stop immediately "
        "and answer with only MCP preflight failed. After both tool calls succeed, "
        "answer with only MCP preflight passed."
    )
    command = _codex_command_with_prefix(
        codex_command=codex_command,
        codex_args_prefix=codex_args_prefix,
        workdir=paths.workdir,
        prompt=prompt,
    )
    try:
        with raw_events.open("w", encoding="utf-8") as stdout:
            result = subprocess.run(
                command,
                cwd=repo_root,
                env=env,
                text=True,
                stdout=stdout,
                stderr=subprocess.PIPE,
                timeout=MCP_PREFLIGHT_TIMEOUT_SECONDS,
            )
    except subprocess.TimeoutExpired:
        normalize_codex_events(raw_events, tool_calls, transcript)
        names = _trace_tool_names(tool_calls)
        errors = _mcp_error_messages(raw_events)
        detail = (
            f"expected={list(expected_tools)}; names={names}; "
            f"timeout={MCP_PREFLIGHT_TIMEOUT_SECONDS}s"
        )
        if errors:
            detail += f"; errors={errors[:3]}"
        return CheckRecord(
            name="codex-mcp-tool-exposure",
            phase="pre",
            status="indeterminate",
            detail=detail,
        )
    if result.returncode != 0:
        _append_stderr(raw_events, result.stderr or "")
    normalize_codex_events(raw_events, tool_calls, transcript)

    names = _trace_tool_names(tool_calls)
    has_expected = all(
        any(_tool_name_matches(tool_name, expected) for tool_name in names)
        for expected in expected_tools
    )
    detail = f"expected={list(expected_tools)}; names={names}"
    errors = _mcp_error_messages(raw_events)
    if errors:
        detail += f"; errors={errors[:3]}"
    if result.returncode != 0:
        detail += f"; exit={result.returncode}"
    return CheckRecord(
        name="codex-mcp-tool-exposure",
        phase="pre",
        status="pass" if has_expected and result.returncode == 0 else "indeterminate",
        detail=detail,
    )


def run_eval(
    *,
    scenario_path: Path,
    condition: str,
    repo_root: Path,
    results_root: Path,
    codex_command: str = "codex",
    codex_args_prefix: tuple[str, ...] = (),
    live_auth: bool = True,
    trial: int = 1,
) -> RunPaths:
    scenario = load_scenario(scenario_path)
    skills = _condition_skills(condition)
    paths = RunPaths.from_run_dir(
        _new_run_dir(results_root, scenario.id, condition, trial)
    )
    prompt = _prompt_from_story(scenario.story)

    paths.workdir.mkdir()
    prepare_codex_home(
        repo_root=repo_root,
        codex_home=paths.agent_home,
        workspace=paths.workdir,
        skills=skills,
    )
    _run_setup(scenario.setup.resolve(), paths.workdir)
    env = minimal_codex_env(
        codex_home=paths.agent_home, repo_root=repo_root, include_auth=live_auth
    )
    if live_auth:
        seed_codex_auth(codex_home=paths.agent_home, env=env)

    pre_records = run_checks_phase(
        scenario.checks,
        "pre",
        run_dir=paths.run_dir,
        workdir=paths.workdir,
        agent_home=paths.agent_home,
        condition=condition,
        repo_root=repo_root,
    )
    if all(record.status == "pass" for record in pre_records):
        preflight = _run_codex_mcp_tool_preflight(
            paths=paths,
            condition=condition,
            repo_root=repo_root,
            codex_command=codex_command,
            codex_args_prefix=codex_args_prefix,
            env=env,
        )
        if preflight is not None:
            pre_records.append(preflight)

    codex_return_code: int | None = None
    if all(record.status == "pass" for record in pre_records):
        command = _codex_command_with_prefix(
            codex_command=codex_command,
            codex_args_prefix=codex_args_prefix,
            workdir=paths.workdir,
            prompt=prompt,
        )
        with paths.raw_events.open("w", encoding="utf-8") as stdout:
            result = subprocess.run(
                command,
                cwd=repo_root,
                env=env,
                text=True,
                stdout=stdout,
                stderr=subprocess.PIPE,
            )
        codex_return_code = result.returncode
        if result.returncode != 0:
            _append_stderr(paths.raw_events, result.stderr or "")
    else:
        paths.raw_events.write_text("", encoding="utf-8")

    normalize_codex_events(paths.raw_events, paths.tool_calls, paths.transcript)
    post_records: list[CheckRecord] = []
    if all(record.status == "pass" for record in pre_records):
        post_records = run_checks_phase(
            scenario.checks,
            "post",
            run_dir=paths.run_dir,
            workdir=paths.workdir,
            agent_home=paths.agent_home,
            condition=condition,
            repo_root=repo_root,
        )
    if codex_return_code not in (None, 0):
        post_records.append(
            CheckRecord(
                name="codex-exit",
                phase="post",
                status="fail",
                detail=f"exit={codex_return_code}",
            )
        )
    all_records = pre_records + post_records
    final, final_reason = _final_status(pre_records, all_records)
    metadata = _metadata(
        scenario=scenario,
        condition=condition,
        trial=trial,
        codex_command=codex_command,
        repo_root=repo_root,
        skills=skills,
    )
    verdict = Verdict(
        metadata=metadata,
        final=final,
        final_reason=final_reason,
        checks=all_records,
        trace_path=paths.tool_calls.name,
        transcript_path=paths.transcript.name,
    )
    paths.verdict.write_text(
        json.dumps(verdict.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
    return paths


def _run_eval_command(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.runner")
    parser.add_argument("scenario_path", type=Path)
    parser.add_argument(
        "--condition",
        choices=tuple(CONDITION_SKILLS),
        required=True,
    )
    parser.add_argument("--results-root", type=Path, default=Path("evals/results"))
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--no-live-auth", action="store_true")
    parser.add_argument("--trial", type=int, default=1)
    args = parser.parse_args(argv)

    paths = run_eval(
        scenario_path=args.scenario_path,
        condition=args.condition,
        repo_root=Path.cwd(),
        results_root=args.results_root,
        codex_command=args.codex_command,
        live_auth=not args.no_live_auth,
        trial=args.trial,
    )
    verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))
    print(paths.verdict)
    if verdict["final"] == "pass":
        return 0
    if verdict["final"] == "fail":
        return 1
    return 2


def _run_summarize_command(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.runner summarize")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("verdicts", type=Path, nargs="+")
    args = parser.parse_args(argv)

    write_digest(generate_digest(args.verdicts), args.output)
    print(args.output)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] == "summarize":
        return _run_summarize_command(args[1:])
    return _run_eval_command(args)


if __name__ == "__main__":
    raise SystemExit(main())
