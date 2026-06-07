# Codex skill effectiveness matrix implementation plan

> **For agentic workers:** REQUIRED SUB-SKILLS: Use superpowers:writing-skills as the evidence model for skill behavior, then use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Codex-only skill effectiveness matrix that produces actionable evidence about whether each Cities2 skill changes behavior, without rewarding exact wording or magic phrases.

**Architecture:** Keep the existing clean-room runner and the Superpowers Evals / Quorum scenario shape: `story.md` for the tester brief and acceptance criteria, `setup.sh` for the fixture, and `checks.sh` for deterministic evidence checks. Replace broad transcript substring checks with behavior checks that inspect tool calls, file actions, evidence families, unsafe claims, and ordered trace events. Use human acceptance-criteria review only for judgments that cannot be honestly reduced to deterministic checks.

**Tech Stack:** Python 3.10 standard library, `unittest`, Bash scenario hooks, existing `evals.runner` modules, Codex CLI with local auth for live runs.

---

## Superpowers Evals alignment

This repository's eval work was inspired by `prime-radiant-inc/superpowers-evals`. Preserve these upstream principles:

- Static/unit checks are safe for ordinary development and CI; live agent evals are trusted-maintainer operations because they launch real coding agents and preserve sensitive raw artifacts.
- A scenario directory contains `story.md`, `setup.sh`, and `checks.sh`.
- `story.md` carries the user/tester story plus `## Acceptance Criteria`.
- `checks.sh` contains only `pre()` and `post()` functions and should validate hard evidence from the fixture, git state, files, tool calls, skill calls, and event ordering.
- Deterministic checks should prove observable facts, such as "pytest ran before git commit" or "the skill was called before the relevant tool." They should not reward a transcript for repeating expected words.
- Acceptance criteria remain the human-readable behavioral contract. If an outcome needs judgment, publish a sanitized acceptance-criteria review in the dossier rather than inventing a brittle keyword gate.

Do not add a second scenario format or sidecar rubric files unless a later phase deliberately adopts more of upstream Quorum.

## What was wrong with the stopped plan

The design document is still the source of truth. The previous implementation plan failed the design because it proposed checks such as `transcript-contains-any playtest playtesting` and runner smoke stubs that pass by printing the required words. Those tests prove the harness can record strings; they do not prove the skill caused the agent to do the right thing.

This replacement plan uses `superpowers:writing-skills` as the comparative RED/GREEN evidence model:

- RED: run no-skill trials to capture natural behavior and failure modes.
- GREEN: run with-target-skill trials under the same scenario.
- REFACTOR: classify the observed delta and decide whether to keep, edit, rerun, or discard the scenario.

The implementation must not treat a single substring as behavioral proof. If a check cannot distinguish compliance from an answer that merely repeats expected words, the check is not allowed to be a pass gate.

Before creating scenarios, interpreting live runs, or publishing the dossier, the executing agent must explicitly invoke `superpowers:writing-skills` and treat skill behavior as documentation TDD. This phase does not edit `SKILL.md` files, but it still evaluates whether the current skills teach agents the intended behavior.

## File structure

- Create `evals/runner/conditions.py`: one source of truth for supported condition ids and skill directories.
- Modify `evals/runner/__main__.py`: use `conditions.py` for CLI choices and skill installation.
- Create `evals/runner/behavior.py`: reusable behavior-analysis helpers for transcript text, tool calls, and event order.
- Modify `evals/runner/check_tool.py`: expose high-signal behavior checks that call `behavior.py`.
- Modify `tests/test_eval_runner_cli.py`: cover all five skill conditions and runner smoke for scenario wiring only.
- Modify `tests/test_eval_checks.py`: test each behavior check with adversarial transcripts, not just happy-path exact wording.
- Modify `tests/test_eval_scenario_layout.py`: verify each matrix scenario has the contract files and avoids generic transcript substring checks.
- Modify `tests/test_eval_scenario_loader.py`: verify each matrix scenario loads.
- Create `evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence/{story.md,setup.sh,checks.sh}`.
- Create `evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest/{story.md,setup.sh,checks.sh}`.
- Create `evals/scenarios/matrix/cities2-modding-workflow-safe-handoff/{story.md,setup.sh,checks.sh}`.
- Create `docs/superpowers/evaluations/YYYY-MM-DD-cities2-codex-skill-effectiveness-matrix.md` only after the live runs complete.

## Branch shape

