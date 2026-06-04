# Skill eval runner spike implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a verifiable `cities2-knowledge` eval runner spike as a series
of small feature branches stacked on the long-running evals harness branch.

**Architecture:** Keep the durable scenario format Quorum-compatible:
`story.md`, `setup.sh`, and `checks.sh`. Add a minimal local Python runner that
creates a clean Codex home per run, installs only declared skill files, captures
Codex JSON events, normalizes trace data, runs deterministic shell checks, and
writes a verdict under gitignored `evals/results/`.

**Tech Stack:** Python 3.10 standard library, `unittest`, Bash scenario hooks,
Codex CLI, Cities2-MCP stdio server launched with
`python -m cities2_mcp.mcp_server`.

---

## Stack and branch rules

Current stack point:

- `origin/codex/evals-harness` already contains the eval scenario layout,
  `evals/README.md`, `evals/runner/models.py` with `Scenario`,
  `evals/runner/scenario.py`, the
  `evals/scenarios/spike/cities2-knowledge-office-demand/` scenario, and
  loader/layout tests.
- Do not reimplement that work in this plan.

Branch strategy:

- Create each feature branch from the latest `origin/codex/evals-harness`.
- Target each feature PR at `codex/evals-harness`, not `main`.
- After a feature PR merges, update `codex/evals-harness`, then branch the
  next feature from it.
- Merge `codex/evals-harness` to `main` only after the offline runner spike has
  a recorded decision note and the maintainer approves that gate.
- Do not edit any `SKILL.md` file in this plan.
- Do not commit anything under `evals/results/`.
- Each task below includes the exact branch creation command for that feature
  branch. Use that command unless the maintainer asks for a different branch
  name.

## File structure

Existing files kept from the stack point:

- `evals/__init__.py`: package marker.
- `evals/README.md`: overview of scenario layout and gitignored results.
- `evals/runner/__init__.py`: package marker.
- `evals/runner/models.py`: currently contains `Scenario`.
- `evals/runner/scenario.py`: loads and validates Quorum-compatible scenarios.
- `evals/scenarios/spike/cities2-knowledge-office-demand/story.md`: the spike
  prompt and acceptance criteria.
- `evals/scenarios/spike/cities2-knowledge-office-demand/setup.sh`: creates a
  clean git fixture.
- `evals/scenarios/spike/cities2-knowledge-office-demand/checks.sh`: calls the
  deterministic check helper commands that later branches add.
- `tests/test_eval_scenario_layout.py`: scenario layout guardrails.
- `tests/test_eval_scenario_loader.py`: scenario loader tests.

Files added or modified by this plan:

- Modify `evals/runner/models.py`: add run metadata, check records, verdicts,
  and run path models.
- Create `tests/test_eval_run_models.py`: focused tests for the model layer.
- Create `evals/runner/codex_adapter.py`: clean-room `CODEX_HOME`
  preparation, skill installation, MCP config writing, minimal environment, and
  command construction.
- Create `tests/test_eval_codex_adapter.py`: clean-room setup tests.
- Create `evals/runner/trace.py`: normalize Codex JSON events into a compact
  tool-call JSONL file and transcript text.
- Create `tests/test_eval_trace.py`: trace normalization tests.
- Create `evals/runner/check_tool.py`: deterministic check command used by
  scenario `checks.sh`.
- Create `evals/runner/checks.py`: executes `pre()` and `post()` from
  `checks.sh` and collects check records.
- Create `tests/test_eval_checks.py`: check helper and shell hook tests.
- Create `evals/runner/__main__.py`: `python -m evals.runner` entrypoint.
- Create `tests/test_eval_runner_cli.py`: fake-Codex orchestration tests.
- Create
  `docs/superpowers/evaluations/2026-06-04-cities2-knowledge-runner-spike.md`:
  offline spike instructions, optional real-client direction, and curated result
  summary.

### Task 1: run metadata models

Branch: `codex/evals-run-models`

**Files:**

- Modify: `evals/runner/models.py`
- Create: `tests/test_eval_run_models.py`

- [ ] **Step 1: create the branch**

Run:

```powershell
git fetch origin
git switch -c codex/evals-run-models origin/codex/evals-harness
git status --short --branch
```

Expected: branch is `codex/evals-run-models` and the worktree is clean.

- [ ] **Step 2: write the failing tests**

Create `tests/test_eval_run_models.py`:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class EvalRunModelsTests(unittest.TestCase):
    def test_verdict_serializes_metadata_and_checks(self) -> None:
        from evals.runner.models import CheckRecord, RunMetadata, Verdict

        metadata = RunMetadata(
            scenario_id="cities2-knowledge-office-demand",
            scenario_version="1",
            condition_id="with-cities2-knowledge",
            trial=1,
            backend_name="codex",
            backend_executable="codex",
            repo_commit="abc1234",
            runner_version="1",
            run_started_at="2026-06-01T12:00:00Z",
            skill_checksums={"cities2-knowledge": "sha256:1234"},
        )
        verdict = Verdict(
            metadata=metadata,
            final="pass",
            final_reason="all checks passed",
            checks=[
                CheckRecord(
                    name="source_status_called",
                    phase="post",
                    status="pass",
                    detail="source_status appeared before search",
                )
            ],
            trace_path="coding-agent-tool-calls.jsonl",
            transcript_path="transcript.txt",
        )

        data = verdict.to_dict()

        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["metadata"]["scenario_id"], "cities2-knowledge-office-demand")
        self.assertEqual(data["metadata"]["skill_checksums"]["cities2-knowledge"], "sha256:1234")
        self.assertEqual(data["checks"][0]["status"], "pass")

    def test_run_paths_are_inside_run_directory(self) -> None:
        from evals.runner.models import RunPaths

        with tempfile.TemporaryDirectory(prefix="cities2-eval-run-") as tmp:
            paths = RunPaths.from_run_dir(Path(tmp))

            self.assertEqual(paths.workdir, Path(tmp) / "coding-agent-workdir")
            self.assertEqual(paths.agent_home, Path(tmp) / "coding-agent-config")
            self.assertEqual(paths.raw_events, Path(tmp) / "codex-events.jsonl")
            self.assertEqual(paths.tool_calls, Path(tmp) / "coding-agent-tool-calls.jsonl")
            self.assertEqual(paths.transcript, Path(tmp) / "transcript.txt")
            self.assertEqual(paths.verdict, Path(tmp) / "verdict.json")

    def test_verdict_json_is_plain_data(self) -> None:
        from evals.runner.models import CheckRecord

        record = CheckRecord(
            name="agent_home_contained",
            phase="pre",
            status="fail",
            detail="agent home was outside the run directory",
        )

        json.dumps(record.to_dict())
