# Eval Results Digest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a sanitized Markdown digest generator for local eval verdicts so maintainers can review actual eval outcomes without committing raw traces or generated run artifacts.

**Architecture:** Extend `evals.runner.summary` from a count-only helper into a small digest module that loads `verdict.json` files, renders deterministic review-oriented Markdown, and rejects obvious private artifacts before writing. Add a `summarize` CLI subcommand in `evals.runner.__main__` that accepts explicit verdict paths first; keep result-directory discovery and transcript-derived excerpts out of this implementation PR.

**Tech Stack:** Python standard library, `unittest`, existing `evals.runner` dataclasses and JSON verdict schema.

---

## File structure

- Modify `evals/runner/summary.py`: keep `summarize_verdicts()` for compatibility, add `generate_digest()`, `write_digest()`, and privacy guard helpers.
- Modify `evals/runner/__main__.py`: add a `summarize` subcommand while preserving the existing scenario-run command.
- Modify `tests/test_eval_summary.py`: add tests for digest sections, verdict table details, deterministic ordering, and privacy rejection.
- Modify `tests/test_eval_runner_cli.py`: add a CLI test for `python -m evals.runner summarize --output <path> <verdict.json>`.
- Later stacked PR only: add one sanitized committed digest under `docs/superpowers/evaluations/`.

## Task 1: Digest generation from explicit verdict files

**Files:**
- Modify: `tests/test_eval_summary.py`
- Modify: `evals/runner/summary.py`

- [ ] **Step 1: Write the failing digest structure test**

Add this test to `EvalSummaryTests` in `tests/test_eval_summary.py`:

```python
    def test_generates_reviewable_digest_from_verdicts(self) -> None:
        from evals.runner.summary import generate_digest

        with tempfile.TemporaryDirectory(prefix="cities2-eval-summary-") as tmp:
            root = Path(tmp)
            first = root / "first" / "verdict.json"
            second = root / "second" / "verdict.json"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_text(
                json.dumps(
                    {
                        "metadata": {
                            "scenario_id": "cities2-debugging-runtime-no-logs",
                            "condition_id": "with-cities2-mod-debugging",
                            "trial": 2,
                            "backend_name": "codex",
                            "repo_commit": "abc123",
                            "run_started_at": "2026-06-06T18:00:00Z",
                            "skill_checksums": {
                                "cities2-mod-debugging": "sha256:skill",
                            },
                        },
                        "final": "fail",
                        "final_reason": "one or more post-checks failed",
                        "checks": [
                            {
                                "name": "handoff-present",
                                "phase": "post",
                                "status": "fail",
                                "detail": "no concrete next evidence handoff",
                            },
                            {
                                "name": "requests-runtime-evidence",
                                "phase": "post",
                                "status": "pass",
                                "detail": "asked for Modding.log",
                            },
                        ],
                        "trace_path": "coding-agent-tool-calls.jsonl",
                        "transcript_path": "transcript.txt",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            second.write_text(
                json.dumps(
                    {
                        "metadata": {
                            "scenario_id": "cities2-debugging-runtime-no-logs",
                            "condition_id": "no-skill",
                            "trial": 1,
                            "backend_name": "codex",
                            "repo_commit": "abc123",
                            "run_started_at": "2026-06-06T17:00:00Z",
                            "skill_checksums": {},
                        },
                        "final": "pass",
                        "final_reason": "all checks passed",
                        "checks": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            digest = generate_digest([first, second])

        self.assertIn("# Eval results digest", digest)
        self.assertIn("## Short version", digest)
        self.assertIn("Verdicts summarized: 2", digest)
        self.assertIn("| codex | cities2-debugging-runtime-no-logs | no-skill | 1 | pass | none |", digest)
        self.assertIn("| codex | cities2-debugging-runtime-no-logs | with-cities2-mod-debugging | 2 | fail | handoff-present |", digest)
        self.assertIn("- `handoff-present`: fail=1", digest)
        self.assertIn("These results cover only the listed backend runs.", digest)
        self.assertNotIn(str(root), digest)
        self.assertNotIn("coding-agent-tool-calls.jsonl", digest)
        self.assertNotIn("transcript.txt", digest)
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```powershell
python -m unittest tests.test_eval_summary.EvalSummaryTests.test_generates_reviewable_digest_from_verdicts -v
```

Expected: failure or import error because `generate_digest` does not exist.

- [ ] **Step 3: Implement the minimal digest renderer**

In `evals/runner/summary.py`, add:

```python
def _failed_checks(verdict: dict[str, object]) -> list[str]:
    failed: list[str] = []
    for check in verdict.get("checks", []):
        if isinstance(check, dict) and check.get("status") == "fail":
            failed.append(str(check.get("name", "unknown-check")))
    return sorted(set(failed))


