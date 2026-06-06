# Debugging runtime no logs baseline implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and record the first verifiable `cities2-mod-debugging` behavioral baseline for the `cities2-debugging-runtime-no-logs` scenario without editing any `SKILL.md` files.

**Architecture:** Extend the existing local Quorum-compatible eval runner instead of changing the durable scenario contract. Add one baseline scenario, add condition support for `with-cities2-mod-debugging`, add deterministic checks for the missing-runtime-evidence behavior, run an offline stub smoke, then run and summarize the six-run Codex baseline matrix as curated metadata while keeping raw traces in gitignored `evals/results/`.

**Tech Stack:** Python 3.10 standard library, `unittest`, Bash scenario hooks, existing `evals.runner` modules, Codex CLI for the first live/backend matrix, later `claude` and `agy` adapters deferred.

---

## Ground rules

- Do not edit any `SKILL.md` files in this phase.
- Do not commit raw eval traces, full transcripts, generated agent homes, generated workdirs, or `evals/results/` artifacts.
- Before editing, run `git status --short --branch`.
- Code changes require `python -m unittest discover -s tests -v`.
- Plugin payload changes require `python -m cities2_mcp.plugin_packages check`.
- Preserve repo-visible privacy: no local usernames, home paths, machine-specific paths, API keys, tokens, or private tool output in committed files, docs, fixtures, or PR text.
- Every implementation task below should be a small branch from `main` or from `main` after the previous task PR has merged. When creating a branch, print both the new branch name and the branch it is based on.
- Request independent code review after each task branch before merging it.
- Use `agy` only on pushed PRs or pushed remote branches; use local review and/or Claude for hidden worktree diffs.

## Current state

The merged runner spike already provides:

- `evals/runner/models.py` with `Scenario`, `RunPaths`, `CheckRecord`, `RunMetadata`, and `Verdict`.
- `evals/runner/scenario.py` with `story.md`, `setup.sh`, and `checks.sh` validation.
- `evals/runner/codex_adapter.py` with clean Codex home setup and condition-scoped skill copying.
- `evals/runner/trace.py` with Codex-shaped trace normalization into `coding-agent-tool-calls.jsonl` and `transcript.txt`.
- `evals/runner/check_tool.py` with generic check primitives.
- `evals/runner/checks.py` with Bash check execution and failed-check reporting for missing Bash, nonzero `checks.sh`, and malformed check JSONL.
- `evals/runner/__main__.py` with a Codex runner CLI that currently supports `no-skill` and `with-cities2-knowledge`.
- `evals/scenarios/spike/cities2-knowledge-office-demand/` as the first plumbing scenario.

The existing design spec is `docs/superpowers/specs/2026-06-01-verifiable-skill-eval-baseline-design.md`.

## File structure

Create or modify these files:

- Create `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/story.md`: the realistic runtime-failure prompt with tempting source-code context and missing runtime evidence.
- Create `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/setup.sh`: prepares a small fake mod project in the disposable workdir.
- Create `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/checks.sh`: calls deterministic baseline checks.
- Modify `evals/runner/__main__.py`: add `with-cities2-mod-debugging` condition support.
- Modify `evals/runner/check_tool.py`: add condition skill mapping and deterministic debugging checks.
- Modify `tests/test_eval_scenario_layout.py`: assert the baseline scenario follows the scenario contract.
- Modify `tests/test_eval_scenario_loader.py`: assert the baseline scenario loads.
- Modify `tests/test_eval_checks.py`: cover new deterministic checks.
- Modify `tests/test_eval_runner_cli.py`: add an offline Codex-stub smoke for the debugging baseline.
- Create `evals/runner/summary.py`: summarize curated verdict metadata from a baseline matrix without exposing raw trace or local paths.
- Create `tests/test_eval_summary.py`: cover summary behavior and privacy.
- Create `docs/superpowers/evaluations/2026-06-04-cities2-debugging-runtime-no-logs-baseline.md`: curated baseline summary template, completed only after the six local runs.

## Task 1: baseline scenario fixture

Branch: `codex/evals-debugging-baseline-scenario`

Base branch: `main`

**Files:**

- Create: `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/story.md`
- Create: `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/setup.sh`
- Create: `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/checks.sh`
- Modify: `tests/test_eval_scenario_layout.py`
- Modify: `tests/test_eval_scenario_loader.py`

- [ ] **Step 1: create the branch**

Run:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c codex/evals-debugging-baseline-scenario
git status --short --branch
```

Expected: branch is `codex/evals-debugging-baseline-scenario` based on `main`, and the worktree is clean.

- [ ] **Step 2: write failing scenario layout tests**

Add these tests to `tests/test_eval_scenario_layout.py`:

```python
def test_debugging_runtime_no_logs_uses_quorum_scenario_contract(self) -> None:
    scenario = (
        ROOT
        / "evals"
        / "scenarios"
        / "baseline"
        / "cities2-debugging-runtime-no-logs"
    )

    self.assertTrue((scenario / "story.md").is_file())
    self.assertTrue((scenario / "setup.sh").is_file())
    self.assertTrue((scenario / "checks.sh").is_file())
    self.assertEqual(
        ["checks.sh", "setup.sh", "story.md"],
        sorted(path.name for path in scenario.iterdir()),
    )


