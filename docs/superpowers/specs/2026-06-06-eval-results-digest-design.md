# Eval results digest design

## Purpose

Cities2-MCP now has a clean-room eval runner, a committed baseline dossier, and at least one skill change driven by real eval evidence, but the results are still difficult for a maintainer to review.

The next phase should make eval outcomes visible without committing raw traces, generated agent homes, transcripts, local paths, credentials, or machine-specific output. The desired artifact is a sanitized digest that turns local `evals/results/` runs into a concise Markdown review document.

## Problem

Raw eval output is intentionally gitignored under `evals/results/`. That is correct for privacy and repository hygiene, but it leaves a review gap: a maintainer can see final pass counts in a committed evaluation note, yet still struggle to answer what actually happened, which behavior changed, and whether a follow-up skill edit was justified.

The current `evals.runner.summary` helper reports counts from `verdict.json` files. Counts are useful, but they are not enough for review because they do not explain failure patterns, trial-level behavior, or what evidence is safe to quote or summarize.

## Goals

- Define a committed digest format for sanitized eval results.
- Preserve the existing rule that raw traces, transcripts, generated homes, and generated workdirs remain uncommitted.
- Make the result of a run matrix understandable from the repository alone.
- Separate objective verdict data from human interpretation.
- Record which real agent backend and condition each digest covers.
- Support later comparison across `codex`, `claude`, and `agy` without designing those adapters in this phase.
- Keep this as a documentation and runner-output improvement, not a skill behavior change.

## Non-goals

- Do not commit raw eval traces or generated `evals/results/` artifacts.
- Do not add new eval scenarios in this phase.
- Do not edit any `SKILL.md` files in this phase.
- Do not claim local runs are representative of all supported clients unless those clients were actually run.
- Do not introduce LLM-as-judge grading yet.
- Do not redesign the runner isolation model.

## Digest location

Committed digests should live under `evals/reports/` because they are maintainer-facing evaluation records, not runnable eval assets.

Use a filename that records the date the digest is written and the scenario or phase being summarized:

```text
evals/reports/YYYY-MM-DD-<scenario-or-phase>-digest.md
```

The digest may link to repo-relative scenario paths and runner files. It must not include absolute local checkout paths, user home paths, generated result directory names that embed local timing details unless needed for maintainer-local lookup, or credential-bearing file names.

## Digest structure

Each digest should use these sections:

- `Short version`: a plain-English answer to what happened.
- `Run matrix`: scenario, backend, conditions, trial count, repository commit, skill checksums, and run date.
- `Verdict table`: one row per condition and trial with final status and failed checks.
- `Failure patterns`: grouped behavior patterns across trials, stated without raw transcript dumps.
- `Representative behavior`: short sanitized paraphrases or excerpts when they are necessary to show why a check passed or failed.
- `Interpretation`: what the results do and do not justify.
- `Follow-up status`: whether any follow-up branch, PR, or skill change exists, and whether it has been independently reviewed.
- `Privacy note`: a reminder that raw outputs remain local and gitignored.

The digest should be short enough to read in one pass. If it needs more than a few pages, the runner should produce multiple scenario-specific digests instead of one sprawling report.

## Allowed content

A digest may include:

- Scenario ids and repo-relative scenario paths.
- Backend names such as `codex`, `claude`, or `agy`.
- Condition ids such as `no-skill` or `with-cities2-mod-debugging`.
- Trial numbers.
- Repository commit hashes.
- Skill file checksums.
- Final verdicts and deterministic check statuses.
- Sanitized failure reasons.
- Sanitized excerpts of agent responses when they are short, necessary, and free of private data.
- Human interpretation that is clearly labeled as interpretation.
- Links to PRs, issues, and committed docs that explain follow-up work.

## Disallowed content

A digest must not include:

- Full transcripts.
- Raw JSONL traces.
- Generated agent home contents.
- Generated workdir contents beyond committed fixture paths.
- Local absolute paths.
- Usernames, home-directory paths, tokens, auth files, machine ids, or local cache paths.
- Secret-bearing filenames or snippets from generated config directories.
- Claims about clients or models that were not actually run.

If a useful behavior example cannot be safely excerpted, summarize it in neutral prose instead.

## Runner support

The existing `evals.runner.summary` helper should grow into a digest generator rather than staying count-only.

The proposed command shape is:

```powershell
python -m evals.runner summarize --output evals/reports/YYYY-MM-DD-<scenario>-digest.md <verdict paths or result dirs>
```

The implementation may start smaller if that is easier to review. A first step can accept explicit `verdict.json` paths and produce only the required sections that can be derived from verdict metadata and check details. Later steps can add result-directory discovery, transcript-derived behavior snippets, and multi-backend comparison tables.

Generated digest output should be deterministic enough for review. Sort scenarios, conditions, trials, checks, and commits consistently.

## Privacy checks

Before writing a digest, the generator should scan candidate text for obvious private artifacts:

- Windows home paths.
- Unix home paths.
- absolute checkout paths.
- known auth filenames such as `auth.json`.
- generated agent config directory names.
- raw result file names that imply credential-bearing locations.

The first implementation can fail closed with a clear error if risky text appears in the generated digest. It does not need to be a perfect secret scanner, but it should prevent the most obvious mistakes.

Repository-visible artifacts still require the normal agent privacy review before commit.

## Relationship to current baseline

The first target input is the real Codex `cities2-debugging-runtime-no-logs` baseline and retest work already run locally.

Those runs currently prove only Codex behavior. The digest should say that plainly. It should not imply that Claude or Agy were evaluated until their runs exist and their results are summarized.

The previous committed baseline note remains valid as a historical record. This phase should not rewrite it unless the maintainer explicitly asks for a reflow or replacement. Instead, add a new digest that is easier to review and can become the pattern for future eval summaries.

## Success criteria

This phase is complete when the repository has:

- A committed spec for the digest format and privacy contract.
- A small runner or documentation update that can create a sanitized digest from local verdicts.
- Tests covering deterministic digest generation and privacy rejection.
- One committed digest for the existing debugging baseline or retest, based only on sanitized local results.
- Verification that no raw `evals/results/` artifacts were committed.

## Recommended implementation shape

Use stacked PRs:

1. Root spec PR from `main` with this design only.
2. Implementation PR stacked on the spec branch that adds digest generation and tests.
3. Results PR stacked on the implementation branch that commits the first sanitized digest.

This keeps the review surface small and avoids another oversized PR. The implementation PR should stay runner-focused and must not edit `SKILL.md` files.
