# Codex skill effectiveness matrix implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run and publish a Codex-only directional effectiveness matrix for all five shipped Cities2 skills without editing any `SKILL.md` files.

**Architecture:** Keep the phase scenario-first and stacked. Commit this plan on the feature-root branch, then stack small implementation PRs for condition support, the three missing scenarios, and the final sanitized matrix dossier. Reuse the existing Quorum-compatible scenario contract, Codex runner isolation, verdict files, and digest/privacy helpers instead of building a new orchestration platform.

**Tech Stack:** Python 3.10 standard library, `unittest`, Bash scenario hooks, existing `evals.runner` modules, Codex CLI with local OAuth/profile auth, GitHub stacked PRs.

---

## Ground rules

- Use `superpowers:writing-skills` as the evidence model before drafting final conclusions: RED no-skill baseline, GREEN with-target-skill comparison, REFACTOR decision classification.
- Do not edit any `SKILL.md` files in this phase.
- Do not commit raw eval traces, full transcripts, generated workdirs, generated agent homes, local paths, usernames, secrets, machine-specific output, or `evals/results/` artifacts.
- Before editing each task branch, run `git status --short --branch`.
- Code changes require `python -m unittest discover -s tests -v`.
- Plugin payload changes require `python -m cities2_mcp.plugin_packages check`; this plan does not intentionally change plugin payload files.
- For every branch created in this stack, print the new branch name and the exact branch or commit it branches from before creating it.
- Every implementation PR must target the previous stack branch, not `main`, except the feature-root plan PR.
- Every PR must have `agent-work`, one priority label, one area label, and the `skill-quality` project.
- Every PR body must include `Stacked on: <branch or PR>` when it is not the root PR.
- Request independent review before marking each PR ready. Treat review evidence as stale after any follow-up commit.
- Prefer `agy` only after the branch is pushed and the PR exists. Verify every `agy` finding against the active worktree before acting.

## Current state

The merged design spec is `docs/superpowers/specs/2026-06-07-codex-skill-effectiveness-matrix-design.md`.

The runner already supports:

- `evals/scenarios/spike/cities2-knowledge-office-demand/`
- `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/`
- `no-skill`, `with-cities2-knowledge`, and `with-cities2-mod-debugging`
- clean Codex home setup with condition-scoped skill copying
- `evals/results/` raw artifact isolation
- deterministic check records and verdict writing
- sanitized digest generation in `evals/runner/summary.py`

Missing for the five-skill matrix:

- condition support for `with-cities2-modding`, `with-cities2-mod-review`, and `with-cities2-mod-release`
- representative scenarios for `cities2-modding`, `cities2-mod-review`, and `cities2-mod-release`
- a published matrix dossier that summarizes all 30 Codex trials in maintainer-readable prose

## Stack shape

Feature-root branch:

```text
codex/codex-skill-effectiveness-matrix
```

Implementation stack:

```text
codex/evals-matrix-condition-foundation
  -> codex/evals-matrix-mod-review-scenario
    -> codex/evals-matrix-release-scenario
      -> codex/evals-matrix-modding-scenario
        -> codex/evals-matrix-results-dossier
```

Open the feature-root PR against `main` with only this plan. Then open each implementation PR against its stack parent.

## File structure

- Create `docs/superpowers/plans/2026-06-07-codex-skill-effectiveness-matrix.md`: this feature-root implementation plan.
- Create `evals/runner/conditions.py`: one source of truth for supported eval conditions and target skill directories.
- Modify `evals/runner/__main__.py`: use the shared condition registry for CLI choices and skill copying.
- Modify `evals/runner/check_tool.py`: use the shared condition registry and add generic transcript checks used by matrix scenarios.
- Modify `tests/test_eval_runner_cli.py`: cover all matrix conditions and stub-smoke each new scenario.
- Modify `tests/test_eval_checks.py`: cover shared condition checks and generic transcript checks.
- Modify `tests/test_eval_scenario_layout.py`: verify the new scenarios follow the `story.md`, `setup.sh`, `checks.sh` contract.
- Modify `tests/test_eval_scenario_loader.py`: verify the new scenarios load.
- Create `evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence/{story.md,setup.sh,checks.sh}`.
- Create `evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest/{story.md,setup.sh,checks.sh}`.
- Create `evals/scenarios/matrix/cities2-modding-workflow-safe-handoff/{story.md,setup.sh,checks.sh}`.
- Create `docs/superpowers/evaluations/2026-06-07-cities2-codex-skill-effectiveness-matrix.md`: final sanitized matrix dossier if the matrix is run on June 7, 2026. If execution starts on a later date, stop before Task 5 and update this plan to use that actual run date.

## Task 1: condition registry and shared transcript checks

Branch: `codex/evals-matrix-condition-foundation`

Base branch: `codex/codex-skill-effectiveness-matrix`

Stacked on: feature-root PR or `codex/codex-skill-effectiveness-matrix`

**Files:**

- Create: `evals/runner/conditions.py`
- Modify: `evals/runner/__main__.py`
- Modify: `evals/runner/check_tool.py`
- Modify: `tests/test_eval_runner_cli.py`
- Modify: `tests/test_eval_checks.py`

- [ ] **Step 1: create the branch**

Print before running:

```text
New branch: codex/evals-matrix-condition-foundation
Branch from: codex/codex-skill-effectiveness-matrix
```

Run:

```powershell
git fetch origin
git status --short --branch
git switch codex/codex-skill-effectiveness-matrix
git pull --ff-only origin codex/codex-skill-effectiveness-matrix
git switch -c codex/evals-matrix-condition-foundation
git status --short --branch
```

Expected: branch is `codex/evals-matrix-condition-foundation`, based on the feature-root branch, and the worktree is clean.

- [ ] **Step 2: write failing condition registry tests**

Add these tests to `tests/test_eval_runner_cli.py`:

```python
def test_condition_skills_supports_all_matrix_target_conditions(self) -> None:
    from evals.runner.__main__ import _condition_skills

    expected = {
        "no-skill": (),
        "with-cities2-knowledge": ("cities2-knowledge",),
        "with-cities2-modding": ("cities2-modding",),
        "with-cities2-mod-review": ("cities2-mod-review",),
        "with-cities2-mod-debugging": ("cities2-mod-debugging",),
        "with-cities2-mod-release": ("cities2-mod-release",),
    }
    for condition, skills in expected.items():
        with self.subTest(condition=condition):
            self.assertEqual(skills, _condition_skills(condition))
```

Add this test to `tests/test_eval_checks.py`:

```python
def test_condition_skill_set_supports_all_matrix_target_conditions(self) -> None:
    from evals.runner.check_tool import run_check

    expected = {
        "no-skill": [],
        "with-cities2-knowledge": ["cities2-knowledge"],
        "with-cities2-modding": ["cities2-modding"],
        "with-cities2-mod-review": ["cities2-mod-review"],
        "with-cities2-mod-debugging": ["cities2-mod-debugging"],
        "with-cities2-mod-release": ["cities2-mod-release"],
    }

    for condition, skills in expected.items():
        with self.subTest(condition=condition):
            with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
                run_dir = Path(tmp)
                workdir = run_dir / "coding-agent-workdir"
                agent_home = run_dir / "coding-agent-config"
                workdir.mkdir()
                for skill in skills:
                    (agent_home / "skills" / skill).mkdir(parents=True)

                record = run_check(
                    "condition-skill-set",
                    [],
                    run_dir=run_dir,
                    workdir=workdir,
                    agent_home=agent_home,
                    condition=condition,
                    phase="pre",
                )

            self.assertEqual("pass", record.status)
```

- [ ] **Step 3: write failing generic transcript check tests**

Add this test to `tests/test_eval_checks.py`:

```python
def test_generic_transcript_contains_all_any_and_not_contains_any(self) -> None:
    from evals.runner.check_tool import run_check

    with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
        run_dir = Path(tmp)
        workdir = run_dir / "coding-agent-workdir"
        agent_home = run_dir / "coding-agent-config"
        workdir.mkdir()
        agent_home.mkdir()
        (run_dir / "transcript.txt").write_text(
            "Findings: observed files show a TSX file. "
            "There is not enough evidence to require React. "
            "The CSS file is not loaded, so it has no current effect.",
            encoding="utf-8",
        )

        contains_all = run_check(
            "transcript-contains-all",
            ["Findings", "observed", "CSS"],
            run_dir=run_dir,
            workdir=workdir,
            agent_home=agent_home,
            condition="with-cities2-mod-review",
            phase="post",
        )
        contains_any = run_check(
            "transcript-contains-any",
            ["playtested package", "not enough evidence"],
            run_dir=run_dir,
            workdir=workdir,
            agent_home=agent_home,
            condition="with-cities2-mod-review",
            phase="post",
        )
        not_contains_any = run_check(
            "transcript-not-contains-any",
            ["install React", "ready for upload now"],
            run_dir=run_dir,
            workdir=workdir,
            agent_home=agent_home,
            condition="with-cities2-mod-review",
            phase="post",
        )
        missing_all = run_check(
            "transcript-contains-all",
            ["Findings", "playtested package"],
            run_dir=run_dir,
            workdir=workdir,
            agent_home=agent_home,
            condition="with-cities2-mod-review",
            phase="post",
        )

    self.assertEqual("pass", contains_all.status)
    self.assertEqual("pass", contains_any.status)
    self.assertEqual("pass", not_contains_any.status)
    self.assertEqual("fail", missing_all.status)
```

- [ ] **Step 4: run the focused tests and verify failure**

Run:

```powershell
python -m unittest tests.test_eval_runner_cli tests.test_eval_checks -v
```

Expected: failures mention unsupported conditions or unknown transcript checks.

- [ ] **Step 5: create `evals/runner/conditions.py`**

Create `evals/runner/conditions.py`:

```python
from __future__ import annotations


CONDITION_SKILLS: dict[str, tuple[str, ...]] = {
    "no-skill": (),
    "with-cities2-knowledge": ("cities2-knowledge",),
    "with-cities2-modding": ("cities2-modding",),
    "with-cities2-mod-review": ("cities2-mod-review",),
    "with-cities2-mod-debugging": ("cities2-mod-debugging",),
    "with-cities2-mod-release": ("cities2-mod-release",),
}


def condition_skills(condition: str) -> tuple[str, ...]:
    try:
        return CONDITION_SKILLS[condition]
    except KeyError as error:
        raise ValueError(f"unsupported condition: {condition}") from error
```

- [ ] **Step 6: update `evals/runner/__main__.py`**

Import the registry:

```python
from evals.runner.conditions import CONDITION_SKILLS, condition_skills
```

Replace `_condition_skills()` with this wrapper so existing tests and callers keep working:

```python
def _condition_skills(condition: str) -> tuple[str, ...]:
    return condition_skills(condition)
```

Replace the `--condition` choices with:

```python
choices=tuple(CONDITION_SKILLS),
```

- [ ] **Step 7: update `evals/runner/check_tool.py`**

Import the registry:

```python
from .conditions import condition_skills
```

Replace the `condition-skill-set` block with:

```python
if name == "condition-skill-set":
    try:
        expected = list(condition_skills(condition))
    except ValueError:
        actual = _skill_dirs(agent_home)
        return _record(
            name,
            phase,
            "indeterminate",
            f"unknown condition={condition}; actual={actual}",
        )
    actual = _skill_dirs(agent_home)
    status = "pass" if actual == expected else "fail"
    return _record(name, phase, status, f"expected={expected}; actual={actual}")
```

Add these helpers near `_has_any()`:

```python
def _contains_all(text: str, needles: list[str]) -> bool:
    lower_text = text.lower()
    return bool(needles) and all(needle.lower() in lower_text for needle in needles)


def _contains_any_arg(text: str, needles: list[str]) -> bool:
    lower_text = text.lower()
    return bool(needles) and any(needle.lower() in lower_text for needle in needles)
```

Add these checks near `transcript-contains`:

```python
if name == "transcript-contains-all":
    text = _transcript_text(run_dir)
    status = "pass" if _contains_all(text, args) else "fail"
    return _record(name, phase, status, f"needles={args}")

if name == "transcript-contains-any":
    text = _transcript_text(run_dir)
    status = "pass" if _contains_any_arg(text, args) else "fail"
    return _record(name, phase, status, f"needles={args}")

if name == "transcript-not-contains-any":
    text = _transcript_text(run_dir)
    status = "pass" if args and not _contains_any_arg(text, args) else "fail"
    return _record(name, phase, status, f"needles={args}")
```

- [ ] **Step 8: run focused tests**

Run:

```powershell
python -m unittest tests.test_eval_runner_cli tests.test_eval_checks -v
```

Expected: `OK`.

- [ ] **Step 9: run the code-change gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: `OK`.

- [ ] **Step 10: commit and open PR**

Run:

```powershell
git add evals/runner/conditions.py evals/runner/__main__.py evals/runner/check_tool.py tests/test_eval_runner_cli.py tests/test_eval_checks.py
git commit -m "Add eval matrix condition foundation"
```

Open a PR targeting `codex/codex-skill-effectiveness-matrix`. Add labels, project, `Stacked on: codex/codex-skill-effectiveness-matrix`, verification evidence, and `*Co-authored by Codex.*`. Request independent review against the exact pushed branch tip.

## Task 2: `cities2-mod-review` scenario

Branch: `codex/evals-matrix-mod-review-scenario`

Base branch: `codex/evals-matrix-condition-foundation`

Stacked on: Task 1 PR

**Files:**

- Create: `evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence/story.md`
- Create: `evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence/setup.sh`
- Create: `evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence/checks.sh`
- Modify: `tests/test_eval_scenario_layout.py`
- Modify: `tests/test_eval_scenario_loader.py`
- Modify: `tests/test_eval_runner_cli.py`

- [ ] **Step 1: create the branch**

Print before running:

```text
New branch: codex/evals-matrix-mod-review-scenario
Branch from: codex/evals-matrix-condition-foundation
```

Run:

```powershell
git fetch origin
git status --short --branch
git switch codex/evals-matrix-condition-foundation
git pull --ff-only origin codex/evals-matrix-condition-foundation
git switch -c codex/evals-matrix-mod-review-scenario
git status --short --branch
```

Expected: branch is `codex/evals-matrix-mod-review-scenario`, based on Task 1, and the worktree is clean.

- [ ] **Step 2: write failing scenario tests**

Add a constant to `tests/test_eval_scenario_layout.py`:

```python
REVIEW_MATRIX_SCENARIO = ROOT / "evals" / "scenarios" / "matrix" / "cities2-mod-review-tsx-no-react-evidence"
```

Add this test to `tests/test_eval_scenario_layout.py`:

```python
def test_review_matrix_scenario_uses_quorum_contract(self) -> None:
    self.assertTrue((REVIEW_MATRIX_SCENARIO / "story.md").is_file())
    self.assertTrue((REVIEW_MATRIX_SCENARIO / "setup.sh").is_file())
    self.assertTrue((REVIEW_MATRIX_SCENARIO / "checks.sh").is_file())

    story = (REVIEW_MATRIX_SCENARIO / "story.md").read_text(encoding="utf-8")
    checks = (REVIEW_MATRIX_SCENARIO / "checks.sh").read_text(encoding="utf-8")

    self.assertIn("id: cities2-mod-review-tsx-no-react-evidence", story)
    self.assertIn("OptionsPanel.tsx", story)
    self.assertIn("theme.css", story)
    self.assertIn("transcript-not-contains-any", checks)
    self.assertIn("install React", checks)
```

Add this test to `tests/test_eval_scenario_loader.py`:

```python
def test_loads_committed_review_matrix_scenario(self) -> None:
    from evals.runner.scenario import load_scenario

    scenario = load_scenario(
        ROOT
        / "evals"
        / "scenarios"
        / "matrix"
        / "cities2-mod-review-tsx-no-react-evidence"
    )

    self.assertEqual("cities2-mod-review-tsx-no-react-evidence", scenario.id)
    self.assertEqual("Cities2 mod review avoids unsupported React claims", scenario.title)
```

- [ ] **Step 3: run scenario tests and verify failure**

Run:

```powershell
python -m unittest tests.test_eval_scenario_layout tests.test_eval_scenario_loader -v
```

Expected: failures mention the missing review matrix scenario files.

- [ ] **Step 4: create `story.md`**

Create `evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence/story.md`:

````markdown
---
id: cities2-mod-review-tsx-no-react-evidence
title: Cities2 mod review avoids unsupported React claims
---

# Cities2 mod review avoids unsupported React claims

## Story

The user asks for a review of a small Cities: Skylines II mod scaffold. The fixture includes a `.tsx` file and an unreferenced CSS file, which tempts unsupported claims about React, loaders, runtime requirements, or active styling.

## Acceptance Criteria

- Lead with findings ordered by severity.
- Distinguish observed project facts from supported guidance and inferred recommendations.
- Do not claim React, a React loader, or a React dependency is required from `.tsx` alone.
- Treat the unreferenced CSS file as having no current effect unless inspected files load it.
- Avoid public release or runtime-readiness claims because this is a review-only scenario.

## Prompt

```text
Please review this small Cities: Skylines II mod scaffold for safety, maintainability, packaging hygiene, and readiness. I noticed `OptionsPanel.tsx` and `theme.css`, so I assume this is a React UI mod and the missing React loader is probably the top issue. Tell me what I should fix first.
```
````

- [ ] **Step 5: create `setup.sh`**

Create `evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence/setup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

git init -b main >/dev/null
git config user.email "eval@example.invalid"
git config user.name "Eval Runner"

mkdir -p ReviewBaitMod/ui ReviewBaitMod/src
cat > ReviewBaitMod/ui/OptionsPanel.tsx <<'EOF'
export function OptionsPanel() {
    return <panel class="options-panel">Options</panel>;
}
EOF

cat > ReviewBaitMod/ui/theme.css <<'EOF'
.options-panel {
    color: white;
}
EOF

cat > ReviewBaitMod/src/Mod.cs <<'EOF'
namespace ReviewBaitMod;

public sealed class Mod
{
    public string Name => "Review Bait Mod";
}
EOF

cat > ReviewBaitMod/README.md <<'EOF'
# Review Bait Mod

Small scaffold for review. No package dependencies are declared in this fixture.
EOF

git add ReviewBaitMod
git commit -m "Seed review eval fixture" >/dev/null
```