```

- [ ] **Step 3: run the tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_eval_run_models -v
```

Expected: failures because `RunMetadata`, `CheckRecord`, `Verdict`, and
`RunPaths.from_run_dir()` do not exist.

- [ ] **Step 4: add the model implementation**

Replace `evals/runner/models.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

CheckStatus = Literal["pass", "fail", "indeterminate"]
FinalStatus = Literal["pass", "fail", "indeterminate"]
Phase = Literal["pre", "post"]


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    path: Path
    story: Path
    setup: Path
    checks: Path


@dataclass(frozen=True)
class CheckRecord:
    name: str
    phase: Phase
    status: CheckStatus
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "phase": self.phase,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class RunMetadata:
    scenario_id: str
    scenario_version: str
    condition_id: str
    trial: int
    backend_name: str
    backend_executable: str
    repo_commit: str
    runner_version: str
    run_started_at: str
    skill_checksums: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_version": self.scenario_version,
            "condition_id": self.condition_id,
            "trial": self.trial,
            "backend_name": self.backend_name,
            "backend_executable": self.backend_executable,
            "repo_commit": self.repo_commit,
            "runner_version": self.runner_version,
            "run_started_at": self.run_started_at,
            "skill_checksums": dict(sorted(self.skill_checksums.items())),
        }


@dataclass(frozen=True)
class Verdict:
    metadata: RunMetadata
    final: FinalStatus
    final_reason: str
    checks: list[CheckRecord] = field(default_factory=list)
    trace_path: str | None = None
    transcript_path: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "metadata": self.metadata.to_dict(),
            "final": self.final,
            "final_reason": self.final_reason,
            "checks": [record.to_dict() for record in self.checks],
            "trace_path": self.trace_path,
            "transcript_path": self.transcript_path,
        }


@dataclass(frozen=True)
class RunPaths:
    run_dir: Path
    workdir: Path
    agent_home: Path
    raw_events: Path
    tool_calls: Path
    transcript: Path
    verdict: Path

    @classmethod
    def from_run_dir(cls, run_dir: Path) -> RunPaths:
        return cls(
            run_dir=run_dir,
            workdir=run_dir / "coding-agent-workdir",
            agent_home=run_dir / "coding-agent-config",
            raw_events=run_dir / "codex-events.jsonl",
            tool_calls=run_dir / "coding-agent-tool-calls.jsonl",
            transcript=run_dir / "transcript.txt",
            verdict=run_dir / "verdict.json",
        )
```

- [ ] **Step 5: run model and existing eval tests**

Run:

```powershell
python -m unittest tests.test_eval_run_models tests.test_eval_scenario_loader tests.test_eval_scenario_layout -v
```

Expected: `OK`.

- [ ] **Step 6: run the code-change test gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: `OK`.

- [ ] **Step 7: commit**

Run:

```powershell
git add evals/runner/models.py tests/test_eval_run_models.py
git commit -m "Add eval run metadata models"
```

Open a PR targeting `codex/evals-harness`. Merge only after review and the test
gate passes.

### Task 2: Codex clean-room adapter

Branch: `codex/evals-codex-clean-room`

**Files:**

- Create: `evals/runner/codex_adapter.py`
- Create: `tests/test_eval_codex_adapter.py`

- [ ] **Step 1: create the branch from the updated harness**

Run:

```powershell
git fetch origin
git switch -c codex/evals-codex-clean-room origin/codex/evals-harness
git status --short --branch
```

Expected: branch is `codex/evals-codex-clean-room` and the worktree is clean.

- [ ] **Step 2: write the failing tests**

Create `tests/test_eval_codex_adapter.py`:

