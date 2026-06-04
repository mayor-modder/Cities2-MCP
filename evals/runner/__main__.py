from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shlex
import subprocess
from pathlib import Path

from evals.runner.checks import _bash_path, _is_wsl_bash, run_checks_phase
from evals.runner.codex_adapter import (
    build_codex_exec_command,
    minimal_codex_env,
    prepare_codex_home,
    seed_codex_auth,
)
from evals.runner.models import CheckRecord, RunMetadata, RunPaths, Verdict
from evals.runner.scenario import Scenario, load_scenario
from evals.runner.trace import normalize_codex_events


RUNNER_VERSION = "1"


def _condition_skills(condition: str) -> tuple[str, ...]:
    if condition == "no-skill":
        return ()
    if condition == "with-cities2-knowledge":
        return ("cities2-knowledge",)
    raise ValueError(f"unsupported condition: {condition}")


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
    if any(record.status != "pass" for record in pre_records):
        return "indeterminate", "one or more pre-checks failed"
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
    pre_records = run_checks_phase(
        scenario.checks,
        "pre",
        run_dir=paths.run_dir,
        workdir=paths.workdir,
        agent_home=paths.agent_home,
        condition=condition,
        repo_root=repo_root,
    )

    env = minimal_codex_env(
        codex_home=paths.agent_home, repo_root=repo_root, include_auth=live_auth
    )
    if live_auth:
        seed_codex_auth(codex_home=paths.agent_home, env=env)

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.runner")
    parser.add_argument("scenario_path", type=Path)
    parser.add_argument(
        "--condition",
        choices=("no-skill", "with-cities2-knowledge"),
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


if __name__ == "__main__":
    raise SystemExit(main())