- [ ] **Step 6: create `checks.sh`**

Create `evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence/checks.sh`:

```bash
pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-called cities2-mod-review
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool transcript-contains-any Findings findings
    python -m evals.runner.check_tool transcript-contains-all observed inferred
    python -m evals.runner.check_tool transcript-contains-all CSS 'not loaded'
    python -m evals.runner.check_tool transcript-not-contains-any 'install React' 'missing React dependency' 'React loader is required' 'must use React'
}
```

- [ ] **Step 7: add a passing runner smoke**

Add a constant to `tests/test_eval_runner_cli.py`:

```python
REVIEW_MATRIX_SCENARIO = ROOT / "evals" / "scenarios" / "matrix" / "cities2-mod-review-tsx-no-react-evidence"
```

Add this test to `tests/test_eval_runner_cli.py`:

```python
@unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
def test_review_matrix_stub_writes_passing_verdict(self) -> None:
    from evals.runner.__main__ import run_eval

    with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
        root = Path(tmp)
        codex_stub = root / "codex_review_stub.py"
        codex_stub.write_text(
            textwrap.dedent(
                """\
                from __future__ import annotations

                print('{"type":"tool_call","name":"cities2-mod-review","arguments":{}}')
                print('{"type":"agent_message","message":"Findings: observed project files show OptionsPanel.tsx and an unreferenced CSS file. Supported evidence is limited because no package dependencies or imports prove React. Inferred recommendation: do not require React from TSX alone. The CSS file is not loaded, so it has no current effect."}')
                """
            ),
            encoding="utf-8",
        )

        paths = run_eval(
            scenario_path=REVIEW_MATRIX_SCENARIO,
            condition="with-cities2-mod-review",
            repo_root=ROOT,
            results_root=root / "results",
            codex_command=sys.executable,
            codex_args_prefix=(str(codex_stub),),
            live_auth=False,
            trial=1,
        )

        verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))

    self.assertEqual("cities2-mod-review-tsx-no-react-evidence", verdict["metadata"]["scenario_id"])
    self.assertEqual("with-cities2-mod-review", verdict["metadata"]["condition_id"])
    self.assertEqual("pass", verdict["final"])
```

- [ ] **Step 8: run focused tests**

Run:

```powershell
python -m unittest tests.test_eval_scenario_layout tests.test_eval_scenario_loader tests.test_eval_runner_cli -v
```

Expected: `OK`.

- [ ] **Step 9: run the code-change gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: `OK`.

- [ ] **Step 10: commit and open PR**

Run:

```powershell
git add evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence tests/test_eval_scenario_layout.py tests/test_eval_scenario_loader.py tests/test_eval_runner_cli.py
git commit -m "Add mod review matrix scenario"
```

Open a PR targeting `codex/evals-matrix-condition-foundation`. Add labels, project, `Stacked on: <Task 1 PR>`, verification evidence, and `*Co-authored by Codex.*`. Request independent review against the exact pushed branch tip.

## Task 3: `cities2-mod-release` scenario

Branch: `codex/evals-matrix-release-scenario`

Base branch: `codex/evals-matrix-mod-review-scenario`

Stacked on: Task 2 PR

**Files:**

- Create: `evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest/story.md`
- Create: `evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest/setup.sh`
- Create: `evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest/checks.sh`
- Modify: `tests/test_eval_scenario_layout.py`
- Modify: `tests/test_eval_scenario_loader.py`
- Modify: `tests/test_eval_runner_cli.py`

- [ ] **Step 1: create the branch**

Print before running:

```text
New branch: codex/evals-matrix-release-scenario
Branch from: codex/evals-matrix-mod-review-scenario
```

Run:

```powershell
git fetch origin
git status --short --branch
git switch codex/evals-matrix-mod-review-scenario
git pull --ff-only origin codex/evals-matrix-mod-review-scenario
git switch -c codex/evals-matrix-release-scenario
git status --short --branch
```

Expected: branch is `codex/evals-matrix-release-scenario`, based on Task 2, and the worktree is clean.

- [ ] **Step 2: write failing scenario tests**

Add a constant to `tests/test_eval_scenario_layout.py`:

```python
RELEASE_MATRIX_SCENARIO = ROOT / "evals" / "scenarios" / "matrix" / "cities2-mod-release-build-passed-no-playtest"
```

Add this test to `tests/test_eval_scenario_layout.py`:

```python
def test_release_matrix_scenario_uses_quorum_contract(self) -> None:
    self.assertTrue((RELEASE_MATRIX_SCENARIO / "story.md").is_file())
    self.assertTrue((RELEASE_MATRIX_SCENARIO / "setup.sh").is_file())
    self.assertTrue((RELEASE_MATRIX_SCENARIO / "checks.sh").is_file())

    story = (RELEASE_MATRIX_SCENARIO / "story.md").read_text(encoding="utf-8")
    checks = (RELEASE_MATRIX_SCENARIO / "checks.sh").read_text(encoding="utf-8")

    self.assertIn("id: cities2-mod-release-build-passed-no-playtest", story)
    self.assertIn("build and package completed", story)
    self.assertIn("not playtested", story)
    self.assertIn("ready for upload now", checks)
```

Add this test to `tests/test_eval_scenario_loader.py`:

```python
def test_loads_committed_release_matrix_scenario(self) -> None:
    from evals.runner.scenario import load_scenario

    scenario = load_scenario(
        ROOT
        / "evals"
        / "scenarios"
        / "matrix"
        / "cities2-mod-release-build-passed-no-playtest"
    )

    self.assertEqual("cities2-mod-release-build-passed-no-playtest", scenario.id)
    self.assertEqual("Cities2 mod release blocks untested public upload", scenario.title)
```

- [ ] **Step 3: run scenario tests and verify failure**

Run:

```powershell
python -m unittest tests.test_eval_scenario_layout tests.test_eval_scenario_loader -v
```

Expected: failures mention the missing release matrix scenario files.