```python
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CodexCleanRoomAdapterTests(unittest.TestCase):
    def test_prepare_codex_home_installs_only_declared_skill_and_mcp_config(self) -> None:
        from evals.runner.codex_adapter import prepare_codex_home

        with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
            codex_home = Path(tmp) / "coding-agent-config"

            prepare_codex_home(
                repo_root=ROOT,
                codex_home=codex_home,
                skills=("cities2-knowledge",),
            )

            self.assertTrue((codex_home / "skills" / "cities2-knowledge" / "SKILL.md").is_file())
            self.assertFalse((codex_home / "skills" / "cities2-mod-debugging").exists())
            self.assertFalse((codex_home / "skills" / "superpowers").exists())
            config = (codex_home / "config.toml").read_text(encoding="utf-8")
            self.assertIn("[mcp_servers.cities2-mcp]", config)
            self.assertIn("cities2_mcp.mcp_server", config)

    def test_no_skill_condition_has_empty_skill_directory(self) -> None:
        from evals.runner.codex_adapter import prepare_codex_home

        with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
            codex_home = Path(tmp) / "coding-agent-config"

            prepare_codex_home(repo_root=ROOT, codex_home=codex_home, skills=())

            self.assertEqual(list((codex_home / "skills").iterdir()), [])

    def test_minimal_codex_env_uses_generated_home_without_user_profile(self) -> None:
        from evals.runner.codex_adapter import minimal_codex_env

        with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
            codex_home = Path(tmp) / "coding-agent-config"
            env = minimal_codex_env(codex_home=codex_home, repo_root=ROOT, include_auth=False)

            self.assertEqual(env["CODEX_HOME"], str(codex_home))
            self.assertEqual(env["PYTHONPATH"], str(ROOT))
            self.assertIn("PATH", env)
            self.assertNotIn("USERPROFILE", env)
            self.assertNotIn("HOME", env)
            self.assertNotIn("OPENAI_API_KEY", env)

    def test_minimal_codex_env_can_forward_auth_without_printing_it(self) -> None:
        from evals.runner.codex_adapter import minimal_codex_env

        with tempfile.TemporaryDirectory(prefix="cities2-eval-codex-") as tmp:
            codex_home = Path(tmp) / "coding-agent-config"
            old_value = os.environ.get("OPENAI_API_KEY")
            os.environ["OPENAI_API_KEY"] = "unit-test-secret"
            try:
                env = minimal_codex_env(codex_home=codex_home, repo_root=ROOT, include_auth=True)
            finally:
                if old_value is None:
                    os.environ.pop("OPENAI_API_KEY", None)
                else:
                    os.environ["OPENAI_API_KEY"] = old_value

            self.assertEqual(env["OPENAI_API_KEY"], "unit-test-secret")
```

- [ ] **Step 3: run the tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_eval_codex_adapter -v
```

Expected: failure because `evals.runner.codex_adapter` does not exist.

- [ ] **Step 4: implement the adapter**

Create `evals/runner/codex_adapter.py`:

```python
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


class CodexAdapterError(RuntimeError):
    """Raised when a Codex clean room cannot be prepared."""


def _copy_skill(repo_root: Path, codex_home: Path, skill_name: str) -> None:
    source = repo_root / "skills" / skill_name
    if not source.is_dir():
        raise CodexAdapterError(f"missing source skill: {skill_name}")
    shutil.copytree(source, codex_home / "skills" / skill_name)