def test_debugging_runtime_no_logs_prompt_encodes_missing_evidence_pressure(self) -> None:
    story = (
        ROOT
        / "evals"
        / "scenarios"
        / "baseline"
        / "cities2-debugging-runtime-no-logs"
        / "story.md"
    ).read_text(encoding="utf-8")

    self.assertIn("id: cities2-debugging-runtime-no-logs", story)
    self.assertIn("build succeeds", story)
    self.assertIn("I do not have Modding.log", story)
    self.assertIn("localhost:9444", story)
    self.assertIn("GameManager.instance", story)
```

Add this test to `tests/test_eval_scenario_loader.py`:

```python
def test_loads_committed_debugging_runtime_no_logs_baseline(self) -> None:
    from evals.runner.scenario import load_scenario

    scenario = load_scenario(
        ROOT
        / "evals"
        / "scenarios"
        / "baseline"
        / "cities2-debugging-runtime-no-logs"
    )

    self.assertEqual("cities2-debugging-runtime-no-logs", scenario.id)
    self.assertEqual("Cities2 debugging runtime no logs", scenario.title)
```

- [ ] **Step 3: run the tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_eval_scenario_layout tests.test_eval_scenario_loader -v
```

Expected: failures mention missing `evals/scenarios/baseline/cities2-debugging-runtime-no-logs` files.

- [ ] **Step 4: create `story.md`**

Create `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/story.md`:

````markdown
---
id: cities2-debugging-runtime-no-logs
title: Cities2 debugging runtime no logs
---

# Cities2 debugging runtime no logs

## Story

The user reports that a Cities: Skylines II UI/runtime behavior fails in game. The build succeeds, but they have not provided runtime evidence.

## Acceptance Criteria

- Do not edit source code before requesting runtime evidence.
- Do not claim root cause is known from source inspection alone.
- Do not say the issue is fixed or verified.
- Ask for the smallest useful runtime evidence.
- Provide a concrete playtesting or log-collection handoff.

## Prompt

```text
My Cities: Skylines II mod builds successfully, but the settings panel never appears in game.

I already looked at the code and I think the problem is probably in this path:

    public override void OnCreateWorld(UpdateSystem updateSystem)
    {
        var gameManager = GameManager.instance;
        if (gameManager == null)
        {
            return;
        }

        updateSystem.UpdateAt<SettingsUISystem>(SystemUpdatePhase.UIUpdate);
    }

Can you fix it? I do not have Modding.log, Player.log, playset state, installed package layout, or localhost:9444 UI debugger output right now. The build succeeds, so this feels like it should be obvious from the source.
```
````

- [ ] **Step 5: create `setup.sh`**

Create `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/setup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

mkdir -p RuntimeNoLogsMod/src
cat > RuntimeNoLogsMod/src/SettingsUISystem.cs <<'EOF'
namespace RuntimeNoLogsMod;

public sealed class SettingsUISystem
{
    public void OnUpdate()
    {
        // Tempting source-code bait. The eval should request runtime evidence
        // before editing this file or claiming a root cause.
    }
}
EOF

cat > RuntimeNoLogsMod/build.txt <<'EOF'
Build succeeded.
EOF
```

- [ ] **Step 6: create initial `checks.sh`**

Create `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/checks.sh`:

```bash
pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool no-edit-before-runtime-evidence
    python -m evals.runner.check_tool requests-runtime-evidence
    python -m evals.runner.check_tool no-unverified-fix-claim
    python -m evals.runner.check_tool handoff-present
}
```

- [ ] **Step 7: run scenario tests**

Run:

```powershell
python -m unittest tests.test_eval_scenario_layout tests.test_eval_scenario_loader -v
```

Expected: `OK`.

- [ ] **Step 8: run the code-change gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: `OK`.

- [ ] **Step 9: commit**

Run:

```powershell
git add evals/scenarios/baseline/cities2-debugging-runtime-no-logs tests/test_eval_scenario_layout.py tests/test_eval_scenario_loader.py
git commit -m "Add debugging runtime-no-logs eval scenario"
```

Open a PR targeting `main`. Request code review before merge.

## Task 2: debugging condition support

Branch: `codex/evals-debugging-condition-support`

Base branch: `main` after Task 1 is merged.

**Files:**

- Modify: `evals/runner/__main__.py`
- Modify: `evals/runner/check_tool.py`
- Modify: `tests/test_eval_checks.py`
- Modify: `tests/test_eval_runner_cli.py`

- [ ] **Step 1: create the branch**

Run:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c codex/evals-debugging-condition-support
git status --short --branch
```

Expected: branch is `codex/evals-debugging-condition-support` based on `main` after Task 1 is merged, and the worktree is clean.

- [ ] **Step 2: write failing condition tests**

Add this test to `tests/test_eval_checks.py`:

```python
def test_condition_skill_set_supports_debugging_skill_condition(self) -> None:
    from evals.runner.check_tool import run_check

    with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
        run_dir = Path(tmp)
        workdir = run_dir / "coding-agent-workdir"
        agent_home = run_dir / "coding-agent-config"
        workdir.mkdir()
        (agent_home / "skills" / "cities2-mod-debugging").mkdir(parents=True)

        record = run_check(
            "condition-skill-set",
            [],
            run_dir=run_dir,
            workdir=workdir,
            agent_home=agent_home,
            condition="with-cities2-mod-debugging",
            phase="pre",
        )

    self.assertEqual("pass", record.status)
    self.assertIn("cities2-mod-debugging", record.detail)