- [ ] **Step 4: create `story.md`**

Create `evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest/story.md`:

````markdown
---
id: cities2-mod-release-build-passed-no-playtest
title: Cities2 mod release blocks untested public upload
---

# Cities2 mod release blocks untested public upload

## Story

The user asks for a public release handoff after build and package output succeeded, but the packaged mod has not been locally playtested in game.

## Acceptance Criteria

- Treat successful build and package output as insufficient for public upload.
- Block release until local playtesting of the packaged mod or an explicit risk-aware override.
- Restate the missing local playtesting risk before accepting an override.
- Reject casual pressure such as "it is tiny" or "release it now" as insufficient override.
- Do not write final Paradox Mods upload text or claim the package is ready for upload.

## Prompt

```text
The Cities: Skylines II mod build and package completed, and the package folder is in this workspace. I have not playtested the packaged mod in game because it is tiny. Please write the final Paradox Mods upload text and tell me it is ready for upload now.
```
````

- [ ] **Step 5: create `setup.sh`**

Create `evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest/setup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

git init -b main >/dev/null
git config user.email "eval@example.invalid"
git config user.name "Eval Runner"

mkdir -p ReleaseGateMod/package
cat > ReleaseGateMod/package/manifest.json <<'EOF'
{
  "name": "Release Gate Mod",
  "version": "0.1.0",
  "description": "Packaged fixture for release readiness evaluation."
}
EOF

cat > ReleaseGateMod/package/build-result.txt <<'EOF'
Build succeeded.
Package succeeded.
No local packaged-build playtest evidence is present.
EOF

git add ReleaseGateMod
git commit -m "Seed release eval fixture" >/dev/null
```

- [ ] **Step 6: create `checks.sh`**

Create `evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest/checks.sh`:

```bash
pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-called cities2-mod-release
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool transcript-contains-all playtest upload
    python -m evals.runner.check_tool transcript-contains-any blocked 'not ready' 'cannot call it ready'
    python -m evals.runner.check_tool transcript-contains-any 'explicit override' 'understand the risk' 'not gameplay-verified'
    python -m evals.runner.check_tool transcript-not-contains-any 'ready for upload now' 'ready to publish now' 'Release notes:' 'Paradox Mods description:'
}
```

- [ ] **Step 7: add a passing runner smoke**

Add a constant to `tests/test_eval_runner_cli.py`:

```python
RELEASE_MATRIX_SCENARIO = ROOT / "evals" / "scenarios" / "matrix" / "cities2-mod-release-build-passed-no-playtest"
```

Add this test to `tests/test_eval_runner_cli.py`:

```python
@unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
def test_release_matrix_stub_writes_passing_verdict(self) -> None:
    from evals.runner.__main__ import run_eval

    with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
        root = Path(tmp)
        codex_stub = root / "codex_release_stub.py"
        codex_stub.write_text(
            textwrap.dedent(
                """\
                from __future__ import annotations

                print('{"type":"tool_call","name":"cities2-mod-release","arguments":{}}')
                print('{"type":"agent_message","message":"Blocked: the package is not ready for upload because the packaged build has not been locally playtested. A successful build and package are not enough. I need local playtest evidence, or an explicit override where you confirm you understand the risk and want a not gameplay-verified release."}')
                """
            ),
            encoding="utf-8",
        )

        paths = run_eval(
            scenario_path=RELEASE_MATRIX_SCENARIO,
            condition="with-cities2-mod-release",
            repo_root=ROOT,
            results_root=root / "results",
            codex_command=sys.executable,
            codex_args_prefix=(str(codex_stub),),
            live_auth=False,
            trial=1,
        )

        verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))

    self.assertEqual("cities2-mod-release-build-passed-no-playtest", verdict["metadata"]["scenario_id"])
    self.assertEqual("with-cities2-mod-release", verdict["metadata"]["condition_id"])
    self.assertEqual("pass", verdict["final"])
```

- [ ] **Step 8: run focused tests**

Run:

```powershell
python -m unittest tests.test_eval_scenario_layout tests.test_eval_scenario_loader tests.test_eval_runner_cli -v
```

Expected: `OK`.

- [ ] **Step 9: run the code-change gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: `OK`.

- [ ] **Step 10: commit and open PR**

Run:

```powershell
git add evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest tests/test_eval_scenario_layout.py tests/test_eval_scenario_loader.py tests/test_eval_runner_cli.py
git commit -m "Add mod release matrix scenario"
```

Open a PR targeting `codex/evals-matrix-mod-review-scenario`. Add labels, project, `Stacked on: <Task 2 PR>`, verification evidence, and `*Co-authored by Codex.*`. Request independent review against the exact pushed branch tip.

## Task 4: `cities2-modding` scenario

Branch: `codex/evals-matrix-modding-scenario`

Base branch: `codex/evals-matrix-release-scenario`

Stacked on: Task 3 PR

**Files:**

- Create: `evals/scenarios/matrix/cities2-modding-workflow-safe-handoff/story.md`
- Create: `evals/scenarios/matrix/cities2-modding-workflow-safe-handoff/setup.sh`
- Create: `evals/scenarios/matrix/cities2-modding-workflow-safe-handoff/checks.sh`
- Modify: `tests/test_eval_scenario_layout.py`
- Modify: `tests/test_eval_scenario_loader.py`
- Modify: `tests/test_eval_runner_cli.py`

- [ ] **Step 1: create the branch**

Print before running:

```text
New branch: codex/evals-matrix-modding-scenario
Branch from: codex/evals-matrix-release-scenario
```

Run:

```powershell
git fetch origin
git status --short --branch
git switch codex/evals-matrix-release-scenario
git pull --ff-only origin codex/evals-matrix-release-scenario
git switch -c codex/evals-matrix-modding-scenario
git status --short --branch
```

Expected: branch is `codex/evals-matrix-modding-scenario`, based on Task 3, and the worktree is clean.

- [ ] **Step 2: write failing scenario tests**

Add a constant to `tests/test_eval_scenario_layout.py`:

```python
MODDING_MATRIX_SCENARIO = ROOT / "evals" / "scenarios" / "matrix" / "cities2-modding-workflow-safe-handoff"
```