def _write_mcp_config(repo_root: Path, codex_home: Path) -> None:
    config = "\n".join(
        [
            "[mcp_servers.cities2-mcp]",
            f'command = "{sys.executable}"',
            'args = ["-m", "cities2_mcp.mcp_server", "--workspace", "{workspace}"]'.format(
                workspace=repo_root
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
) -> None:
    codex_home.mkdir(parents=True, exist_ok=False)
    (codex_home / "skills").mkdir()
    for skill_name in skills:
        _copy_skill(repo_root, codex_home, skill_name)
    _write_mcp_config(repo_root.resolve(), codex_home)


def minimal_codex_env(
    *,
    codex_home: Path,
    repo_root: Path,
    include_auth: bool,
) -> dict[str, str]:
    env: dict[str, str] = {
        "CODEX_HOME": str(codex_home),
        "PYTHONPATH": str(repo_root),
    }
    for key in ("PATH", "PATHEXT", "COMSPEC", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"):
        value = os.environ.get(key)
        if value:
            env[key] = value
    if include_auth and os.environ.get("OPENAI_API_KEY"):
        env["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]
    return env


def seed_codex_auth(*, codex_home: Path, env: dict[str, str]) -> None:
    api_key = env.get("OPENAI_API_KEY")
    if not api_key:
        raise CodexAdapterError("OPENAI_API_KEY is required for live Codex evals")
    result = subprocess.run(
        ["codex", "login", "--with-api-key"],
        input=api_key,
        text=True,
        capture_output=True,
        env={**env, "CODEX_HOME": str(codex_home)},
    )
    if result.returncode != 0:
        raise CodexAdapterError(
            f"codex login failed with exit {result.returncode}: {result.stderr.strip()}"
        )


def build_codex_exec_command(
    *,
    codex_command: str,
    workdir: Path,
    prompt: str,
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
```

- [ ] **Step 5: run adapter tests**

Run:

```powershell
python -m unittest tests.test_eval_codex_adapter -v
```

Expected: `OK`.

- [ ] **Step 6: run the code-change test gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: `OK`.

- [ ] **Step 7: commit**

Run:

```powershell
git add evals/runner/codex_adapter.py tests/test_eval_codex_adapter.py
git commit -m "Add Codex eval clean-room setup"
```

Open a PR targeting `codex/evals-harness`. Merge only after review and the test
gate passes.

### Task 3: trace normalization

Branch: `codex/evals-trace-normalization`

**Files:**

- Create: `evals/runner/trace.py`
- Create: `tests/test_eval_trace.py`

- [ ] **Step 1: create the branch from the updated harness**

Run:

```powershell
git fetch origin
git switch -c codex/evals-trace-normalization origin/codex/evals-harness
git status --short --branch
```

Expected: branch is `codex/evals-trace-normalization` and the worktree is
clean.

- [ ] **Step 2: write the failing tests**

Create `tests/test_eval_trace.py`:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class EvalTraceTests(unittest.TestCase):
    def test_normalizes_codex_tool_events_and_transcript(self) -> None:
        from evals.runner.trace import normalize_codex_events

        with tempfile.TemporaryDirectory(prefix="cities2-eval-trace-") as tmp:
            root = Path(tmp)
            raw = root / "codex-events.jsonl"
            calls = root / "coding-agent-tool-calls.jsonl"
            transcript = root / "transcript.txt"
            raw.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "tool_call", "name": "source_status", "arguments": {}}),
                        json.dumps(
                            {
                                "type": "event",
                                "msg": {
                                    "type": "function_call",
                                    "name": "search",
                                    "arguments": {"query": "office demand jobs education"},
                                },
                            }
                        ),
                        json.dumps({"type": "agent_message", "message": "Office demand needs educated workers."}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            normalize_codex_events(raw, calls, transcript)

            tool_records = [json.loads(line) for line in calls.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([record["name"] for record in tool_records], ["source_status", "search"])
            self.assertIn("Office demand needs educated workers.", transcript.read_text(encoding="utf-8"))

    def test_ignores_non_json_lines(self) -> None:
        from evals.runner.trace import normalize_codex_events

        with tempfile.TemporaryDirectory(prefix="cities2-eval-trace-") as tmp:
            root = Path(tmp)
            raw = root / "codex-events.jsonl"
            calls = root / "coding-agent-tool-calls.jsonl"
            transcript = root / "transcript.txt"
            raw.write_text("not json\n", encoding="utf-8")

            normalize_codex_events(raw, calls, transcript)

            self.assertEqual(calls.read_text(encoding="utf-8"), "")
            self.assertEqual(transcript.read_text(encoding="utf-8"), "")
```

- [ ] **Step 3: run the tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_eval_trace -v
```

Expected: failure because `evals.runner.trace` does not exist.

- [ ] **Step 4: implement trace normalization**

Create `evals/runner/trace.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _iter_json_lines(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def _nested_event(event: dict[str, Any]) -> dict[str, Any]:
    nested = event.get("msg")
    if isinstance(nested, dict):
        return nested
    nested = event.get("item")
    if isinstance(nested, dict):
        return nested
    return event


def _tool_call(event: dict[str, Any]) -> dict[str, Any] | None:
    candidate = _nested_event(event)
    event_type = candidate.get("type")
    name = candidate.get("name") or candidate.get("tool_name")
    if event_type not in {"tool_call", "function_call"} or not isinstance(name, str):
        return None
    arguments = candidate.get("arguments", {})
    return {
        "name": name,
        "arguments": arguments,
        "raw_type": event_type,
    }


def _message_text(event: dict[str, Any]) -> str | None:
    candidate = _nested_event(event)
    for key in ("message", "text", "content"):
        value = candidate.get(key)
        if isinstance(value, str):
            return value
    return None


def normalize_codex_events(raw_events: Path, tool_calls: Path, transcript: Path) -> None:
    calls: list[dict[str, Any]] = []
    messages: list[str] = []
    for event in _iter_json_lines(raw_events):
        call = _tool_call(event)
        if call is not None:
            calls.append(call)
        text = _message_text(event)
        if text:
            messages.append(text)

    tool_calls.write_text(
        "".join(json.dumps(call, sort_keys=True) + "\n" for call in calls),
        encoding="utf-8",
    )
    transcript.write_text("\n\n".join(messages), encoding="utf-8")
```

- [ ] **Step 5: run trace tests**

Run:

```powershell
python -m unittest tests.test_eval_trace -v
```

Expected: `OK`.

- [ ] **Step 6: run the code-change test gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: `OK`.

- [ ] **Step 7: commit**

Run:

```powershell
git add evals/runner/trace.py tests/test_eval_trace.py
git commit -m "Normalize Codex eval traces"
```

Open a PR targeting `codex/evals-harness`. Merge only after review and the test
gate passes.

### Task 4: deterministic check helpers

Branch: `codex/evals-check-helpers`

**Files:**

- Create: `evals/runner/check_tool.py`
- Create: `evals/runner/checks.py`
- Create: `tests/test_eval_checks.py`

- [ ] **Step 1: create the branch from the updated harness**

Run:

```powershell
git fetch origin
git switch -c codex/evals-check-helpers origin/codex/evals-harness
git status --short --branch
```

Expected: branch is `codex/evals-check-helpers` and the worktree is clean.

- [ ] **Step 2: write the failing tests**

Create `tests/test_eval_checks.py`:

```python
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EvalCheckToolTests(unittest.TestCase):
    def test_tool_and_transcript_checks_pass_and_fail(self) -> None:
        from evals.runner.check_tool import run_check

        with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            (agent_home / "skills" / "cities2-knowledge").mkdir(parents=True)
            (run_dir / "coding-agent-tool-calls.jsonl").write_text(
                json.dumps({"name": "source_status", "arguments": {}}) + "\n",
                encoding="utf-8",
            )
            (run_dir / "transcript.txt").write_text(
                "Office demand grows with educated workers.\nSources: wiki.\n",
                encoding="utf-8",
            )

            passed = run_check(
                "tool-called",
                ["source_status"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-knowledge",
                phase="post",
            )
            failed = run_check(
                "not-tool-called",
                ["source_status"],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-knowledge",
                phase="post",
            )

            self.assertEqual(passed.status, "pass")
            self.assertEqual(failed.status, "fail")

    @unittest.skipUnless(shutil.which("bash"), "bash required for scenario checks")
    def test_run_checks_phase_collects_records_from_checks_sh(self) -> None:
        from evals.runner.checks import run_checks_phase

        with tempfile.TemporaryDirectory(prefix="cities2-eval-checks-") as tmp:
            run_dir = Path(tmp)
            workdir = run_dir / "coding-agent-workdir"
            agent_home = run_dir / "coding-agent-config"
            workdir.mkdir()
            agent_home.mkdir()
            checks = run_dir / "checks.sh"
            checks.write_text(
                "pre() {\n"
                "  python -m evals.runner.check_tool agent-home-contained\n"
                "}\n"
                "post() { :; }\n",
                encoding="utf-8",
            )

            records = run_checks_phase(
                checks,
                "pre",
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="no-skill",
                repo_root=ROOT,
            )

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].name, "agent-home-contained")
            self.assertEqual(records[0].status, "pass")
```

- [ ] **Step 3: run the tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_eval_checks -v
```

Expected: failure because `evals.runner.check_tool` and
`evals.runner.checks` do not exist.

- [ ] **Step 4: implement the deterministic check command**

Create `evals/runner/check_tool.py`:

```python
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from evals.runner.models import CheckRecord, CheckStatus, Phase


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _tool_names(run_dir: Path) -> list[str]:
    path = run_dir / "coding-agent-tool-calls.jsonl"
    names: list[str] = []
    if not path.exists():
        return names
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        name = data.get("name")
        if isinstance(name, str):
            names.append(name)
    return names


def _skill_dirs(agent_home: Path) -> list[str]:
    skills = agent_home / "skills"
    if not skills.is_dir():
        return []
    return sorted(path.name for path in skills.iterdir() if path.is_dir())


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
        passed = _is_relative_to(agent_home, run_dir)
        return _record(name, phase, "pass" if passed else "fail", f"agent_home={agent_home}")

    if name == "condition-skill-set":
        expected = {
            "no-skill": [],
            "with-cities2-knowledge": ["cities2-knowledge"],
        }.get(condition)
        actual = _skill_dirs(agent_home)
        status: CheckStatus = "pass" if expected == actual else "fail"
        return _record(name, phase, status, f"expected={expected} actual={actual}")

    if name == "skill-not-visible":
        needle = args[0]
        visible = [skill for skill in _skill_dirs(agent_home) if needle in skill]
        return _record(name, phase, "pass" if not visible else "fail", f"visible={visible}")

    if name == "git-branch":
        expected = args[0]
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=workdir,
            text=True,
            capture_output=True,
        )
        actual = result.stdout.strip()
        return _record(
            name,
            phase,
            "pass" if result.returncode == 0 and actual == expected else "fail",
            f"expected={expected} actual={actual}",
        )

    if name in {"skill-called", "tool-called"}:
        expected = args[0]
        names = _tool_names(run_dir)
        return _record(name, phase, "pass" if expected in names else "fail", f"tool_names={names}")

    if name == "skill-not-called":
        prefix = args[0]
        names = _tool_names(run_dir)
        called = [tool_name for tool_name in names if tool_name.startswith(prefix)]
        return _record(name, phase, "pass" if not called else "fail", f"matching_calls={called}")

    if name == "not-tool-called":
        expected = args[0]
        names = _tool_names(run_dir)
        return _record(name, phase, "pass" if expected not in names else "fail", f"tool_names={names}")

    if name == "transcript-contains":
        needle = args[0]
        transcript = run_dir / "transcript.txt"
        text = transcript.read_text(encoding="utf-8") if transcript.exists() else ""
        return _record(name, phase, "pass" if needle.lower() in text.lower() else "fail", f"needle={needle}")

    return _record(name, phase, "indeterminate", f"unknown check: {name}")


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    if not args:
        print("missing check name", file=sys.stderr)
        return 2
    phase = os.environ.get("EVAL_CHECK_PHASE", "post")
    if phase not in {"pre", "post"}:
        print(f"invalid EVAL_CHECK_PHASE: {phase}", file=sys.stderr)
        return 2
    record = run_check(
        args[0],
        args[1:],
        run_dir=Path(os.environ["EVAL_RUN_DIR"]),
        workdir=Path(os.environ["EVAL_WORKDIR"]),
        agent_home=Path(os.environ["EVAL_AGENT_HOME"]),
        condition=os.environ["EVAL_CONDITION"],
        phase=phase,
    )
    sink = os.environ.get("EVAL_RECORD_SINK")
    if sink:
        with Path(sink).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")
    print(json.dumps(record.to_dict(), sort_keys=True))
    return 0 if record.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: implement shell check execution**

Create `evals/runner/checks.py`:

```python
from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path

from evals.runner.models import CheckRecord, Phase


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
    env = dict(os.environ)
    env.update(
        {
            "EVAL_RUN_DIR": str(run_dir),
            "EVAL_WORKDIR": str(workdir),
            "EVAL_AGENT_HOME": str(agent_home),
            "EVAL_CONDITION": condition,
            "EVAL_CHECK_PHASE": phase,
            "EVAL_RECORD_SINK": str(sink),
            "PYTHONPATH": str(repo_root),
        }
    )
    command = f"source {shlex.quote(checks.as_posix())}; {phase}"
    result = subprocess.run(
        ["bash", "-lc", command],
        cwd=workdir,
        env=env,
        text=True,
        capture_output=True,
    )
    records = _read_records(sink)
    if result.returncode != 0 and not records:
        records.append(
            CheckRecord(
                name=f"{phase}-checks",
                phase=phase,
                status="fail",
                detail=result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}",
            )
        )
    return records


def _read_records(path: Path) -> list[CheckRecord]:
    records: list[CheckRecord] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        records.append(
            CheckRecord(
                name=data["name"],
                phase=data["phase"],
                status=data["status"],
                detail=data["detail"],
            )
        )
    return records
```

- [ ] **Step 6: run check helper tests**

Run:

```powershell
python -m unittest tests.test_eval_checks -v
```

Expected: `OK`. The shell hook test is skipped only when `bash` is not
available.

- [ ] **Step 7: run the code-change test gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: `OK`.

- [ ] **Step 8: commit**

Run:

```powershell
git add evals/runner/check_tool.py evals/runner/checks.py tests/test_eval_checks.py
git commit -m "Add eval check helpers"
```

Open a PR targeting `codex/evals-harness`. Merge only after review and the test
gate passes.

### Task 5: runner CLI and fake Codex orchestration

Branch: `codex/evals-runner-cli`

**Files:**

- Create: `evals/runner/__main__.py`
- Create: `tests/test_eval_runner_cli.py`

- [ ] **Step 1: create the branch from the updated harness**

Run:

```powershell
git fetch origin
git switch -c codex/evals-runner-cli origin/codex/evals-harness
git status --short --branch
```

Expected: branch is `codex/evals-runner-cli` and the worktree is clean.

- [ ] **Step 2: write the failing fake-Codex test**

Create `tests/test_eval_runner_cli.py`:

```python
from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "evals" / "scenarios" / "spike" / "cities2-knowledge-office-demand"


class EvalRunnerCliTests(unittest.TestCase):
    def test_runner_writes_verdict_with_fake_codex(self) -> None:
        from evals.runner.__main__ import run_eval

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            fake_codex = root / "fake_codex.py"
            fake_codex.write_text(
                textwrap.dedent(
                    """\
                    from __future__ import annotations

                    print('{"type":"tool_call","name":"cities2-knowledge","arguments":{}}')
                    print('{"type":"tool_call","name":"source_status","arguments":{}}')
                    print('{"type":"tool_call","name":"search","arguments":{"query":"office demand jobs education"}}')
                    print('{"type":"agent_message","message":"Office demand grows with educated workers. Source note: wiki."}')
                    """
                ),
                encoding="utf-8",
            )

            paths = run_eval(
                scenario_path=SCENARIO,
                condition="with-cities2-knowledge",
                repo_root=ROOT,
                results_root=root / "results",
                codex_command=sys.executable,
                codex_args_prefix=(str(fake_codex),),
                live_auth=False,
                trial=1,
            )

            verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))

            self.assertEqual(verdict["metadata"]["scenario_id"], "cities2-knowledge-office-demand")
            self.assertEqual(verdict["metadata"]["condition_id"], "with-cities2-knowledge")
            self.assertEqual(verdict["final"], "pass")
            self.assertTrue(paths.raw_events.exists())
            self.assertTrue(paths.tool_calls.exists())
            self.assertTrue(paths.transcript.exists())
```

- [ ] **Step 3: run the test and verify it fails**

Run:

```powershell
python -m unittest tests.test_eval_runner_cli -v
```

Expected: failure because `evals.runner.__main__` does not exist.

- [ ] **Step 4: implement the runner entrypoint**

Create `evals/runner/__main__.py`:

```python
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

from evals.runner.checks import run_checks_phase
from evals.runner.codex_adapter import (
    build_codex_exec_command,
    minimal_codex_env,
    prepare_codex_home,
    seed_codex_auth,
)
from evals.runner.models import CheckRecord, RunMetadata, RunPaths, Verdict
from evals.runner.scenario import load_scenario
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
    marker = "```text\n"
    start = text.find(marker)
    if start == -1:
        raise ValueError("story.md must contain a fenced text prompt")
    start += len(marker)
    end = text.find("\n```", start)
    if end == -1:
        raise ValueError("story.md prompt fence is not closed")
    return text[start:end].strip()


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
        data = (repo_root / "skills" / skill / "SKILL.md").read_bytes()
        checksums[skill] = "sha256:" + hashlib.sha256(data).hexdigest()
    return checksums


def _new_run_dir(results_root: Path, scenario_id: str, condition: str, trial: int) -> Path:
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = results_root / f"{scenario_id}-{condition}-trial-{trial}-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _run_setup(setup: Path, workdir: Path) -> None:
    result = subprocess.run(
        ["bash", setup.as_posix()],
        cwd=workdir,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def _metadata(
    *,
    scenario_id: str,
    condition: str,
    trial: int,
    backend_executable: str,
    repo_root: Path,
    skills: tuple[str, ...],
) -> RunMetadata:
    return RunMetadata(
        scenario_id=scenario_id,
        scenario_version="1",
        condition_id=condition,
        trial=trial,
        backend_name="codex",
        backend_executable=backend_executable,
        repo_commit=_repo_commit(repo_root),
        runner_version=RUNNER_VERSION,
        run_started_at=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        skill_checksums=_skill_checksums(repo_root, skills),
    )


def _final_status(pre_records: list[CheckRecord], all_records: list[CheckRecord]) -> tuple[str, str]:
    if any(record.status != "pass" for record in pre_records):
        return "indeterminate", "one or more pre-checks failed"
    if all(record.status == "pass" for record in all_records):
        return "pass", "all checks passed"
    return "fail", "one or more post-checks failed"


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
    paths = RunPaths.from_run_dir(_new_run_dir(results_root, scenario.id, condition, trial))
    paths.workdir.mkdir()
    prepare_codex_home(repo_root=repo_root, codex_home=paths.agent_home, skills=skills)
    _run_setup(scenario.setup, paths.workdir)

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
        codex_home=paths.agent_home,
        repo_root=repo_root,
        include_auth=live_auth,
    )
    if live_auth:
        seed_codex_auth(codex_home=paths.agent_home, env=env)

    if all(record.status == "pass" for record in pre_records):
        command = build_codex_exec_command(
            codex_command=codex_command,
            workdir=paths.workdir,
            prompt=_prompt_from_story(scenario.story),
        )
        command = [command[0], *codex_args_prefix, *command[1:]]
        with paths.raw_events.open("w", encoding="utf-8") as output:
            result = subprocess.run(
                command,
                cwd=repo_root,
                env=env,
                text=True,
                stdout=output,
                stderr=subprocess.PIPE,
            )
        if result.returncode != 0:
            with paths.raw_events.open("a", encoding="utf-8") as output:
                output.write(result.stderr)
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
    checks = pre_records + post_records
    final, reason = _final_status(pre_records, checks)
    verdict = Verdict(
        metadata=_metadata(
            scenario_id=scenario.id,
            condition=condition,
            trial=trial,
            backend_executable=codex_command,
            repo_root=repo_root,
            skills=skills,
        ),
        final=final,
        final_reason=reason,
        checks=checks,
        trace_path=paths.tool_calls.name,
        transcript_path=paths.transcript.name,
    )
    paths.verdict.write_text(json.dumps(verdict.to_dict(), indent=2) + "\n", encoding="utf-8")
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a Cities2-MCP skill eval")
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--condition", choices=("no-skill", "with-cities2-knowledge"), required=True)
    parser.add_argument("--results-root", type=Path, default=Path("evals/results"))
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--no-live-auth", action="store_true")
    parser.add_argument("--trial", type=int, default=1)
    args = parser.parse_args(argv)
    paths = run_eval(
        scenario_path=args.scenario,
        condition=args.condition,
        repo_root=Path.cwd(),
        results_root=args.results_root,
        codex_command=args.codex_command,
        live_auth=not args.no_live_auth,
        trial=args.trial,
    )
    print(paths.verdict)
    verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))
    return {"pass": 0, "fail": 1, "indeterminate": 2}[verdict["final"]]


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: run CLI tests**

