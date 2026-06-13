# Eval results dossier implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repo-visible, privacy-preserving results dossier that makes the six `cities2-debugging-runtime-no-logs` baseline runs understandable to a maintainer.

**Architecture:** Add a focused documentation artifact under `evals/reports/`, guarded by lightweight tests in `tests/test_eval_docs.py`. Use local ignored `evals/results/` artifacts only as source evidence; commit curated prose and short sanitized snippets only.

**Tech Stack:** Markdown, Python `unittest`, existing `evals.runner.summary` verdict data, GitHub PR review workflow.

---

## File structure

- Modify: `tests/test_eval_docs.py`
  - Add constants and tests that require the dossier to exist, include the agreed sections, include all six condition/trial labels, and avoid repo-visible privacy leaks.
- Create: `evals/reports/2026-06-06-cities2-debugging-runtime-no-logs-results-dossier.md`
  - Curated human-readable dossier for the six-run Codex debugging baseline.
- Do not modify: `skills/**/SKILL.md`, `integrations/**/skills/**/SKILL.md`, `plugins/**/skills/**/SKILL.md`
  - This phase records and interprets results only.
- Do not add: `evals/results/**`
  - Raw verdicts, transcripts, traces, generated workdirs, and generated agent homes stay ignored.

## Branching

Use a new task branch from the current stack point after the design/spec branch is merged or otherwise chosen as the parent.

Before creating the branch, print the exact branch name and base:

```powershell
git status --short --branch
git rev-parse HEAD
```

Suggested branch name:

```text
codex/evals-results-dossier
```

If the spec commit `8778fe2` is still unmerged, branch from `codex/evals-results-dossier-spec`. If it has been merged, branch from current `origin/main`.

## Task 1: add dossier guard tests

**Files:**
- Modify: `tests/test_eval_docs.py`
- Create later: `evals/reports/2026-06-06-cities2-debugging-runtime-no-logs-results-dossier.md`

- [ ] **Step 1: Write the failing tests**

Add this constant near the existing `EVALUATION` constant:

```python
DEBUGGING_DOSSIER = (
    ROOT
    / "evals"
    / "reports"
    / "2026-06-06-cities2-debugging-runtime-no-logs-results-dossier.md"
)
```

Add these tests to `EvalDocsTests`:

```python
    def test_debugging_results_dossier_has_reviewable_structure(self) -> None:
        dossier = DEBUGGING_DOSSIER.read_text(encoding="utf-8")

        expected_sections = [
            "# Cities2 debugging runtime-no-logs results dossier",
            "## Executive summary",
            "## Run matrix",
            "## Per-run observations",
            "## Cross-run patterns",
            "## Interpretation",
            "## Next decisions",
            "## Artifact hygiene",
        ]
        for section in expected_sections:
            self.assertIn(section, dossier)

        expected_runs = [
            "no-skill trial 1",
            "no-skill trial 2",
            "no-skill trial 3",
            "with-cities2-mod-debugging trial 1",
            "with-cities2-mod-debugging trial 2",
            "with-cities2-mod-debugging trial 3",
        ]
        for run_label in expected_runs:
            self.assertIn(run_label, dossier)

        self.assertIn("handoff-present", dossier)
        self.assertIn("no-unverified-fix-claim", dossier)
        self.assertIn("requests-runtime-evidence", dossier)
        self.assertIn("current behavior", dossier)
        self.assertIn("does not justify editing `cities2-mod-debugging`", dossier)

    def test_debugging_results_dossier_avoids_raw_artifacts_and_private_paths(self) -> None:
        dossier = DEBUGGING_DOSSIER.read_text(encoding="utf-8")

        forbidden = [
            "<raw tool-call artifact filename>",
            "<raw transcript artifact filename>",
            "<raw summary artifact filename>",
            "generated workdir",
            "generated agent home",
            "C:" + "\\" + "Users",
            "\\" + "Users" + "\\",
            "/" + "Users" + "/",
            "OPENAI_API_KEY" + "=",
        ]
        for needle in forbidden:
            self.assertNotIn(needle, dossier)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{20,}", dossier))
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_eval_docs -v
```

Expected: the new tests fail with `FileNotFoundError` for `2026-06-06-cities2-debugging-runtime-no-logs-results-dossier.md`.

- [ ] **Step 3: Commit the failing-test checkpoint only if the branch policy allows red commits**

Preferred for this repo: do not commit red tests separately. Keep the red output as local TDD evidence and proceed to Task 2.

## Task 2: inspect local baseline artifacts and prepare private notes

**Files:**
- Read only: ignored local run summary artifacts for the six selected results.
- Read only: ignored local assistant-response artifacts referenced by those summaries.
- Do not commit: any generated notes under `evals/results/`.