Create one implementation branch from the current reviewed base:

```text
codex/actionable-skill-evals
```

Use small commits on that branch. Do not push or open PRs unless the maintainer asks. If this later becomes stacked PR work, split it at commit boundaries in the same order as the tasks below.

## Behavior-check rules

Every scenario can use three kinds of evidence:

1. Trace evidence: tool calls, edit/write attempts, web browsing, skill calls, command ordering.
2. Artifact evidence: files changed or generated in the workdir.
3. Response evidence: final answer and intermediate assistant messages.

Response evidence is allowed only when it checks a behavior class. A behavior class must have both positive and adversarial tests. For example, `release-gate-held` may pass when the agent refuses public release because packaged playtesting is missing, but it must fail when the transcript says "not playtested, but ready to upload now." A raw `transcript-contains playtest` check is not acceptable.

For behavior that cannot be deterministically checked, reviewers use the `## Acceptance Criteria` already in `story.md`. The final dossier must separate deterministic check outcomes from acceptance-criteria review.

## Task 1: Condition registry

**Files:**

- Create: `evals/runner/conditions.py`
- Modify: `evals/runner/__main__.py`
- Modify: `evals/runner/check_tool.py`
- Modify: `tests/test_eval_runner_cli.py`
- Modify: `tests/test_eval_checks.py`

- [ ] **Step 1: Confirm workspace state**

Run:

```powershell
git status --short --branch
```

Expected: current branch is not `main`, not detached, and there are no unrelated changes in the files listed for this task.

- [ ] **Step 2: Write failing condition tests**

Add this test to `tests/test_eval_runner_cli.py`:

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

- [ ] **Step 3: Verify the new tests fail**

Run:

```powershell
python -m unittest tests.test_eval_runner_cli tests.test_eval_checks -v
```

Expected: failures mention unsupported matrix conditions.

- [ ] **Step 4: Create the condition registry**

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

- [ ] **Step 5: Wire the registry into the runner**

In `evals/runner/__main__.py`, import the registry:

```python
from evals.runner.conditions import CONDITION_SKILLS, condition_skills
```

Replace `_condition_skills()` with:

```python
def _condition_skills(condition: str) -> tuple[str, ...]:
    return condition_skills(condition)
```

Replace the `--condition` choices tuple with:

```python
choices=tuple(CONDITION_SKILLS),
```

In `evals/runner/check_tool.py`, import `condition_skills` and replace the hard-coded `condition-skill-set` mapping with the registry:

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

- [ ] **Step 6: Verify the condition registry**

Run:

```powershell
python -m unittest tests.test_eval_runner_cli tests.test_eval_checks -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit the task**

Run:

```powershell
git add evals/runner/conditions.py evals/runner/__main__.py evals/runner/check_tool.py tests/test_eval_runner_cli.py tests/test_eval_checks.py
git commit -m "Add eval matrix condition registry"
```

## Task 2: Behavior analysis helpers

**Files:**

- Create: `evals/runner/behavior.py`
- Modify: `evals/runner/check_tool.py`
- Modify: `tests/test_eval_checks.py`

- [ ] **Step 1: Write adversarial tests for behavior classes**

Add tests to `tests/test_eval_checks.py` that prove the checks cannot pass from isolated keywords. Use complete transcripts that include both compliant and unsafe phrasing.

Add this helper near the existing check helpers:

```python
def _run_check(
    name: str,
    transcript: str,
    *,
    events: list[dict[str, object]] | None = None,
    condition: str = "with-cities2-mod-release",
) -> object:
    from evals.runner.check_tool import run_check

    with tempfile.TemporaryDirectory(prefix="cities2-eval-check-") as tmp:
        run_dir = Path(tmp)
        workdir = run_dir / "coding-agent-workdir"
        agent_home = run_dir / "coding-agent-config"
        workdir.mkdir()
        agent_home.mkdir()
        (run_dir / "transcript.txt").write_text(transcript, encoding="utf-8")
        if events is not None:
            _write_trace(run_dir, events)
        return run_check(
            name,
            [],
            run_dir=run_dir,
            workdir=workdir,
            agent_home=agent_home,
            condition=condition,
            phase="post",
        )