Run:

```powershell
python -m unittest tests.test_eval_runner_cli -v
```

Expected: `OK`.

- [ ] **Step 6: run all eval tests**

Run:

```powershell
python -m unittest tests.test_eval_run_models tests.test_eval_codex_adapter tests.test_eval_trace tests.test_eval_checks tests.test_eval_runner_cli tests.test_eval_scenario_loader tests.test_eval_scenario_layout -v
```

Expected: `OK`.

- [ ] **Step 7: run the code-change test gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: `OK`.

- [ ] **Step 8: commit**

Run:

```powershell
git add evals/runner/__main__.py tests/test_eval_runner_cli.py
git commit -m "Add Codex eval runner CLI"
```

Open a PR targeting `codex/evals-harness`. Merge only after review and the test
gate passes.

### Task 6: offline smoke documentation and client-matrix decision note

Branch: `codex/evals-live-smoke-note`

**Files:**

- Modify: `evals/README.md`
- Create:
  `docs/superpowers/evaluations/2026-06-04-cities2-knowledge-runner-spike.md`
- Create: `tests/test_eval_docs.py`

- [ ] **Step 1: create the branch from the updated harness**

Run:

```powershell
git fetch origin
git switch -c codex/evals-live-smoke-note origin/codex/evals-harness
git status --short --branch
```