- [ ] **Step 1: Confirm exactly six Task 7 verdicts are available**

Run a local-only inspection command over ignored `cities2-debugging-runtime-no-logs` result summaries, excluding the trial-99 calibration run.

Expected: six selected results are counted. If fewer than six are present, rerun the missing trials from the merged baseline plan before continuing.

- [ ] **Step 2: Print check outcomes without raw transcripts**

Run a local-only inspection command that prints only condition, trial number, final status, and failed check names from the ignored run summaries.

Expected: six concise lines, with no absolute local paths.

- [ ] **Step 3: Inspect assistant-message excerpts locally**

Run a local-only inspection command that reads assistant-message artifacts referenced by the selected summaries and prints short excerpts for human review.

Expected: local-only excerpts for human inspection. Do not paste this raw output directly into the committed dossier.

- [ ] **Step 4: Write private local notes if helpful**

If the terminal output is too hard to work from, create a local ignored scratch note under `evals/results/debugging-dossier-notes.md`. Keep it untracked.

Run after writing the note:

```powershell
git status --short evals/results
git ls-files evals/results
```

Expected: `git status --short evals/results` may show nothing because the directory is ignored; `git ls-files evals/results` prints nothing.

## Task 3: create the curated results dossier

**Files:**
- Create: `evals/reports/2026-06-06-cities2-debugging-runtime-no-logs-results-dossier.md`
- Test: `tests/test_eval_docs.py`

- [ ] **Step 1: Create the dossier Markdown file**

Create `evals/reports/2026-06-06-cities2-debugging-runtime-no-logs-results-dossier.md` with the required sections from the spec. Use the local inspection output from Task 2 to write final prose on the first pass; do not add scaffold sentences that need later replacement.

The document must start with this exact heading:

```markdown
# Cities2 debugging runtime-no-logs results dossier
```

Include these sections in this order:

```markdown
## Executive summary
## Run matrix
## Per-run observations
## Cross-run patterns
## Interpretation
## Next decisions
## Artifact hygiene
```

The run matrix must include these exact run labels and failed-check sets:

| Run | Verdict | Failed checks |
| --- | --- | --- |
| no-skill trial 1 | fail | `handoff-present`, `post-checks` |
| no-skill trial 2 | fail | `requests-runtime-evidence`, `handoff-present`, `post-checks` |
| no-skill trial 3 | fail | `requests-runtime-evidence`, `handoff-present`, `post-checks` |
| with-cities2-mod-debugging trial 1 | fail | `no-unverified-fix-claim`, `handoff-present`, `post-checks` |
| with-cities2-mod-debugging trial 2 | pass | none |
| with-cities2-mod-debugging trial 3 | fail | `no-unverified-fix-claim`, `handoff-present`, `post-checks` |

Add two more columns to the final table:

- `Behavior summary`: one concise sentence based on the local transcript/verdict inspection.
- `Reviewer note`: one cautious sentence explaining why the behavior matters.

The per-run observation section must include one subsection for each exact run label. Each subsection must contain:

- `Verdict: pass.` or `Verdict: fail.`
- `Failed checks: ...`
- `Observation:` followed by final prose based on local artifacts.
- `What this suggests:` followed by conservative interpretation.

The cross-run section must cover these exact subsections:

```markdown
### Evidence request behavior
### Edit discipline
### Fix-claim discipline
### Handoff quality
### Skill effect
```

The interpretation section must include this exact phrase:

```text
does not justify editing `cities2-mod-debugging`
```

The artifact hygiene section must state:

- raw traces, full transcripts, generated workdirs, generated agent homes, and local result paths remain under gitignored `evals/results/`,
- the dossier contains curated summaries only,
- no `SKILL.md` files were edited for this dossier.

- [ ] **Step 2: Check for leftover scaffold language**

Keep each paragraph on one logical line. Then run:

Run:

```powershell
$patterns = @(
    ('TO' + 'DO'),
    ('TB' + 'D'),
    ('FIX' + 'ME'),
    ('PLACE' + 'HOLDER'),
    'Observation: .*$',
    'What this suggests: .*$'
)
Select-String -Path evals/reports/2026-06-06-cities2-debugging-runtime-no-logs-results-dossier.md -Pattern $patterns -SimpleMatch
```

Expected: no output.

- [ ] **Step 3: Run focused tests and verify the dossier passes**

Run:

```powershell
python -m unittest tests.test_eval_docs -v
```

Expected: all `EvalDocsTests` pass.

## Task 4: verify artifact hygiene and required gates

**Files:**
- Modify: `tests/test_eval_docs.py`
- Create: `evals/reports/2026-06-06-cities2-debugging-runtime-no-logs-results-dossier.md`
- Do not add: `evals/results/**`