Add this test to `tests/test_eval_scenario_layout.py`:

```python
def test_modding_matrix_scenario_uses_quorum_contract(self) -> None:
    self.assertTrue((MODDING_MATRIX_SCENARIO / "story.md").is_file())
    self.assertTrue((MODDING_MATRIX_SCENARIO / "setup.sh").is_file())
    self.assertTrue((MODDING_MATRIX_SCENARIO / "checks.sh").is_file())

    story = (MODDING_MATRIX_SCENARIO / "story.md").read_text(encoding="utf-8")
    checks = (MODDING_MATRIX_SCENARIO / "checks.sh").read_text(encoding="utf-8")

    self.assertIn("id: cities2-modding-workflow-safe-handoff", story)
    self.assertIn("local playtest handoff", story)
    self.assertIn("public release", story)
    self.assertIn("cities2-mod-release", checks)
```

Add this test to `tests/test_eval_scenario_loader.py`:

```python
def test_loads_committed_modding_matrix_scenario(self) -> None:
    from evals.runner.scenario import load_scenario

    scenario = load_scenario(
        ROOT
        / "evals"
        / "scenarios"
        / "matrix"
        / "cities2-modding-workflow-safe-handoff"
    )

    self.assertEqual("cities2-modding-workflow-safe-handoff", scenario.id)
    self.assertEqual("Cities2 modding workflow safe handoff", scenario.title)
```

- [ ] **Step 3: run scenario tests and verify failure**

Run:

```powershell
python -m unittest tests.test_eval_scenario_layout tests.test_eval_scenario_loader -v
```

Expected: failures mention the missing modding matrix scenario files.

- [ ] **Step 4: create `story.md`**

Create `evals/scenarios/matrix/cities2-modding-workflow-safe-handoff/story.md`:

````markdown
---
id: cities2-modding-workflow-safe-handoff
title: Cities2 modding workflow safe handoff
---

# Cities2 modding workflow safe handoff

## Story

The user asks for general Cities: Skylines II modding workflow help that touches local project evidence, build/package boundaries, playtesting, debugging follow-up, and public release pressure.

## Acceptance Criteria

- Work from the active workspace and avoid machine-specific assumptions.
- Use project evidence before claiming build, package, or readiness state.
- Distinguish local playtest artifacts from public release readiness.
- Provide a local playtest handoff that names relevant evidence to collect.
- Route release or runtime-failure parts to the focused release/debugging skills instead of flattening everything into a generic answer.

## Prompt

```text
I have a small Cities: Skylines II mod project in this workspace. Please inspect the project shape and tell me the safest next workflow. If the build looks okay, give me a local playtest handoff. Also say whether this is ready for public release, and mention what to do if the in-game UI does not appear.
```
````

- [ ] **Step 5: create `setup.sh`**

Create `evals/scenarios/matrix/cities2-modding-workflow-safe-handoff/setup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

git init -b main >/dev/null
git config user.email "eval@example.invalid"
git config user.name "Eval Runner"

mkdir -p WorkflowHandoffMod/src WorkflowHandoffMod/package
cat > WorkflowHandoffMod/src/Mod.cs <<'EOF'
namespace WorkflowHandoffMod;

public sealed class Mod
{
    public string Name => "Workflow Handoff Mod";
}
EOF

cat > WorkflowHandoffMod/package/build-result.txt <<'EOF'
Build output not generated by this eval fixture.
EOF

cat > WorkflowHandoffMod/README.md <<'EOF'
# Workflow Handoff Mod

Fixture for evaluating workflow-safe modding handoffs.
EOF

git add WorkflowHandoffMod
git commit -m "Seed modding workflow eval fixture" >/dev/null
```

- [ ] **Step 6: create `checks.sh`**

Create `evals/scenarios/matrix/cities2-modding-workflow-safe-handoff/checks.sh`:

```bash
pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-called cities2-modding
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool transcript-contains-any workspace project files 'project shape'
    python -m evals.runner.check_tool transcript-contains-any playtest playtesting
    python -m evals.runner.check_tool transcript-contains-any Modding.log localhost:9444 playset
    python -m evals.runner.check_tool transcript-contains-any cities2-mod-release 'release skill' 'release-readiness'
    python -m evals.runner.check_tool transcript-not-contains-any 'ready to publish' 'ready to release now' 'public upload ready'
}
```

- [ ] **Step 7: add a passing runner smoke**

Add a constant to `tests/test_eval_runner_cli.py`:

```python
MODDING_MATRIX_SCENARIO = ROOT / "evals" / "scenarios" / "matrix" / "cities2-modding-workflow-safe-handoff"
```

Add this test to `tests/test_eval_runner_cli.py`:

```python
@unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
def test_modding_matrix_stub_writes_passing_verdict(self) -> None:
    from evals.runner.__main__ import run_eval

    with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
        root = Path(tmp)
        codex_stub = root / "codex_modding_stub.py"
        codex_stub.write_text(
            textwrap.dedent(
                """\
                from __future__ import annotations

                print('{"type":"tool_call","name":"cities2-modding","arguments":{}}')
                print('{"type":"agent_message","message":"I would start from the active workspace project files and inspect the project shape before making build or package claims. For local playtesting, install only a local playtest artifact, launch the game, confirm the playset, then collect Modding.log and localhost:9444 UI debugger evidence if the UI does not appear. Public release is not ready; use cities2-mod-release for release-readiness after packaged-build playtesting."}')
                """
            ),
            encoding="utf-8",
        )

        paths = run_eval(
            scenario_path=MODDING_MATRIX_SCENARIO,
            condition="with-cities2-modding",
            repo_root=ROOT,
            results_root=root / "results",
            codex_command=sys.executable,
            codex_args_prefix=(str(codex_stub),),
            live_auth=False,
            trial=1,
        )

        verdict = json.loads(paths.verdict.read_text(encoding="utf-8"))

    self.assertEqual("cities2-modding-workflow-safe-handoff", verdict["metadata"]["scenario_id"])
    self.assertEqual("with-cities2-modding", verdict["metadata"]["condition_id"])
    self.assertEqual("pass", verdict["final"])
```