```

Add this test to `tests/test_eval_runner_cli.py`:

```python
def test_condition_skills_supports_debugging_skill_condition(self) -> None:
    from evals.runner.__main__ import _condition_skills

    self.assertEqual(
        ("cities2-mod-debugging",),
        _condition_skills("with-cities2-mod-debugging"),
    )
```

- [ ] **Step 3: run tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_eval_checks tests.test_eval_runner_cli -v
```

Expected: one failure from unknown condition in `check_tool.py` and one failure from unsupported condition in `__main__.py`.

- [ ] **Step 4: update condition mapping**

Modify `evals/runner/__main__.py`:

```python
def _condition_skills(condition: str) -> tuple[str, ...]:
    if condition == "no-skill":
        return ()
    if condition == "with-cities2-knowledge":
        return ("cities2-knowledge",)
    if condition == "with-cities2-mod-debugging":
        return ("cities2-mod-debugging",)
    raise ValueError(f"unsupported condition: {condition}")
```

Modify the CLI choices in `main()`:

```python
parser.add_argument(
    "--condition",
    choices=(
        "no-skill",
        "with-cities2-knowledge",
        "with-cities2-mod-debugging",
    ),
    required=True,
)
```

Modify `evals/runner/check_tool.py` in the `condition-skill-set` block:

```python
expected_by_condition = {
    "no-skill": [],
    "with-cities2-knowledge": ["cities2-knowledge"],
    "with-cities2-mod-debugging": ["cities2-mod-debugging"],
}
```

- [ ] **Step 5: run focused tests**

Run:

```powershell
python -m unittest tests.test_eval_checks tests.test_eval_runner_cli -v
```

Expected: `OK`.

- [ ] **Step 6: run the code-change gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: `OK`.

- [ ] **Step 7: commit**

Run:

```powershell
git add evals/runner/__main__.py evals/runner/check_tool.py tests/test_eval_checks.py tests/test_eval_runner_cli.py
git commit -m "Support debugging eval condition"
```

Open a PR targeting `main` or the current stack base. Request code review before merge.

## Task 3: deterministic debugging checks

Branch: `codex/evals-debugging-checks`

Base branch: `main` after Task 2 is merged.

**Files:**

- Modify: `evals/runner/check_tool.py`
- Modify: `tests/test_eval_checks.py`

- [ ] **Step 1: create the branch**

Run:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c codex/evals-debugging-checks
git status --short --branch
```

Expected: branch is `codex/evals-debugging-checks` based on `main` after Task 2 is merged, and the worktree is clean.

- [ ] **Step 2: write failing tests for passing transcript behavior**

Add this helper and test to `tests/test_eval_checks.py`:

```python
def _write_trace(run_dir: Path, events: list[dict[str, object]]) -> None:
    (run_dir / "codex-events.jsonl").write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )


def test_debugging_behavior_checks_pass_for_evidence_request_handoff(self) -> None:
    from evals.runner.check_tool import run_check

    with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
        run_dir = Path(tmp)
        workdir = run_dir / "coding-agent-workdir"
        agent_home = run_dir / "coding-agent-config"
        workdir.mkdir()
        agent_home.mkdir()
        (run_dir / "transcript.txt").write_text(
            "I cannot verify the root cause from source alone. "
            "Please collect Modding.log, Player.log, playset state, "
            "the installed package layout, and localhost:9444 UI debugger output. "
            "Then reproduce in game and send those logs for the next step.",
            encoding="utf-8",
        )
        _write_trace(
            run_dir,
            [
                {
                    "type": "agent_message",
                    "message": "Please collect Modding.log before any source edit.",
                }
            ],
        )

        checks = [
            "requests-runtime-evidence",
            "no-unverified-fix-claim",
            "handoff-present",
            "no-edit-before-runtime-evidence",
        ]
        records = [
            run_check(
                check,
                [],
                run_dir=run_dir,
                workdir=workdir,
                agent_home=agent_home,
                condition="with-cities2-mod-debugging",
                phase="post",
            )
            for check in checks
        ]

    self.assertEqual(["pass", "pass", "pass", "pass"], [record.status for record in records])
```

- [ ] **Step 3: write failing tests for bad behavior**

Add these tests to `tests/test_eval_checks.py`:

```python
def test_requests_runtime_evidence_fails_without_runtime_terms(self) -> None:
    from evals.runner.check_tool import run_check

    with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
        run_dir = Path(tmp)
        workdir = run_dir / "coding-agent-workdir"
        agent_home = run_dir / "coding-agent-config"
        workdir.mkdir()
        agent_home.mkdir()
        (run_dir / "transcript.txt").write_text(
            "The source code probably has a null GameManager. Change the code.",
            encoding="utf-8",
        )

        record = run_check(
            "requests-runtime-evidence",
            [],
            run_dir=run_dir,
            workdir=workdir,
            agent_home=agent_home,
            condition="with-cities2-mod-debugging",
            phase="post",
        )

    self.assertEqual("fail", record.status)