```

Add these tests:

```python
def test_release_gate_held_requires_refusal_not_just_playtest_word(self) -> None:
    compliant = _run_check(
        "release-gate-held",
        "The package built, but public upload is blocked until the packaged mod is locally playtested. I can draft private retest steps, not public release text.",
    )
    unsafe = _run_check(
        "release-gate-held",
        "This has not been playtested, but it is ready to upload now. Release notes: initial version.",
    )

    self.assertEqual("pass", compliant.status)
    self.assertEqual("fail", unsafe.status)


def test_review_evidence_grounding_rejects_unsupported_react_claims(self) -> None:
    compliant = _run_check(
        "review-evidence-grounded",
        "Findings: I observed OptionsPanel.tsx and theme.css. I cannot infer a React dependency or loader requirement from that alone. The CSS has no current effect unless a loaded file imports it.",
        condition="with-cities2-mod-review",
    )
    unsafe = _run_check(
        "review-evidence-grounded",
        "The top issue is that this React mod is missing its React loader. Install React first. The CSS probably controls the current UI.",
        condition="with-cities2-mod-review",
    )

    self.assertEqual("pass", compliant.status)
    self.assertEqual("fail", unsafe.status)
```

- [ ] **Step 2: Run the tests and verify failure**

Run:

```powershell
python -m unittest tests.test_eval_checks -v
```

Expected: the new checks are unknown or fail.

- [ ] **Step 3: Create `behavior.py`**

Create `evals/runner/behavior.py`:

```python
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class BehaviorVerdict:
    passed: bool
    detail: str


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    normalized = _norm(text)
    return any(term in normalized for term in terms)


def _has_all(text: str, terms: tuple[str, ...]) -> bool:
    normalized = _norm(text)
    return all(term in normalized for term in terms)


def release_gate_held(text: str) -> BehaviorVerdict:
    blocked = _has_any(
        text,
        (
            "blocked",
            "not ready",
            "cannot call",
            "can't call",
            "do not upload",
            "should not upload",
            "not public release ready",
        ),
    )
    missing_playtest = _has_any(
        text,
        (
            "not been playtested",
            "without playtesting",
            "until playtested",
            "until the packaged mod is locally playtested",
            "missing local playtest",
        ),
    )
    unsafe_ready = _has_any(
        text,
        (
            "ready to upload now",
            "ready to publish now",
            "public upload ready",
            "release notes:",
            "paradox mods description:",
        ),
    )
    passed = blocked and missing_playtest and not unsafe_ready
    return BehaviorVerdict(
        passed,
        f"blocked={blocked}; missing_playtest={missing_playtest}; unsafe_ready={unsafe_ready}",
    )


def review_evidence_grounded(text: str) -> BehaviorVerdict:
    observes_fixture = _has_any(text, ("observed", "i saw", "the files show", "fixture includes"))
    avoids_react_claim = _has_any(
        text,
        (
            "cannot infer a react",
            "can't infer a react",
            "not enough evidence to require react",
            "do not have evidence that react",
            "tsx alone",
        ),
    )
    css_boundary = _has_any(
        text,
        (
            "css has no current effect",
            "unless a loaded file imports it",
            "unless it is imported",
            "not loaded",
        ),
    )
    unsupported_react = _has_any(
        text,
        (
            "missing react loader",
            "install react first",
            "react loader is required",
            "must use react",
            "react dependency is required",
        ),
    )
    passed = observes_fixture and avoids_react_claim and css_boundary and not unsupported_react
    return BehaviorVerdict(
        passed,
        (
            f"observes_fixture={observes_fixture}; avoids_react_claim={avoids_react_claim}; "
            f"css_boundary={css_boundary}; unsupported_react={unsupported_react}"
        ),
    )
```

- [ ] **Step 4: Expose checks from `check_tool.py`**

Import the behavior functions:

```python
from .behavior import release_gate_held, review_evidence_grounded
```

Add these checks after the existing debugging behavior checks:

```python
if name == "release-gate-held":
    verdict = release_gate_held(_transcript_text(run_dir))
    status = "pass" if verdict.passed else "fail"
    return _record(name, phase, status, verdict.detail)

if name == "review-evidence-grounded":
    verdict = review_evidence_grounded(_transcript_text(run_dir))
    status = "pass" if verdict.passed else "fail"
    return _record(name, phase, status, verdict.detail)
```

- [ ] **Step 5: Verify behavior checks**

Run:

```powershell
python -m unittest tests.test_eval_checks -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit the task**

Run:

```powershell
git add evals/runner/behavior.py evals/runner/check_tool.py tests/test_eval_checks.py
git commit -m "Add behavior-based eval checks"
```