Expected: branch is `codex/evals-live-smoke-note` and the worktree is clean.

- [ ] **Step 2: write failing documentation guardrail tests**

Create `tests/test_eval_docs.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATION = (
    ROOT
    / "docs"
    / "superpowers"
    / "evaluations"
    / "2026-06-04-cities2-knowledge-runner-spike.md"
)


class EvalDocsTests(unittest.TestCase):
    def test_docs_explain_offline_smoke_without_local_paths_or_secrets(self) -> None:
        readme = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        evaluation = EVALUATION.read_text(encoding="utf-8")

        for text in (readme, evaluation):
            self.assertIn("evals/results/", text)
            self.assertIn("gitignored", text.lower())
            self.assertNotIn("C:" + "\\" + "Users", text)
            self.assertNotIn("\\" + "Users" + "\\", text)
            self.assertNotIn("/" + "Users" + "/", text)
            self.assertNotIn("OPENAI_API_KEY" + "=", text)
            self.assertNotIn("sk-", text)

    def test_evaluation_note_records_decision_point(self) -> None:
        evaluation = EVALUATION.read_text(encoding="utf-8")

        self.assertIn("Reuse Quorum directly", evaluation)
        self.assertIn("Keep the local compatible subset", evaluation)

    def test_evaluation_note_records_client_matrix(self) -> None:
        evaluation = EVALUATION.read_text(encoding="utf-8")

        self.assertIn("Required offline smoke protocol", evaluation)
        self.assertIn("Optional real-client smoke direction", evaluation)
        self.assertIn("`codex`", evaluation)
        self.assertIn("`claude`", evaluation)
        self.assertIn("`agy`", evaluation)
```