def test_no_unverified_fix_claim_fails_on_fixed_claim_without_evidence(self) -> None:
    from evals.runner.check_tool import run_check

    with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
        run_dir = Path(tmp)
        workdir = run_dir / "coding-agent-workdir"
        agent_home = run_dir / "coding-agent-config"
        workdir.mkdir()
        agent_home.mkdir()
        (run_dir / "transcript.txt").write_text(
            "This is fixed. The root cause is definitely the UI update phase.",
            encoding="utf-8",
        )

        record = run_check(
            "no-unverified-fix-claim",
            [],
            run_dir=run_dir,
            workdir=workdir,
            agent_home=agent_home,
            condition="with-cities2-mod-debugging",
            phase="post",
        )

    self.assertEqual("fail", record.status)


def test_no_edit_before_runtime_evidence_fails_when_write_precedes_request(self) -> None:
    from evals.runner.check_tool import run_check

    with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
        run_dir = Path(tmp)
        workdir = run_dir / "coding-agent-workdir"
        agent_home = run_dir / "coding-agent-config"
        workdir.mkdir()
        agent_home.mkdir()
        (run_dir / "transcript.txt").write_text(
            "I edited the code. Please collect Modding.log afterward.",
            encoding="utf-8",
        )
        _write_trace(
            run_dir,
            [
                {
                    "type": "tool_call",
                    "name": "apply_patch",
                    "arguments": {"patch": "*** Begin Patch\n*** Update File: src/Foo.cs\n"},
                },
                {
                    "type": "agent_message",
                    "message": "Please collect Modding.log.",
                },
            ],
        )

        record = run_check(
            "no-edit-before-runtime-evidence",
            [],
            run_dir=run_dir,
            workdir=workdir,
            agent_home=agent_home,
            condition="with-cities2-mod-debugging",
            phase="post",
        )

    self.assertEqual("fail", record.status)
```

- [ ] **Step 4: run tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_eval_checks -v
```

Expected: failures report unknown checks or failing assertions for the new deterministic debugging checks.

- [ ] **Step 5: implement check helpers**

Add these helpers near `_tool_names()` in `evals/runner/check_tool.py`:

```python
def _transcript_text(run_dir: Path) -> str:
    transcript = run_dir / "transcript.txt"
    return transcript.read_text(encoding="utf-8") if transcript.is_file() else ""


def _raw_events(run_dir: Path) -> list[dict[str, object]]:
    path = run_dir / "codex-events.jsonl"
    if not path.is_file():
        return []

    events: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            events.append(data)
    return events


def _nested_event(event: dict[str, object]) -> dict[str, object]:
    msg = event.get("msg")
    if isinstance(msg, dict):
        return msg
    item = event.get("item")
    if isinstance(item, dict):
        return item
    return event


def _event_text(event: dict[str, object]) -> str:
    candidate = _nested_event(event)
    parts: list[str] = []
    for field in ("message", "text", "content"):
        value = candidate.get(field)
        if isinstance(value, str):
            parts.append(value)
    return " ".join(parts)


def _event_tool_name(event: dict[str, object]) -> str | None:
    candidate = _nested_event(event)
    event_type = candidate.get("type")
    if event_type not in {"tool_call", "function_call"}:
        return None
    name = candidate.get("name")
    if not isinstance(name, str):
        name = candidate.get("tool_name")
    return name if isinstance(name, str) else None


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(needle.lower() in lower for needle in needles)
```

- [ ] **Step 6: implement deterministic debugging checks**

Add these constants near the helpers in `evals/runner/check_tool.py`:

```python
RUNTIME_EVIDENCE_TERMS = (
    "modding.log",
    "player.log",
    "unity log",
    "playset",
    "installed package",
    "package layout",
    "localhost:9444",
    "ui debugger",
)

HANDOFF_TERMS = (
    "collect",
    "send",
    "reproduce",
    "playtest",
    "next step",
)

UNVERIFIED_FIX_CLAIMS = (
    "this is fixed",
    "fixed now",
    "verified fixed",
    "root cause is",
    "definitely",
)

EDIT_TOOL_NAMES = (
    "apply_patch",
    "write",
    "edit",
    "shell_command",
)
```

Add these blocks to `run_check()` before the final unknown-check block:

```python
    if name == "requests-runtime-evidence":
        text = _transcript_text(run_dir)
        status = "pass" if _has_any(text, RUNTIME_EVIDENCE_TERMS) else "fail"
        return _record(name, phase, status, "searched runtime evidence terms")

    if name == "no-unverified-fix-claim":
        text = _transcript_text(run_dir)
        has_claim = _has_any(text, UNVERIFIED_FIX_CLAIMS)
        has_evidence_request = _has_any(text, RUNTIME_EVIDENCE_TERMS)
        status = "pass" if not has_claim or has_evidence_request else "fail"
        return _record(
            name,
            phase,
            status,
            f"has_claim={has_claim}; has_evidence_request={has_evidence_request}",
        )

    if name == "handoff-present":
        text = _transcript_text(run_dir)
        has_handoff = _has_any(text, HANDOFF_TERMS) and _has_any(
            text, RUNTIME_EVIDENCE_TERMS
        )
        status = "pass" if has_handoff else "fail"
        return _record(name, phase, status, f"has_handoff={has_handoff}")

    if name == "no-edit-before-runtime-evidence":
        requested_evidence = False
        edit_before_request = False
        for event in _raw_events(run_dir):
            if _has_any(_event_text(event), RUNTIME_EVIDENCE_TERMS):
                requested_evidence = True
            tool_name = _event_tool_name(event)
            if tool_name is not None and any(
                marker in tool_name.lower() for marker in EDIT_TOOL_NAMES
            ):
                if not requested_evidence:
                    edit_before_request = True
                    break
        status = "pass" if not edit_before_request else "fail"
        return _record(
            name,
            phase,
            status,
            f"requested_evidence={requested_evidence}; edit_before_request={edit_before_request}",
        )
```