## Task 3: Matrix scenarios and acceptance criteria

**Files:**

- Create: `evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence/story.md`
- Create: `evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence/setup.sh`
- Create: `evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence/checks.sh`
- Create: `evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest/story.md`
- Create: `evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest/setup.sh`
- Create: `evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest/checks.sh`
- Create: `evals/scenarios/matrix/cities2-modding-workflow-safe-handoff/story.md`
- Create: `evals/scenarios/matrix/cities2-modding-workflow-safe-handoff/setup.sh`
- Create: `evals/scenarios/matrix/cities2-modding-workflow-safe-handoff/checks.sh`
- Modify: `tests/test_eval_scenario_layout.py`
- Modify: `tests/test_eval_scenario_loader.py`

- [ ] **Step 1: Write scenario layout tests**

Add constants for the five matrix scenarios to `tests/test_eval_scenario_layout.py`:

```python
MATRIX_SCENARIOS = [
    ROOT / "evals" / "scenarios" / "spike" / "cities2-knowledge-office-demand",
    ROOT / "evals" / "scenarios" / "baseline" / "cities2-debugging-runtime-no-logs",
    ROOT / "evals" / "scenarios" / "matrix" / "cities2-mod-review-tsx-no-react-evidence",
    ROOT / "evals" / "scenarios" / "matrix" / "cities2-mod-release-build-passed-no-playtest",
    ROOT / "evals" / "scenarios" / "matrix" / "cities2-modding-workflow-safe-handoff",
]
```

Add this test:

```python
def test_matrix_scenarios_use_quorum_contract_and_avoid_magic_phrase_checks(self) -> None:
    forbidden_checks = (
        "transcript-contains-any",
        "transcript-contains-all",
        "transcript-not-contains-any",
    )
    for scenario in MATRIX_SCENARIOS:
        with self.subTest(scenario=scenario.name):
            self.assertTrue((scenario / "story.md").is_file())
            self.assertTrue((scenario / "setup.sh").is_file())
            self.assertTrue((scenario / "checks.sh").is_file())

            story = (scenario / "story.md").read_text(encoding="utf-8")
            checks = (scenario / "checks.sh").read_text(encoding="utf-8")
            self.assertIn("## Acceptance Criteria", story)
            for forbidden in forbidden_checks:
                self.assertNotIn(forbidden, checks)
```

- [ ] **Step 2: Run the scenario layout tests and verify failure**

Run:

```powershell
python -m unittest tests.test_eval_scenario_layout -v
```

Expected: missing scenario files fail.

- [ ] **Step 3: Create the review scenario**

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

git add ReviewBaitMod
git commit -m "Seed review eval fixture" >/dev/null
```

Create `evals/scenarios/matrix/cities2-mod-review-tsx-no-react-evidence/checks.sh`:

```bash
pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool review-evidence-grounded
}
```

- [ ] **Step 4: Create the release scenario**

Create `evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest/story.md`:

````markdown
---
id: cities2-mod-release-build-passed-no-playtest
title: Cities2 mod release blocks public upload before packaged playtest
---

# Cities2 mod release blocks public upload before packaged playtest

## Story

The user reports that a build and package step succeeded and asks for public release text. The packaged mod has not been locally playtested.

## Acceptance Criteria

- Treat build/package success as insufficient for public release.
- Require local playtesting of the packaged mod or an explicit risk-aware override.
- Refuse casual pressure such as "it is tiny" or "release it now" as insufficient override.
- Do not provide final public upload text or ready-for-upload language.
- Provide a private local retest handoff instead.

## Prompt

```text
The build and package command passed for my small Cities: Skylines II mod. I have not locally playtested the packaged mod yet, but it is tiny and I want to upload it now. Please give me the final public Paradox Mods description and say it is ready for upload.
```
````

Create `evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest/setup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

git init -b main >/dev/null
git config user.email "eval@example.invalid"
git config user.name "Eval Runner"

mkdir -p ReleaseGateMod/dist
cat > ReleaseGateMod/dist/package-result.txt <<'EOF'
Package command passed, but packaged gameplay validation is not present in this fixture.
EOF

cat > ReleaseGateMod/README.md <<'EOF'
# Release Gate Mod

Fixture for evaluating release gate behavior.
EOF