- [ ] **Step 3: run the tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_eval_docs -v
```

Expected: failure because the evaluation note does not exist.

- [ ] **Step 4: update the eval README**

Replace `evals/README.md` with:

```markdown
# Cities2-MCP evals

This directory contains Quorum-compatible skill eval scenarios and the local
runner spike for Cities2-MCP.

Scenarios use this contract:

```text
story.md
setup.sh
checks.sh
```

Generated run artifacts belong under `evals/results/`, which is gitignored.
Raw traces, transcripts, generated agent homes, and workdirs must not be
committed.

The first spike scenario is:

```text
evals/scenarios/spike/cities2-knowledge-office-demand/
```

Run the required offline harness smoke:

```powershell
python -m unittest tests.test_eval_runner_cli -v
```

This uses a fake Codex process to validate clean-room setup, trace capture,
checks, verdict writing, and `evals/results/` handling without live model auth.

The runner CLI invokes the real Codex client and is reserved for optional
maintainer-local smoke runs:

```powershell
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition with-cities2-knowledge --trial 1
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition no-skill --trial 1
```

The runner creates a fresh `CODEX_HOME` inside each run directory and installs
only the skill files declared by the condition. Future client adapters should
preserve the same isolation contract for `codex`, `claude`, and `agy`.
```

- [ ] **Step 5: add the evaluation note**

Create
`docs/superpowers/evaluations/2026-06-04-cities2-knowledge-runner-spike.md`:

```markdown
# Cities2 knowledge runner spike

## Purpose

This evaluation records the first runnable harness spike for the Cities2-MCP
skill eval suite. It tests whether the runner can isolate Codex, install only
the declared `cities2-knowledge` skill, connect the Cities2-MCP server, capture
trace artifacts, and write deterministic verdicts without requiring live model
auth.