def _metadata_value(verdict: dict[str, object], name: str, default: str = "unknown") -> str:
    metadata = verdict.get("metadata")
    if not isinstance(metadata, dict):
        raise TypeError("verdict metadata must be an object")
    value = metadata.get(name)
    return str(value) if value not in (None, "") else default


def _trial(verdict: dict[str, object]) -> int:
    metadata = verdict.get("metadata")
    if not isinstance(metadata, dict):
        raise TypeError("verdict metadata must be an object")
    value = metadata.get("trial", 0)
    if isinstance(value, int):
        return value
    return int(str(value))


def generate_digest(paths: Iterable[Path]) -> str:
    verdicts = [_load(path) for path in paths]
    rows = sorted(
        verdicts,
        key=lambda item: (
            _metadata_value(item, "backend_name"),
            _metadata_value(item, "scenario_id"),
            _metadata_value(item, "condition_id"),
            _trial(item),
        ),
    )
    check_counts: dict[str, Counter[str]] = defaultdict(Counter)
    backends: set[str] = set()
    commits: set[str] = set()
    checksums: set[str] = set()
    run_dates: set[str] = set()

    for verdict in rows:
        metadata = verdict["metadata"]
        if not isinstance(metadata, dict):
            raise TypeError("verdict metadata must be an object")
        backend = metadata.get("backend_name")
        if isinstance(backend, str) and backend:
            backends.add(backend)
        commit = metadata.get("repo_commit")
        if isinstance(commit, str) and commit:
            commits.add(commit)
        run_started_at = metadata.get("run_started_at")
        if isinstance(run_started_at, str) and len(run_started_at) >= 10:
            run_dates.add(run_started_at[:10])
        skill_checksums = metadata.get("skill_checksums")
        if isinstance(skill_checksums, dict):
            for value in skill_checksums.values():
                if isinstance(value, str):
                    checksums.add(value)
        for check in verdict.get("checks", []):
            if isinstance(check, dict):
                check_counts[str(check.get("name", "unknown-check"))][
                    str(check.get("status", "unknown"))
                ] += 1

    lines = [
        "# Eval results digest",
        "",
        "## Short version",
        "",
        f"Verdicts summarized: {len(rows)}",
        f"Backends: {', '.join(sorted(backends)) if backends else 'unknown'}",
        f"Run dates: {', '.join(sorted(run_dates)) if run_dates else 'unknown'}",
        "",
        "These results cover only the listed backend runs.",
        "",
        "## Run matrix",
        "",
        f"Repository commits: {', '.join(sorted(commits)) if commits else 'unknown'}",
        f"Skill checksums: {', '.join(sorted(checksums)) if checksums else 'none'}",
        "",
        "## Verdict table",
        "",
        "| Backend | Scenario | Condition | Trial | Final | Failed checks |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for verdict in rows:
        failed = ", ".join(_failed_checks(verdict)) or "none"
        lines.append(
            "| "
            f"{_metadata_value(verdict, 'backend_name')} | "
            f"{_metadata_value(verdict, 'scenario_id')} | "
            f"{_metadata_value(verdict, 'condition_id')} | "
            f"{_trial(verdict)} | "
            f"{str(verdict.get('final', 'unknown'))} | "
            f"{failed} |"
        )
    lines.extend(["", "## Failure patterns", ""])
    if check_counts:
        for check_name, counter in sorted(check_counts.items()):
            parts = [
                f"{status}={counter[status]}"
                for status in ("pass", "fail", "indeterminate")
                if counter[status]
            ]
            lines.append(f"- `{check_name}`: {'; '.join(parts)}")
    else:
        lines.append("- No check records were present.")
    lines.extend(
        [
            "",
            "## Representative behavior",
            "",
            "No raw transcripts are included in this digest.",
            "",
            "## Interpretation",
            "",
            "This digest reports deterministic verdict data and grouped check outcomes. Human interpretation should remain tied to the listed runs and should not generalize to untested clients.",
            "",
            "## Follow-up status",
            "",
            "No follow-up status was provided by the digest generator.",
            "",
            "## Privacy note",
            "",
            "Raw traces, transcripts, generated agent homes, and generated workdirs remain local under gitignored `evals/results/`.",
            "",
        ]
    )
    return "\n".join(lines)
```

- [ ] **Step 4: Run the focused test and verify it passes**

Run:

```powershell
python -m unittest tests.test_eval_summary.EvalSummaryTests.test_generates_reviewable_digest_from_verdicts -v
```

Expected: one passing test.

- [ ] **Step 5: Run all summary tests**

Run:

```powershell
python -m unittest tests.test_eval_summary -v
```

Expected: all `EvalSummaryTests` pass.

- [ ] **Step 6: Commit Task 1**

Run:

```powershell
git add evals/runner/summary.py tests/test_eval_summary.py
git commit -m "Add eval digest rendering"
```

## Task 2: Privacy rejection before writing digest files

**Files:**
- Modify: `tests/test_eval_summary.py`
- Modify: `evals/runner/summary.py`

- [ ] **Step 1: Write failing privacy tests**

Add these tests to `EvalSummaryTests`:

```python
    def test_write_digest_rejects_private_paths(self) -> None:
        from evals.runner.summary import write_digest

        with tempfile.TemporaryDirectory(prefix="cities2-eval-summary-") as tmp:
            output = Path(tmp) / "digest.md"

            with self.assertRaisesRegex(ValueError, "private artifact"):
                write_digest("leaked C:\\\\Users\\\\Example\\\\.codex\\\\auth.json\n", output)

        self.assertFalse(output.exists())

    def test_write_digest_writes_safe_text(self) -> None:
        from evals.runner.summary import write_digest

        with tempfile.TemporaryDirectory(prefix="cities2-eval-summary-") as tmp:
            output = Path(tmp) / "digest.md"

            write_digest("# Eval results digest\n\nsafe\n", output)

            self.assertEqual("# Eval results digest\n\nsafe\n", output.read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run privacy tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_eval_summary.EvalSummaryTests.test_write_digest_rejects_private_paths tests.test_eval_summary.EvalSummaryTests.test_write_digest_writes_safe_text -v
```

Expected: import error because `write_digest` does not exist.

- [ ] **Step 3: Implement privacy guard and writer**

In `evals/runner/summary.py`, add:

```python
_PRIVATE_PATTERNS = (
    re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\s`|]+", re.IGNORECASE),
    re.compile(r"/home/[^\\s`|]+", re.IGNORECASE),
    re.compile(r"/Users/[^\\s`|]+", re.IGNORECASE),
    re.compile(r"\\bauth\\.json\\b", re.IGNORECASE),
    re.compile(r"coding-agent-config", re.IGNORECASE),
)


def validate_digest_text(text: str) -> None:
    for pattern in _PRIVATE_PATTERNS:
        if pattern.search(text):
            raise ValueError(f"digest contains private artifact: {pattern.pattern}")


def write_digest(text: str, output: Path) -> None:
    validate_digest_text(text)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
```

Also add `import re` at the top of `evals/runner/summary.py`.

- [ ] **Step 4: Run privacy tests and verify they pass**

Run:

```powershell
python -m unittest tests.test_eval_summary.EvalSummaryTests.test_write_digest_rejects_private_paths tests.test_eval_summary.EvalSummaryTests.test_write_digest_writes_safe_text -v
```

Expected: both tests pass.

- [ ] **Step 5: Run all summary tests**

Run:

```powershell
python -m unittest tests.test_eval_summary -v
```

Expected: all `EvalSummaryTests` pass.

- [ ] **Step 6: Commit Task 2**

Run:

```powershell
git add evals/runner/summary.py tests/test_eval_summary.py
git commit -m "Reject private eval digest artifacts"
```

## Task 3: `summarize` CLI subcommand

**Files:**
- Modify: `tests/test_eval_runner_cli.py`
- Modify: `evals/runner/__main__.py`

- [ ] **Step 1: Write failing CLI test**

Add this test to `EvalRunnerCliTests` in `tests/test_eval_runner_cli.py`:

```python
    def test_summarize_subcommand_writes_digest(self) -> None:
        from evals.runner.__main__ import main

        with tempfile.TemporaryDirectory(prefix="cities2-eval-runner-") as tmp:
            root = Path(tmp)
            verdict = root / "verdict.json"
            output = root / "digest.md"
            verdict.write_text(
                json.dumps(
                    {
                        "metadata": {
                            "scenario_id": "cities2-debugging-runtime-no-logs",
                            "condition_id": "no-skill",
                            "trial": 1,
                            "backend_name": "codex",
                            "repo_commit": "abc123",
                            "run_started_at": "2026-06-06T17:00:00Z",
                            "skill_checksums": {},
                        },
                        "final": "pass",
                        "final_reason": "all checks passed",
                        "checks": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            status = main(["summarize", "--output", str(output), str(verdict)])

            digest = output.read_text(encoding="utf-8")

        self.assertEqual(0, status)
        self.assertIn("# Eval results digest", digest)
        self.assertIn("Verdicts summarized: 1", digest)
```

- [ ] **Step 2: Run CLI test and verify it fails**

Run:

```powershell
python -m unittest tests.test_eval_runner_cli.EvalRunnerCliTests.test_summarize_subcommand_writes_digest -v
```

Expected: argument parsing failure because `summarize` is not a supported subcommand.

- [ ] **Step 3: Add subcommand parsing**

In `evals/runner/__main__.py`, import digest helpers:

```python
from evals.runner.summary import generate_digest, write_digest
```

Then refactor `main()` so it recognizes `summarize` before the existing run command:

```python
def _run_summarize_command(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.runner summarize")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("verdicts", nargs="+", type=Path)
    args = parser.parse_args(argv)
    write_digest(generate_digest(args.verdicts), args.output)
    print(args.output)
    return 0


def _run_eval_command(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.runner")
    parser.add_argument("scenario_path", type=Path)
```

Move the remaining existing run-command parser arguments and `run_eval()` call from `main()` into `_run_eval_command()` without changing their behavior. Make `main()` dispatch:

```python
def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "summarize":
        return _run_summarize_command(argv[1:])
    return _run_eval_command(argv)
```

Also add `import sys` near the existing imports.

- [ ] **Step 4: Run CLI test and verify it passes**

Run:

```powershell
python -m unittest tests.test_eval_runner_cli.EvalRunnerCliTests.test_summarize_subcommand_writes_digest -v
```

Expected: one passing test.

- [ ] **Step 5: Run runner and summary tests**

Run:

```powershell
python -m unittest tests.test_eval_summary tests.test_eval_runner_cli -v
```

Expected: all tests in both modules pass.

- [ ] **Step 6: Commit Task 3**

Run:

```powershell
git add evals/runner/__main__.py tests/test_eval_runner_cli.py
git commit -m "Add eval digest CLI"
```

## Task 4: Documentation and final verification

**Files:**
- Modify: `evals/README.md`

- [ ] **Step 1: Document the digest command**

Add this section to `evals/README.md` after the existing runner CLI examples:

```markdown
## Summarize local verdicts

Raw run artifacts remain under gitignored `evals/results/`. To create a committed review artifact, generate a sanitized digest from explicit verdict files:

```powershell
$output = "docs/superpowers/evaluations/2026-06-06-cities2-debugging-runtime-no-logs-digest.md"
$verdict = Get-ChildItem "evals/results/cities2-debugging-runtime-no-logs-with-cities2-mod-debugging-trial-*/verdict.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
python -m evals.runner summarize --output $output $verdict
```

Review the generated digest before committing it. The digest writer rejects obvious private paths and generated agent config markers, but it is not a substitute for the repository privacy review.
```

- [ ] **Step 2: Run focused docs and runner tests**

Run:

```powershell
python -m unittest tests.test_eval_summary tests.test_eval_runner_cli tests.test_eval_docs -v
```

Expected: all selected tests pass.

- [ ] **Step 3: Run required code gate**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 4: Run package gate**

Run:

```powershell
python -m cities2_mcp.plugin_packages check
```

Expected: package check passes or reports no plugin payload drift. This PR should not change plugin payloads.

- [ ] **Step 5: Run privacy and artifact checks**

Run:

```powershell
git status --short --branch
git diff --stat codex/eval-results-digest-plan..HEAD
git diff --name-only codex/eval-results-digest-plan..HEAD
git diff --check
git diff --cached --check
```

Expected: only runner, tests, and `evals/README.md` files are changed; no `evals/results/` paths are staged.

- [ ] **Step 6: Commit Task 4**

Run:

```powershell
git add evals/README.md docs/superpowers/plans/2026-06-06-eval-results-digest.md
git commit -m "Document eval digest workflow"
```

## Task 5: Open stacked implementation PR

**Files:**
- No code changes expected.

- [ ] **Step 1: Push the implementation branch**

Run:

```powershell
git push -u origin codex/eval-results-digest-impl
```

- [ ] **Step 2: Create PR against the plan branch**

Create the PR with:

```text
Base: codex/eval-results-digest-plan
Head: codex/eval-results-digest-impl
Title: [codex] Add eval results digest generation
```

The body must include:

```markdown
Stacked on: #113

## Summary

Adds sanitized eval digest generation from explicit verdict files, a `python -m evals.runner summarize` command, tests, and README usage notes.

## Validation

- `python -m unittest tests.test_eval_summary tests.test_eval_runner_cli tests.test_eval_docs -v`
- `python -m unittest discover -s tests -v`
- `python -m cities2_mcp.plugin_packages check`
- `git diff --check`

*Co-authored by Codex.*
```

Apply labels `agent-work`, `priority: medium`, and `area: evals`, and attach the PR to the `skill-quality` project.

- [ ] **Step 3: Run the PR-shape audit**

Run:

```powershell
git status --short --branch
git log --oneline codex/eval-results-digest-plan..HEAD
$pr = gh pr view --json number --jq .number
gh pr view $pr --json baseRefName,headRefName,commits,files,isDraft
gh pr diff $pr --name-only
git diff --stat codex/eval-results-digest-plan..HEAD
```

Expected: base is `codex/eval-results-digest-plan`; files are limited to runner code, tests, and `evals/README.md`; diff size remains reviewable.

## Task 6: First results digest PR

Do this only after the implementation PR is reviewed or the maintainer explicitly asks to stack the digest immediately.

**Files:**
- Create: `docs/superpowers/evaluations/YYYY-MM-DD-cities2-debugging-runtime-no-logs-digest.md`

- [ ] **Step 1: Print branch point**

Use:

```text
New branch: codex/eval-results-digest-first-report
Branch from: codex/eval-results-digest-impl
```

- [ ] **Step 2: Generate digest from selected local verdicts**

Run the new CLI with explicit verdict paths selected by the maintainer from local `evals/results/`.

- [ ] **Step 3: Review generated digest manually**

Check that it contains no raw transcript, trace path, generated agent home, local absolute path, username, token, or machine-specific output.

- [ ] **Step 4: Commit and open stacked PR**

Open the PR against `codex/eval-results-digest-impl` with:

```text
Stacked on: <implementation PR number>
```

Use labels `agent-work`, `priority: medium`, and `area: evals`, and attach it to `skill-quality`.