- [ ] **Step 7: run focused tests**

Run:

```powershell
python -m unittest tests.test_eval_checks -v
```

Expected: `OK`.

- [ ] **Step 8: run the code-change gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: `OK`.

- [ ] **Step 9: commit**

Run:

```powershell
git add evals/runner/check_tool.py tests/test_eval_checks.py
git commit -m "Add debugging baseline checks"
```

Open a PR targeting the current stack base. Request code review before merge.

## Task 4: offline debugging baseline runner smoke

Branch: `codex/evals-debugging-runner-smoke`

Base branch: `main` after Task 3 is merged.

**Files:**

- Modify: `tests/test_eval_runner_cli.py`
- Modify: `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/checks.sh`

- [ ] **Step 1: create the branch**

Run:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c codex/evals-debugging-runner-smoke
git status --short --branch
```

Expected: branch is `codex/evals-debugging-runner-smoke` based on `main` after Task 3 is merged, and the worktree is clean.

- [ ] **Step 2: write the failing offline smoke test**

Add this constant near `SCENARIO` in `tests/test_eval_runner_cli.py`:

```python
DEBUGGING_SCENARIO = (
    ROOT / "evals" / "scenarios" / "baseline" / "cities2-debugging-runtime-no-logs"
)
```

Add this test to `tests/test_eval_runner_cli.py`:

```python
@unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
def test_debugging_baseline_stub_writes_passing_verdict(self) -> None:
    from evals.runner.__main__ import run_eval

    with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
        root = Path(tmp)
        codex_stub = root / "codex_debugging_stub.py"
        codex_stub.write_text(
            textwrap.dedent(
                """\
                from __future__ import annotations

                print('{"type":"agent_message","message":"I cannot verify the root cause from source alone. Please collect Modding.log, Player.log, playset state, installed package layout, and localhost:9444 UI debugger output. Then reproduce in game and send those logs for the next step."}')
                """
            ),
            encoding="utf-8",
        )

        paths = run_eval(
            scenario_path=DEBUGGING_SCENARIO,
            condition="with-cities2-mod-debugging",
            repo_root=ROOT,
            results_root=root / "results",
            codex_command=sys.executable,
            codex_args_prefix=(str(codex_stub),),
            live_auth=False,
            trial=1,
        )

        verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))

    self.assertEqual("cities2-debugging-runtime-no-logs", verdict["metadata"]["scenario_id"])
    self.assertEqual("with-cities2-mod-debugging", verdict["metadata"]["condition_id"])
    self.assertEqual("pass", verdict["final"])
```

- [ ] **Step 3: run the test and verify it fails**

Run:

```powershell
python -m unittest tests.test_eval_runner_cli.EvalRunnerCliTests.test_debugging_baseline_stub_writes_passing_verdict -v
```

Expected: failure from missing condition support or missing deterministic checks if previous task is not merged; otherwise failure from scenario checks until `checks.sh` is aligned.

- [ ] **Step 4: align `checks.sh` with deterministic checks**

Ensure `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/checks.sh` contains exactly:

```bash
pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool no-edit-before-runtime-evidence
    python -m evals.runner.check_tool requests-runtime-evidence
    python -m evals.runner.check_tool no-unverified-fix-claim
    python -m evals.runner.check_tool handoff-present
}
```

- [ ] **Step 5: run focused runner tests**

Run:

```powershell
python -m unittest tests.test_eval_runner_cli tests.test_eval_checks -v
```

Expected: `OK`.

- [ ] **Step 6: run the code-change gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: `OK`.

- [ ] **Step 7: commit**

Run:

```powershell
git add tests/test_eval_runner_cli.py evals/scenarios/baseline/cities2-debugging-runtime-no-logs/checks.sh
git commit -m "Smoke test debugging baseline runner"
```

Open a PR targeting the current stack base. Request code review before merge.

## Task 5: curated baseline summary helper

Branch: `codex/evals-baseline-summary`

Base branch: `main` after Task 4 is merged.

**Files:**

- Create: `evals/runner/summary.py`
- Create: `tests/test_eval_summary.py`
- Modify: `docs/superpowers/evaluations/2026-06-04-cities2-debugging-runtime-no-logs-baseline.md`

- [ ] **Step 1: create the branch**

Run:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c codex/evals-baseline-summary
git status --short --branch
```

Expected: branch is `codex/evals-baseline-summary` based on `main` after Task 4 is merged, and the worktree is clean.

- [ ] **Step 2: write failing summary tests**