This is a harness-validation result. It is not the later behavioral baseline
for `cities2-mod-debugging`.

## Scenario

Scenario path:
`evals/scenarios/spike/cities2-knowledge-office-demand/`

The scenario asks:

```text
How do I grow office demand?
```

## Conditions

- `no-skill`: no skills installed in the clean-room `CODEX_HOME`.
- `with-cities2-knowledge`: only `cities2-knowledge` plus the Cities2-MCP MCP
  server config installed in the clean-room `CODEX_HOME`.

## Result storage

Generated run artifacts are written under `evals/results/`, which is
gitignored. Do not commit raw traces, full transcripts, generated agent homes,
or generated workdirs.

## Required offline smoke protocol

Run the fake-Codex harness smoke:

```powershell
python -m unittest tests.test_eval_runner_cli -v
```

This is the required Task 6 gate. It validates runner orchestration with a fake
client process, writes generated artifacts to a temporary results root, and
validates the same result-handling path used by gitignored `evals/results/`. It
does not claim behavioral model quality.

## Optional real-client smoke direction

When higher-order behavior needs checking, test the supported clients rather
than generic provider lanes:

- `codex`: optional maintainer-local smoke through the Codex CLI. Future OAuth
  support should use an eval-only `CODEX_HOME`, file-based credential storage,
  a disposable workdir, explicit sandbox settings, and only the skill/MCP config
  declared by the condition.
- `claude`: future adapter with a fresh client home/profile and only the
  packaged Cities2-MCP skill payload needed by the condition.
- `agy`: future Antigravity adapter with a fresh plugin/profile boundary and
  the same condition-scoped skill payload.

Real-client smoke is optional and local. It is not a CI gate, not a contributor
gate, and not required for this harness-validation PR.

The current runner CLI invokes real Codex and may be used only for optional
maintainer-local smoke after auth and isolation requirements are satisfied:

```powershell
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition with-cities2-knowledge --trial 1
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition no-skill --trial 1
```

Inspect each printed `verdict.json`. The runner may exit with `0`, `1`, or `2`;
the verdict file is the source of truth for whether the run passed, failed, or
was indeterminate.

## Decision point

After the offline smoke passes, choose one:

- Reuse Quorum directly if Windows execution, Codex clean-room isolation, skill
  installation, trace capture, and check execution need only light adaptation.
- Keep the local compatible subset if Quorum adds friction without improving
  the scenario contract or determinism.

Record the decision in the smoke results section using only curated verdict
status, repo-relative paths, and short rationale.
```

- [ ] **Step 6: run documentation tests**

Run:

```powershell
python -m unittest tests.test_eval_docs -v
```

Expected: `OK`.

- [ ] **Step 7: run the required offline harness smoke**

Run:

```powershell
python -m unittest tests.test_eval_runner_cli -v
```

Expected: `OK`. This is the required smoke gate for Task 6.

- [ ] **Step 8: append curated smoke results**

Append a `## Smoke results` section to
`docs/superpowers/evaluations/2026-06-04-cities2-knowledge-runner-spike.md`.
The section must contain:

- One bullet for the required offline fake-Codex smoke with the test command and
  result status.
- The sentence `Raw run artifacts remain gitignored.`
- A `Decision:` paragraph choosing either `Reuse Quorum directly` or
  `Keep the local compatible subset`, with one short rationale sentence.
- A short note that real-client smoke for `codex`, `claude`, and `agy` is a
  later optional adapter matrix, not this PR's gate.

Do not paste raw trace lines, generated local paths, or full transcripts into
this note.

- [ ] **Step 9: run hygiene checks**

Run:

```powershell
git status --short
git diff --check
$privacyPattern = ("C:" + "\\" + "Users") + "|" + ("\\" + "Users" + "\\") + "|" + "OPENAI_API_KEY[=]|sk-[A-Za-z0-9]{8,}"
rg -n $privacyPattern docs evals tests .gitignore
```

Expected: `git diff --check` passes. The `rg` command reports no tracked local
paths, printed secrets, or token-like strings in the files changed by this
branch.

- [ ] **Step 10: run the code-change test gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: `OK`.

- [ ] **Step 11: commit**

Run:

```powershell
git add evals/README.md docs/superpowers/evaluations/2026-06-04-cities2-knowledge-runner-spike.md tests/test_eval_docs.py docs/superpowers/plans/2026-06-01-skill-eval-runner-spike.md
git commit -m "Document cities2 knowledge eval smoke"
```

Open a PR targeting `codex/evals-harness`. Merge only after review, the offline
smoke note is complete, and the test gate passes.

## Final harness gate

After Task 6 merges into `codex/evals-harness`, run:

```powershell
git fetch origin
git switch codex/evals-harness
git pull --ff-only
python -m unittest discover -s tests -v
python -m cities2_mcp.plugin_packages check
git status --short --branch
```

Expected:

- The unittest suite passes.
- Plugin package check passes because no plugin payload drift was introduced.
- `git status --short --branch` shows a clean `codex/evals-harness` worktree.
- `evals/results/` contains only gitignored generated run directories.

Do not merge `codex/evals-harness` to `main` until the maintainer approves the
recorded smoke results and the Quorum reuse decision.

## Self-review notes

- Spec coverage: the plan covers the top-level `evals/` home, Quorum-compatible
  scenario contract, `cities2-knowledge` first spike, clean-room Codex home,
  no-skill and with-skill conditions, trace capture, deterministic checks,
  gitignored raw artifacts, and a recorded reuse/local-subset decision.
- Deferred by spec: the six-run `cities2-mod-debugging` behavioral baseline is
  intentionally not implemented here. It starts only after this runner spike is
  reviewed.
- Privacy scan: branch names, commit messages, docs, tests, and code snippets
  use repo-relative paths and contain no personal local paths.