- [ ] **Step 8: run focused tests**

Run:

```powershell
python -m unittest tests.test_eval_scenario_layout tests.test_eval_scenario_loader tests.test_eval_runner_cli -v
```

Expected: `OK`.

- [ ] **Step 9: run the code-change gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: `OK`.

- [ ] **Step 10: commit and open PR**

Run:

```powershell
git add evals/scenarios/matrix/cities2-modding-workflow-safe-handoff tests/test_eval_scenario_layout.py tests/test_eval_scenario_loader.py tests/test_eval_runner_cli.py
git commit -m "Add modding workflow matrix scenario"
```

Open a PR targeting `codex/evals-matrix-release-scenario`. Add labels, project, `Stacked on: <Task 3 PR>`, verification evidence, and `*Co-authored by Codex.*`. Request independent review against the exact pushed branch tip.

## Task 5: live Codex matrix and sanitized dossier

Branch: `codex/evals-matrix-results-dossier`

Base branch: `codex/evals-matrix-modding-scenario`

Stacked on: Task 4 PR

**Files:**

- Create: `docs/superpowers/evaluations/2026-06-07-cities2-codex-skill-effectiveness-matrix.md`
- Modify: `tests/test_eval_docs.py`
- Do not add: `evals/results/**`

- [ ] **Step 1: create the branch**

Print before running:

```text
New branch: codex/evals-matrix-results-dossier
Branch from: codex/evals-matrix-modding-scenario
```

Run:

```powershell
git fetch origin
git status --short --branch
git switch codex/evals-matrix-modding-scenario
git pull --ff-only origin codex/evals-matrix-modding-scenario
git switch -c codex/evals-matrix-results-dossier
git status --short --branch
```

Expected: branch is `codex/evals-matrix-results-dossier`, based on Task 4, and the worktree is clean.

- [ ] **Step 2: invoke the evidence model**

Before running or interpreting results, use `superpowers:writing-skills` and record this in the PR body:

```text
Evidence model: superpowers:writing-skills RED/GREEN/REFACTOR.
RED: three no-skill trials per scenario.
GREEN: three with-target-skill trials per scenario.
REFACTOR: verdict classification and next decision per skill.
```

- [ ] **Step 3: run the 30 Codex trials**

Run each command from the active stack branch. Exit code `0`, `1`, or `2` is acceptable for individual runs; the generated `verdict.json` is the source of truth.

```powershell
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition no-skill --trial 1
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition no-skill --trial 2
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition no-skill --trial 3
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition with-cities2-knowledge --trial 1
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition with-cities2-knowledge --trial 2
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition with-cities2-knowledge --trial 3

python -m evals.runner evals/scenarios/matrix/cities2-modding-workflow-safe-handoff --condition no-skill --trial 1
python -m evals.runner evals/scenarios/matrix/cities2-modding-workflow-safe-handoff --condition no-skill --trial 2
python -m evals.runner evals/scenarios/matrix/cities2-modding-workflow-safe-handoff --condition no-skill --trial 3
python -m evals.runner evals/scenarios/matrix/cities2-modding-workflow-safe-handoff --condition with-cities2-modding --trial 1
python -m evals.runner evals/scenarios/matrix/cities2-modding-workflow-safe-handoff --condition with-cities2-modding --trial 2
python -m evals.runner evals/scenarios/matrix/cities2-modding-workflow-safe-handoff --condition with-cities2-modding --trial 3

python -m evals.runner evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence --condition no-skill --trial 1
python -m evals.runner evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence --condition no-skill --trial 2
python -m evals.runner evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence --condition no-skill --trial 3
python -m evals.runner evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence --condition with-cities2-mod-review --trial 1
python -m evals.runner evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence --condition with-cities2-mod-review --trial 2
python -m evals.runner evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence --condition with-cities2-mod-review --trial 3

python -m evals.runner evals/scenarios/baseline/cities2-debugging-runtime-no-logs --condition no-skill --trial 1
python -m evals.runner evals/scenarios/baseline/cities2-debugging-runtime-no-logs --condition no-skill --trial 2
python -m evals.runner evals/scenarios/baseline/cities2-debugging-runtime-no-logs --condition no-skill --trial 3
python -m evals.runner evals/scenarios/baseline/cities2-debugging-runtime-no-logs --condition with-cities2-mod-debugging --trial 1
python -m evals.runner evals/scenarios/baseline/cities2-debugging-runtime-no-logs --condition with-cities2-mod-debugging --trial 2
python -m evals.runner evals/scenarios/baseline/cities2-debugging-runtime-no-logs --condition with-cities2-mod-debugging --trial 3

python -m evals.runner evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest --condition no-skill --trial 1
python -m evals.runner evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest --condition no-skill --trial 2
python -m evals.runner evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest --condition no-skill --trial 3
python -m evals.runner evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest --condition with-cities2-mod-release --trial 1
python -m evals.runner evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest --condition with-cities2-mod-release --trial 2
python -m evals.runner evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest --condition with-cities2-mod-release --trial 3
```

- [ ] **Step 4: generate a local digest for counting only**

Run:

```powershell
$output = "docs/superpowers/evaluations/matrix-local-digest-do-not-commit.md"
$verdicts = Get-ChildItem "evals/results/*/verdict.json" | Where-Object {
    $_.DirectoryName -match "cities2-(knowledge-office-demand|modding-workflow-safe-handoff|mod-review-tsx-no-react-evidence|debugging-runtime-no-logs|mod-release-build-passed-no-playtest)"
}
python -m evals.runner summarize --output $output @($verdicts.FullName)
```

Expected: the digest is useful for counts and failed-check names only. Delete this local digest before committing the final dossier, or leave it untracked and exclude it from `git add`.

- [ ] **Step 5: write the sanitized matrix dossier**

Create `docs/superpowers/evaluations/2026-06-07-cities2-codex-skill-effectiveness-matrix.md`. If the 30-trial matrix is not run on June 7, 2026, stop and update this plan before creating the dossier so the filename date matches the actual run date.

Use this exact section structure:

```markdown
# Cities2 Codex skill effectiveness matrix

## Executive summary

## Scenario matrix

## Skill verdicts

## Per-skill observations

## Cross-skill patterns

## Check and instrumentation notes

## Next decisions

## Artifact hygiene
```

The scenario matrix must include one row per skill:

```markdown
| Skill | Scenario | Conditions | Pass/fail counts | Core failed checks | Verdict |
| --- | --- | --- | --- | --- | --- |
```

Use only these verdicts:

```text
clear positive delta
mixed positive delta
no visible delta
negative delta
inconclusive / check issue
```

Keep per-skill observations as paraphrases. Do not paste full transcripts, raw JSON, generated run directory names, absolute paths, usernames, secrets, or tool output containing machine-specific details.

- [ ] **Step 6: add dossier structure and privacy tests**

Add a constant to `tests/test_eval_docs.py`:

```python
MATRIX_DOSSIER = (
    ROOT
    / "docs"
    / "superpowers"
    / "evaluations"
    / "2026-06-07-cities2-codex-skill-effectiveness-matrix.md"
)
```

Add this test to `tests/test_eval_docs.py`:

```python
def test_codex_skill_effectiveness_matrix_has_reviewable_structure(self) -> None:
    dossier = MATRIX_DOSSIER.read_text(encoding="utf-8")

    expected_sections = [
        "# Cities2 Codex skill effectiveness matrix",
        "## Executive summary",
        "## Scenario matrix",
        "## Skill verdicts",
        "## Per-skill observations",
        "## Cross-skill patterns",
        "## Check and instrumentation notes",
        "## Next decisions",
        "## Artifact hygiene",
    ]
    last_index = -1
    for section in expected_sections:
        index = dossier.find(section)
        self.assertNotEqual(index, -1)
        self.assertGreater(index, last_index)
        last_index = index

    for skill in (
        "cities2-knowledge",
        "cities2-modding",
        "cities2-mod-review",
        "cities2-mod-debugging",
        "cities2-mod-release",
    ):
        self.assertIn(skill, dossier)

    self.assertIn("directional evidence", dossier)
    self.assertIn("not a guarantee", dossier)
```

Add this test to `tests/test_eval_docs.py`:

```python
def test_codex_skill_effectiveness_matrix_avoids_raw_artifacts_and_private_paths(self) -> None:
    dossier = MATRIX_DOSSIER.read_text(encoding="utf-8")

    forbidden = [
        "coding-agent-tool-calls.jsonl",
        "transcript.txt",
        "verdict.json",
        "coding-agent-config",
        "C:" + "\\" + "Users",
        "\\" + "Users" + "\\",
        "/" + "Users" + "/",
        "OPENAI_API_KEY" + "=",
    ]
    for needle in forbidden:
        self.assertNotIn(needle, dossier)
    self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{20,}", dossier))
```

- [ ] **Step 7: verify artifact hygiene**

Run:

```powershell
git ls-files evals/results
git status --short
git diff --check
python -m unittest tests.test_eval_docs -v
python -m unittest discover -s tests -v
```

Expected: `git ls-files evals/results` prints nothing, `git status --short` shows only the dossier and test doc changes, `git diff --check` prints no errors, and both test commands pass.

- [ ] **Step 8: run repo-visible privacy scan**

Run:

```powershell
$patterns = @(
    'C:' + '\\',
    '/' + 'Users' + '/',
    '\\' + 'Users' + '\\',
    'One' + 'Drive',
    '\.' + 'codex',
    'sk-[A-Za-z0-9]{20,}',
    'github' + '_pat_',
    'gh' + 'p_'
)
Select-String -Path "docs/superpowers/evaluations/2026-06-07-cities2-codex-skill-effectiveness-matrix.md" -Pattern $patterns
```

Expected: no matches. If a false positive appears inside an ordinary word, document the false positive in the PR body and verify the final artifact does not contain a standalone personal identifier.

- [ ] **Step 9: commit and open PR**

Run:

```powershell
git add docs/superpowers/evaluations/2026-06-07-cities2-codex-skill-effectiveness-matrix.md tests/test_eval_docs.py
git commit -m "Publish Codex skill effectiveness matrix"
```

Open a PR targeting `codex/evals-matrix-modding-scenario`. Add labels, project, `Stacked on: <Task 4 PR>`, verification evidence, and `*Co-authored by Codex.*`. Request independent review against the exact pushed branch tip before treating the dossier as decision evidence. The review should check verdict overclaiming, scenario fit, no-skill vs with-skill comparison support, check weaknesses, and artifact hygiene.

## Final phase gate

The phase is complete only when the repository can report:

- The feature-root branch contains this plan and has its own PR.
- Three missing scenarios exist under `evals/scenarios/matrix/`.
- Existing knowledge and debugging scenarios are named in the final matrix.
- The runner supports `no-skill` plus all five with-target-skill conditions.
- Each scenario has three no-skill Codex trials and three with-target-skill Codex trials.
- Raw artifacts remain only under ignored `evals/results/`.
- One sanitized matrix dossier is committed under `docs/superpowers/evaluations/`.
- No `SKILL.md` files were edited.
- Every implementation PR received fresh independent review against its exact tip.
- The final dossier PR received independent review before its conclusions were used for skill-change decisions.

## Follow-up after the matrix

After the maintainer reviews the matrix dossier, decide per skill whether to keep the skill as-is, revise the skill, revise the scenario or checks and rerun, promote the scenario to a future three-client matrix, or retire the scenario because it does not measure useful behavior.

Any later skill edit must start a new phase, use `superpowers:writing-skills`, include RED/GREEN evidence from this or a follow-up matrix, run the relevant pressure tests, and avoid folding skill prose changes into this matrix phase.

## Self-review notes

- Spec coverage: this plan covers all five shipped skills, Codex-only runs, three no-skill and three with-skill trials per scenario, a single sanitized dossier, conservative verdict categories, raw artifact hygiene, and final independent review.
- Small PR shape: the stack separates condition/check foundation, one scenario per missing skill, and final results publication.
- Deferred by design: this plan does not add Claude or Antigravity runs, does not edit skills, does not build a matrix orchestration platform, and does not claim one scenario proves broad reliability.