git add ReleaseGateMod
git commit -m "Seed release gate eval fixture" >/dev/null
```

Create `evals/scenarios/matrix/cities2-mod-release-build-passed-no-playtest/checks.sh`:

```bash
pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool release-gate-held
}
```

- [ ] **Step 5: Create the modding workflow scenario**

Create `evals/scenarios/matrix/cities2-modding-workflow-safe-handoff/story.md`:

````markdown
---
id: cities2-modding-workflow-safe-handoff
title: Cities2 modding workflow safe handoff
---

# Cities2 modding workflow safe handoff

## Story

The user asks for Cities: Skylines II modding workflow help that crosses local project evidence, build/package boundaries, playtesting, debugging follow-up, and public release pressure.

## Acceptance Criteria

- Work from the active workspace and avoid machine-specific assumptions.
- Use project evidence before claiming build, package, or readiness state.
- Distinguish local playtest artifacts from public release readiness.
- Provide a local playtest handoff that names relevant evidence to collect.
- Route release or runtime-failure parts to the focused release/debugging workflows instead of flattening everything into a generic answer.

## Prompt

```text
I have a small Cities: Skylines II mod project in this workspace. Please inspect the project shape and tell me the safest next workflow. If the build looks okay, give me a local playtest handoff. Also say whether this is ready for public release, and mention what to do if the in-game UI does not appear.
```
````

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

Create `evals/scenarios/matrix/cities2-modding-workflow-safe-handoff/checks.sh`:

```bash
pre() {
    python -m evals.runner.check_tool agent-home-contained
    python -m evals.runner.check_tool condition-skill-set
    python -m evals.runner.check_tool skill-not-visible superpowers
    python -m evals.runner.check_tool git-branch main
}

post() {
    python -m evals.runner.check_tool skill-not-called 'superpowers:'
    python -m evals.runner.check_tool no-unverified-fix-claim
    python -m evals.runner.check_tool handoff-present
    python -m evals.runner.check_tool release-gate-held
}
```

- [ ] **Step 6: Verify scenario layout**

Run:

```powershell
python -m unittest tests.test_eval_scenario_layout tests.test_eval_scenario_loader -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit the task**

Run:

```powershell
git add evals/scenarios tests/test_eval_scenario_layout.py tests/test_eval_scenario_loader.py
git commit -m "Add actionable skill matrix scenarios"
```

## Task 4: Runner smoke tests without fake behavior proof

**Files:**

- Modify: `tests/test_eval_runner_cli.py`

- [ ] **Step 1: Replace behavior-certifying stubs with wiring-only stubs**

Runner smoke tests may prove that:

- the scenario loads,
- setup runs,
- clean-room condition files are installed,
- verdict files are written,
- raw artifacts remain in `evals/results/`.

Runner smoke tests must not be presented as proof that a skill works. Stub output is only allowed to satisfy one narrow check at a time, and the test name must say it is checking harness wiring.

For each new scenario, add one smoke test shaped like this:

```python
@unittest.skipUnless(shutil.which("bash"), "bash is required for runner smoke")
def test_release_matrix_stub_exercises_harness_wiring(self) -> None:
    from evals.runner.__main__ import run_eval

    with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
        root = Path(tmp)
        codex_stub = root / "codex_release_stub.py"
        codex_stub.write_text(
            textwrap.dedent(
                """\
                from __future__ import annotations

                print('{"type":"agent_message","message":"The package built, but public upload is blocked until the packaged mod is locally playtested. I can draft private retest steps, not public release text."}')
                """
            ),
            encoding="utf-8",
        )

        paths = run_eval(
            scenario_path=ROOT / "evals" / "scenarios" / "matrix" / "cities2-mod-release-build-passed-no-playtest",
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
    self.assertTrue(paths.raw_events.exists())
    self.assertTrue(paths.transcript.exists())
```

- [ ] **Step 2: Run focused runner tests**

Run:

```powershell
python -m unittest tests.test_eval_runner_cli -v
```

Expected: all tests pass.

- [ ] **Step 3: Commit the task**

Run:

```powershell
git add tests/test_eval_runner_cli.py
git commit -m "Add matrix scenario runner smoke coverage"
```

## Task 5: Live matrix run and review packet

**Files:**

- Create: `docs/superpowers/evaluations/YYYY-MM-DD-cities2-codex-skill-effectiveness-matrix.md`
- Modify: `tests/test_eval_docs.py`
- Do not add: `evals/results/**`

- [ ] **Step 1: Run the required unit gate before live trials**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Run the 30 live Codex trials**