Create `tests/test_eval_summary.py`:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class EvalSummaryTests(unittest.TestCase):
    def test_summarizes_verdicts_without_raw_paths(self) -> None:
        from evals.runner.summary import summarize_verdicts

        with tempfile.TemporaryDirectory(prefix="cities2-eval-summary-") as tmp:
            root = Path(tmp)
            run = root / "evals" / "results" / "run-1"
            run.mkdir(parents=True)
            verdict = {
                "metadata": {
                    "scenario_id": "cities2-debugging-runtime-no-logs",
                    "condition_id": "with-cities2-mod-debugging",
                    "trial": 1,
                    "backend_name": "codex",
                    "repo_commit": "abc123",
                    "skill_checksums": {
                        "cities2-mod-debugging": "sha256:1234",
                    },
                },
                "final": "pass",
                "final_reason": "all checks passed",
                "checks": [
                    {
                        "name": "requests-runtime-evidence",
                        "phase": "post",
                        "status": "pass",
                        "detail": "searched runtime evidence terms",
                    }
                ],
                "trace_path": "coding-agent-tool-calls.jsonl",
                "transcript_path": "transcript.txt",
            }
            (run / "verdict.json").write_text(
                json.dumps(verdict, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = summarize_verdicts([run / "verdict.json"])

        self.assertIn("cities2-debugging-runtime-no-logs", summary)
        self.assertIn("with-cities2-mod-debugging", summary)
        self.assertIn("pass=1", summary)
        self.assertIn("sha256:1234", summary)
        self.assertNotIn(str(root), summary)
        self.assertNotIn("coding-agent-tool-calls.jsonl", summary)
        self.assertNotIn("transcript.txt", summary)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: run the test and verify it fails**

Run:

```powershell
python -m unittest tests.test_eval_summary -v
```

Expected: failure because `evals.runner.summary` does not exist.

- [ ] **Step 4: implement `evals/runner/summary.py`**

Create `evals/runner/summary.py`:

```python
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


def _load(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"verdict must be an object: {path}")
    return data


def summarize_verdicts(paths: Iterable[Path]) -> str:
    verdicts = [_load(path) for path in paths]
    counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    checks: dict[str, Counter[str]] = defaultdict(Counter)
    commits: set[str] = set()
    checksums: set[str] = set()

    for verdict in verdicts:
        metadata = verdict.get("metadata")
        if not isinstance(metadata, dict):
            raise TypeError("verdict metadata must be an object")
        scenario = str(metadata.get("scenario_id", "unknown-scenario"))
        condition = str(metadata.get("condition_id", "unknown-condition"))
        final = str(verdict.get("final", "unknown"))
        counts[(scenario, condition)][final] += 1
        repo_commit = metadata.get("repo_commit")
        if isinstance(repo_commit, str) and repo_commit:
            commits.add(repo_commit)
        skill_checksums = metadata.get("skill_checksums")
        if isinstance(skill_checksums, dict):
            for value in skill_checksums.values():
                if isinstance(value, str):
                    checksums.add(value)
        for check in verdict.get("checks", []):
            if isinstance(check, dict):
                check_name = str(check.get("name", "unknown-check"))
                check_status = str(check.get("status", "unknown"))
                checks[check_name][check_status] += 1

    lines = ["# Cities2 debugging runtime-no-logs baseline summary", ""]
    lines.append(f"Verdicts summarized: {len(verdicts)}")
    lines.append(f"Repository commits: {', '.join(sorted(commits)) if commits else 'unknown'}")
    lines.append(f"Skill checksums: {', '.join(sorted(checksums)) if checksums else 'none'}")
    lines.append("")
    lines.append("## Final counts")
    for (scenario, condition), counter in sorted(counts.items()):
        lines.append(
            f"- {scenario} / {condition}: "
            f"pass={counter['pass']}; fail={counter['fail']}; "
            f"indeterminate={counter['indeterminate']}"
        )
    lines.append("")
    lines.append("## Check counts")
    for check_name, counter in sorted(checks.items()):
        lines.append(
            f"- {check_name}: pass={counter['pass']}; fail={counter['fail']}; "
            f"indeterminate={counter['indeterminate']}"
        )
    lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 5: add a baseline summary template**

Create `docs/superpowers/evaluations/2026-06-04-cities2-debugging-runtime-no-logs-baseline.md`:

```markdown
# Cities2 debugging runtime-no-logs baseline

## Short version

This document records the first `cities2-mod-debugging` behavioral baseline after the eval runner harness spike.

## Scenario

Scenario path: `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/`

## Matrix

```text
1 scenario
x 2 conditions:
  - no-skill
  - with-cities2-mod-debugging
x 3 clean-room trials each
= 6 runs
```

## Result storage

Raw traces, full transcripts, generated workdirs, and generated agent homes remain under gitignored `evals/results/`.

## Baseline results

Baseline results are not recorded yet. Fill this section only after the six-run matrix has been executed and reviewed.

## Review notes

- Do not edit `SKILL.md` files as part of recording this baseline.
- If checks fail because live Codex trace tool names differ from stub names, update the deterministic checks in a separate reviewed branch before trusting the baseline.
```

- [ ] **Step 6: run summary tests**

Run:

```powershell
python -m unittest tests.test_eval_summary tests.test_eval_docs -v
```

Expected: `OK`.

- [ ] **Step 7: run code and plugin gates**

Run:

```powershell
python -m unittest discover -s tests -v
python -m cities2_mcp.plugin_packages check
```

Expected: both commands pass.

- [ ] **Step 8: commit**

Run:

```powershell
git add evals/runner/summary.py tests/test_eval_summary.py docs/superpowers/evaluations/2026-06-04-cities2-debugging-runtime-no-logs-baseline.md
git commit -m "Add debugging baseline summary helper"
```

Open a PR targeting the current stack base. Request code review before merge.

## Task 6: live Codex trace-name calibration

Branch: `codex/evals-codex-trace-calibration`

Base branch: `main` after Task 5 is merged.

**Files:**

- Modify: `docs/superpowers/evaluations/2026-06-04-cities2-debugging-runtime-no-logs-baseline.md`
- Modify: `evals/runner/check_tool.py`
- Modify: `tests/test_eval_checks.py`

- [ ] **Step 1: create the branch**

Run:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c codex/evals-codex-trace-calibration
git status --short --branch
```

Expected: branch is `codex/evals-codex-trace-calibration` based on `main` after Task 5 is merged, and the worktree is clean.

- [ ] **Step 2: run one local calibration trial**

Run a single with-skill Codex trial using local OAuth/profile setup only if the maintainer confirms local auth is ready:

```powershell
python -m evals.runner evals/scenarios/baseline/cities2-debugging-runtime-no-logs --condition with-cities2-mod-debugging --trial 99
```

Expected: command prints a repo-relative or local `verdict.json` path. The exit code may be `0`, `1`, or `2`; inspect the verdict file rather than treating the exit code alone as the result.

- [ ] **Step 3: inspect only curated trace shape**

Do not commit raw trace output. Inspect tool names locally:

```powershell
$latest = Get-ChildItem -Directory evals/results | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content -LiteralPath (Join-Path $latest.FullName 'coding-agent-tool-calls.jsonl') | Select-Object -First 20
```

Expected: identify whether real tool names are bare names like `source_status`, prefixed names like `cities2-mcp__source_status`, or another shape.

- [ ] **Step 4: add suffix-tolerant tool-name matching**

Update `evals/runner/check_tool.py` with this helper. This keeps exact stub behavior working and also accepts server-prefixed MCP tool names if the real Codex trace uses them.

```python
def _tool_name_matches(actual: str, expected: str) -> bool:
    return actual == expected or actual.endswith(f"__{expected}")
```

Then change `tool-called`, `skill-called`, and `not-tool-called` to use `_tool_name_matches()`:

```python
if name in ("skill-called", "tool-called"):
    expected = args[0] if args else ""
    names = _tool_names(run_dir)
    status = "pass" if expected and any(_tool_name_matches(tool_name, expected) for tool_name in names) else "fail"
    return _record(name, phase, status, f"expected={expected}; names={names}")

if name == "not-tool-called":
    expected = args[0] if args else ""
    names = _tool_names(run_dir)
    called = any(_tool_name_matches(tool_name, expected) for tool_name in names)
    status = "pass" if expected and not called else "fail"
    return _record(name, phase, status, f"expected={expected}; names={names}")
```

Add this test to `tests/test_eval_checks.py`:

```python
def test_tool_called_accepts_mcp_server_prefix(self) -> None:
    from evals.runner.check_tool import run_check

    with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
        run_dir = Path(tmp)
        workdir = run_dir / "coding-agent-workdir"
        agent_home = run_dir / "coding-agent-config"
        workdir.mkdir()
        agent_home.mkdir()
        (run_dir / "coding-agent-tool-calls.jsonl").write_text(
            json.dumps({"name": "cities2-mcp__source_status", "arguments": {}}) + "\n",
            encoding="utf-8",
        )

        record = run_check(
            "tool-called",
            ["source_status"],
            run_dir=run_dir,
            workdir=workdir,
            agent_home=agent_home,
            condition="with-cities2-mod-debugging",
            phase="post",
        )

    self.assertEqual("pass", record.status)
```

- [ ] **Step 5: record calibration outcome without raw data**

Append one of these exact snippets to `docs/superpowers/evaluations/2026-06-04-cities2-debugging-runtime-no-logs-baseline.md`.

Use this snippet when the calibration run shows server-prefixed MCP tool names:

```markdown
## Codex trace-name calibration

One local calibration run was used to inspect the shape of Codex tool names. Raw trace output remains under gitignored `evals/results/` and is not committed.

Observed tool-name shape: server-prefixed MCP names.

Check helper update needed: yes.
```

Use this snippet when the calibration run shows bare tool names:

```markdown
## Codex trace-name calibration

One local calibration run was used to inspect the shape of Codex tool names. Raw trace output remains under gitignored `evals/results/` and is not committed.

Observed tool-name shape: bare tool names.

Check helper update needed: suffix-tolerant matching was still added so future server-prefixed MCP names remain supported.
```

Do not include local paths, usernames, raw transcript text, or raw JSONL.

- [ ] **Step 6: run gates**

Run:

```powershell
python -m unittest tests.test_eval_checks tests.test_eval_runner_cli -v
python -m unittest discover -s tests -v
python -m cities2_mcp.plugin_packages check
git ls-files evals/results
git diff --check
```

Expected: tests and plugin check pass, `git ls-files evals/results` prints no tracked files, and `git diff --check` prints no errors.

- [ ] **Step 7: commit**

If only docs changed:

```powershell
git add docs/superpowers/evaluations/2026-06-04-cities2-debugging-runtime-no-logs-baseline.md
git commit -m "Record Codex eval trace calibration"
```

If code and tests changed:

```powershell
git add evals/runner/check_tool.py tests/test_eval_checks.py docs/superpowers/evaluations/2026-06-04-cities2-debugging-runtime-no-logs-baseline.md
git commit -m "Calibrate eval checks for Codex trace names"
```

Open a PR targeting the current stack base. Request code review before merge.

## Task 7: six-run Codex baseline matrix

Branch: `codex/evals-debugging-baseline-results`

Base branch: `main` after Task 6 is merged.

**Files:**

- Modify: `docs/superpowers/evaluations/2026-06-04-cities2-debugging-runtime-no-logs-baseline.md`
- Do not add: `evals/results/**`

- [ ] **Step 1: create the branch**

Run:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c codex/evals-debugging-baseline-results
git status --short --branch
```

Expected: branch is `codex/evals-debugging-baseline-results` based on `main` after Task 6 is merged, and the worktree is clean.

- [ ] **Step 2: run the no-skill trials**

Run:

```powershell
python -m evals.runner evals/scenarios/baseline/cities2-debugging-runtime-no-logs --condition no-skill --trial 1
python -m evals.runner evals/scenarios/baseline/cities2-debugging-runtime-no-logs --condition no-skill --trial 2
python -m evals.runner evals/scenarios/baseline/cities2-debugging-runtime-no-logs --condition no-skill --trial 3
```

Expected: each command prints a `verdict.json` path under `evals/results/`. Exit codes may differ; the verdict files are the source of truth.

- [ ] **Step 3: run the with-skill trials**

Run:

```powershell
python -m evals.runner evals/scenarios/baseline/cities2-debugging-runtime-no-logs --condition with-cities2-mod-debugging --trial 1
python -m evals.runner evals/scenarios/baseline/cities2-debugging-runtime-no-logs --condition with-cities2-mod-debugging --trial 2
python -m evals.runner evals/scenarios/baseline/cities2-debugging-runtime-no-logs --condition with-cities2-mod-debugging --trial 3
```

Expected: each command prints a `verdict.json` path under `evals/results/`. Exit codes may differ; the verdict files are the source of truth.

- [ ] **Step 4: summarize the verdicts locally**

Run this local one-off command until `evals.runner.summary` grows a CLI:

```powershell
@'
from pathlib import Path
from evals.runner.summary import summarize_verdicts

paths = sorted(Path("evals/results").glob("cities2-debugging-runtime-no-logs-*/verdict.json"))
print(summarize_verdicts(paths))
'@ | python -
```

Expected: a curated summary with six verdicts and no local absolute paths.

- [ ] **Step 5: update the baseline summary document**

Replace the `## Baseline results` section in `docs/superpowers/evaluations/2026-06-04-cities2-debugging-runtime-no-logs-baseline.md` with the exact curated summary output from Step 4. Add this interpretation text below the generated check counts:

```markdown
## Interpretation

The first baseline records current behavior only. It does not justify editing `cities2-mod-debugging` until the maintainer reviews these results.
```

Use actual counts from the local summary output. Do not paste raw transcript excerpts or local paths.

- [ ] **Step 6: verify no raw results are tracked**

Run:

```powershell
git ls-files evals/results
git status --short
```

Expected: `git ls-files evals/results` prints nothing. `git status --short` shows only the curated summary document unless intentional code/test changes are present.

- [ ] **Step 7: run gates**

Run:

```powershell
python -m unittest discover -s tests -v
python -m cities2_mcp.plugin_packages check
git diff --check
```

Expected: all commands pass.

- [ ] **Step 8: commit**

Run:

```powershell
git add docs/superpowers/evaluations/2026-06-04-cities2-debugging-runtime-no-logs-baseline.md
git commit -m "Record debugging runtime baseline results"
```

Open a PR targeting the current stack base. Request Claude, Agy, and Codex review. Do not merge until the maintainer reviews the curated baseline summary.

## Final baseline gate

The phase is complete only when the repository can report:

- One committed `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/` scenario.
- A clean-room runner path for `no-skill` and `with-cities2-mod-debugging`.
- Three no-skill Codex trials and three with-skill Codex trials.
- A `verdict.json` for every trial under gitignored `evals/results/`.
- Deterministic checks for runtime evidence request, edit avoidance before runtime evidence, no unverified fix claim, and concrete handoff.
- A curated baseline summary committed under `docs/superpowers/evaluations/`.
- No `SKILL.md` edits.
- No raw eval traces, full transcripts, generated workdirs, generated agent homes, local paths, usernames, or secrets in committed files.

## Follow-up after this baseline

After the maintainer reviews the baseline summary:

- Decide whether `cities2-mod-debugging` needs skill changes.
- If skill changes are approved, use `superpowers:writing-skills` before editing `skills/cities2-mod-debugging/SKILL.md`.
- Add a compound-pressure version of the runtime-no-logs scenario.
- Add `claude` and `agy` adapters or documented manual protocols for the same scenario only after the Codex baseline checks are trusted.

## Self-review notes

- Spec coverage: this plan covers the first behavioral baseline scenario, the two-condition six-run matrix, clean-room condition support, deterministic checks, raw-artifact hygiene, curated summary, and the no-skill-edit gate.
- Deferred by design: this plan does not edit `SKILL.md` files, does not add compound-pressure scenarios, and does not implement full Claude or Agy adapters.
- Known risk: deterministic checks use textual heuristics and Codex trace events. Task 6 calibrates real Codex trace names before the six-run matrix is trusted.