- [ ] **Step 1: Verify no raw results are tracked**

Run:

```powershell
git ls-files evals/results
git status --short --branch
```

Expected: `git ls-files evals/results` prints nothing. `git status --short --branch` shows only `tests/test_eval_docs.py` and the new dossier document.

- [ ] **Step 2: Run privacy scan on repo-visible changes**

Run:

```powershell
$privacyPatterns = @(
    ('C:' + '/Users'),
    ('C:' + '\\Users'),
    ('OPENAI_API' + '_KEY='),
    ('auth' + '.json')
)
git diff -- evals/reports/2026-06-06-cities2-debugging-runtime-no-logs-results-dossier.md docs/superpowers/plans/2026-06-06-eval-results-dossier.md docs/superpowers/specs/2026-06-06-eval-results-dossier-design.md | Select-String -Pattern $privacyPatterns -SimpleMatch -CaseSensitive
git diff -- evals/reports/2026-06-06-cities2-debugging-runtime-no-logs-results-dossier.md docs/superpowers/plans/2026-06-06-eval-results-dossier.md docs/superpowers/specs/2026-06-06-eval-results-dossier-design.md | Select-String -Pattern 'sk-[A-Za-z0-9_-]{20,}' -CaseSensitive
```

Expected: no output. If checking exact raw artifact filenames from ignored local results, keep those local-only scan needles out of repo-visible docs.

- [ ] **Step 3: Run whitespace check**

Run:

```powershell
git diff --check
```

Expected: exit 0 and no whitespace errors.

- [ ] **Step 4: Run the full unit suite**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 5: Run plugin payload check**

Run:

```powershell
python -m cities2_mcp.plugin_packages check
```

Expected: `Plugin package payloads are in sync.`

## Task 5: commit, review, and open PR

**Files:**
- Commit: `tests/test_eval_docs.py`
- Commit: `evals/reports/2026-06-06-cities2-debugging-runtime-no-logs-results-dossier.md`

- [ ] **Step 1: Commit the dossier**

Run:

```powershell
git add tests/test_eval_docs.py evals/reports/2026-06-06-cities2-debugging-runtime-no-logs-results-dossier.md
git commit -m "Record debugging baseline results dossier"
```

Expected: one commit with the guard tests and dossier.

- [ ] **Step 2: Request independent Codex review**

Use `superpowers:requesting-code-review` against the exact branch tip. The reviewer should check:

- every run summary is supported by local artifacts,
- no raw artifacts or private paths are committed,
- interpretation does not overclaim,
- the next decisions follow from the evidence.

- [ ] **Step 3: Request external reviews if available**

For pushed PR review, request Claude and Agy reviews. If Agy returns empty stdout, record that it was attempted but do not count it as review evidence.

- [ ] **Step 4: Push and open PR**

Run:

```powershell
git push -u origin codex/evals-results-dossier
gh pr create --base main --head codex/evals-results-dossier --title "[codex] Record debugging baseline results dossier" --body-file -
```

Use this PR body:

```markdown
## Summary

- Add a curated results dossier for the six-run `cities2-debugging-runtime-no-logs` Codex baseline.
- Add eval-doc guard tests for dossier structure and artifact hygiene.
- Record next decisions without editing `cities2-mod-debugging` or committing raw eval artifacts.

## Validation

- `python -m unittest tests.test_eval_docs -v`
- `python -m unittest discover -s tests -v`
- `python -m cities2_mcp.plugin_packages check`
- `git diff --check`
- `git ls-files evals/results`
- Privacy scan on the changed diff

## Review evidence

- Independent Codex review pending.
- Claude review pending.
- Agy review pending.

## Gate

Do not use this dossier as approval for `SKILL.md` edits until the maintainer reviews the evidence and approves a follow-up skill-change phase.

*Co-authored by Codex.*
```

- [ ] **Step 5: Apply required PR metadata**

Run:

```powershell
gh pr edit <PR_NUMBER> --add-label agent-work --add-label "priority: medium" --add-label "area: evals" --add-project skill-quality
```

Expected: PR has `agent-work`, one priority label, one area label, and the Skill Quality project.

- [ ] **Step 6: Update PR body after reviews**

After reviews finish, replace the pending review bullets with exact reviewer names, reviewed commit SHAs, and findings. If new commits land after review, request fresh review against the new tip before marking the PR ready.

## Final gate

The phase is complete only when the repository has:

- a committed results dossier under `evals/reports/`,
- all six baseline runs represented by condition and trial,
- plain-English per-run observations,
- cross-run pattern interpretation,
- next decisions for debugging skill work and old PR triage,
- no `SKILL.md` edits,
- no tracked `evals/results/` artifacts,
- passing unit tests and plugin payload check,
- independent review against the final branch tip.