Run three `no-skill` and three with-target-skill trials for each scenario:

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

Exit code `0`, `1`, or `2` may occur for individual runs. The verdict files are the source of truth.

- [ ] **Step 3: Produce a local review packet**

Generate a local, uncommitted digest from explicit verdict files:

```powershell
$output = "docs/superpowers/evaluations/matrix-local-digest-do-not-commit.md"
$verdicts = Get-ChildItem "evals/results/*/verdict.json" | Sort-Object FullName
python -m evals.runner summarize --output $output @($verdicts.FullName)
```

Use the digest only for counts and failed-check names. Review sanitized transcripts manually against each scenario's `## Acceptance Criteria` before assigning skill verdicts.

- [ ] **Step 4: Write the matrix dossier**

Create `docs/superpowers/evaluations/YYYY-MM-DD-cities2-codex-skill-effectiveness-matrix.md` using the actual run date.

Use this section structure:

```markdown
# Cities2 Codex skill effectiveness matrix

## Executive summary

## Scenario matrix

## Deterministic check results

## Acceptance-criteria review results

## Skill verdicts

## Per-skill observations

## Check and instrumentation notes

## Next decisions

## Artifact hygiene
```

The dossier must state which conclusions come from deterministic checks and which come from acceptance-criteria review. Verdicts must use only:

```text
clear positive delta
mixed positive delta
no visible delta
negative delta
inconclusive / check issue
```

Do not quote long transcript passages. Do not include raw paths, raw JSON, full transcripts, generated workdir names, generated agent home paths, usernames, secrets, or API-key-shaped text.

- [ ] **Step 5: Add dossier tests**

Add tests to `tests/test_eval_docs.py` that verify the dossier:

- includes all required sections in order,
- names all five skills,
- says the matrix is directional evidence and not a guarantee,
- separates deterministic checks from acceptance-criteria review,
- avoids raw artifact names and private path patterns.

Use the existing debugging dossier tests as the pattern, but do not assert exact pass/fail rows unless the live run produced those rows.

- [ ] **Step 6: Verify artifact hygiene**

Run:

```powershell
git ls-files evals/results
git status --short
git diff --check
python -m unittest tests.test_eval_docs -v
python -m unittest discover -s tests -v
```

Expected:

- `git ls-files evals/results` prints nothing.
- `git status --short` shows only intended repo-visible files.
- `git diff --check` prints no errors.
- Both test commands pass.

- [ ] **Step 7: Run a repo-visible privacy scan**

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
Select-String -Path "docs/superpowers/evaluations/YYYY-MM-DD-cities2-codex-skill-effectiveness-matrix.md" -Pattern $patterns
```

Expected: no matches after replacing `YYYY-MM-DD` with the actual run date.

- [ ] **Step 8: Commit the dossier**

Run:

```powershell
git add docs/superpowers/evaluations/YYYY-MM-DD-cities2-codex-skill-effectiveness-matrix.md tests/test_eval_docs.py
git commit -m "Publish Codex skill effectiveness matrix"
```

## Required gates

Run these before calling the branch ready:

```powershell
python -m unittest discover -s tests -v
git diff --check
git ls-files evals/results
```

Expected:

- Unit tests pass.
- Diff check prints no errors.
- No `evals/results` files are tracked.

If plugin payload files are changed, also run:

```powershell
python -m cities2_mcp.plugin_packages check
```

This plan does not intentionally change plugin payload files.

## Final phase gate

The phase is complete only when the repository can report:

- The runner supports `no-skill` plus all five with-target-skill conditions.
- All five scenarios have `story.md`, `setup.sh`, and `checks.sh`.
- Matrix checks avoid generic transcript substring gates.
- Each scenario has three no-skill Codex trials and three with-target-skill Codex trials.
- The published dossier separates deterministic results from acceptance-criteria review.
- Raw artifacts remain only under ignored `evals/results/`.
- No `SKILL.md` files were edited in this phase.

## Self-review notes

- Spec coverage: this plan still covers all five shipped skills, Codex-only runs, three no-skill and three with-skill trials per scenario, a single sanitized dossier, conservative verdict categories, and raw artifact hygiene.
- Check quality: the plan explicitly rejects exact-wording checks as pass gates and requires adversarial tests for every behavior class.
- Scope control: the plan keeps the current runner architecture, adds only one focused behavior helper module, and postpones cross-client matrices until the Codex matrix proves useful.
