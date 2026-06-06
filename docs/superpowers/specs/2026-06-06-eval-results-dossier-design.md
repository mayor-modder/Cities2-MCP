# Eval results dossier design

## Purpose

The first debugging baseline is now merged, but its current summary is still too compressed for a maintainer to understand what actually happened in each run. This phase creates a human-readable results dossier for the `cities2-debugging-runtime-no-logs` baseline so the maintainer can review concrete behavior before deciding whether to edit `cities2-mod-debugging`, refine eval checks, or retire stale quality PRs.

The dossier is evidence, not a fix. It must describe current behavior without turning raw traces into repo-visible artifacts.

## Goals

- Show the actual six-run baseline results in plain English.
- Make each run reviewable without requiring the maintainer to open raw trace files.
- Preserve privacy by committing only curated text.
- Separate likely skill issues from likely eval-check or instrumentation issues.
- Produce a clear next-decision list for the debugging skill and older open PRs.

## Non-goals

- Do not edit any `SKILL.md` files.
- Do not commit `evals/results/`, raw traces, generated workdirs, generated agent homes, full transcripts, local paths, usernames, secrets, or machine-specific output.
- Do not build a general reporting platform before reviewing this first dossier.
- Do not decide the fate of #41, #52, #76, or #77 inside this phase. The dossier may note which PRs look relevant to inspect next.

## Source material

The source material is the six local verdicts from the merged `cities2-debugging-runtime-no-logs` baseline:

- Three `no-skill` Codex trials.
- Three `with-cities2-mod-debugging` Codex trials.

Raw artifacts remain under ignored `evals/results/`. The committed dossier may use only sanitized facts extracted from verdict metadata, check outcomes, normalized assistant messages, and short transcript snippets when needed to explain a failure. Snippets must be minimal and must not include local paths, generated run directory names, usernames, secrets, or raw tool output that is not necessary for the claim.

## Dossier structure

Create a repo-visible Markdown document under `docs/superpowers/evaluations/` with a filename that clearly identifies the debugging baseline and dossier purpose.

The document should use this structure:

1. `# Cities2 debugging runtime-no-logs results dossier`
2. `## Executive summary`
3. `## Run matrix`
4. `## Per-run observations`
5. `## Cross-run patterns`
6. `## Interpretation`
7. `## Next decisions`
8. `## Artifact hygiene`

## Executive summary

The executive summary should answer what happened in a few paragraphs:

- `no-skill` failed all three trials.
- `with-cities2-mod-debugging` passed one of three trials.
- The skill condition improved behavior, but not reliably enough to justify immediate skill edits without reviewing examples.
- The strongest repeated failures were missing concrete handoff and, in some runs, failure to request runtime evidence or avoid unverified fix claims.

The summary must avoid claiming that the skill is defective. It should say what the observed runs suggest and what remains uncertain.

## Run matrix

The run matrix should be a compact table with one row per trial:

- condition
- trial number
- verdict
- failed checks
- one-sentence behavior summary
- reviewer note

The table should be readable on GitHub without horizontal sprawl. If the failed-check list is long, use short check names and explain them below the table.

## Per-run observations

Each run should have a short subsection. The subsection should include:

- verdict and condition
- checks that failed
- checks that passed when relevant to interpretation
- a plain-English description of what the agent did
- at most one or two short sanitized snippets when the behavior cannot be understood from a paraphrase
- a cautious note on what the run suggests

The run sections should not include raw JSON, full transcripts, tool-call dumps, generated paths, or local result paths.

## Cross-run patterns

The cross-run section should group findings by behavior rather than by check implementation:

- Evidence request behavior: whether agents asked for runtime logs or equivalent evidence before diagnosing.
- Edit discipline: whether agents avoided edits before runtime evidence.
- Fix-claim discipline: whether agents claimed a fix without verification.
- Handoff quality: whether agents ended with a concrete next step, requested evidence, or gave a useful handoff.
- Skill effect: what changed between no-skill and with-skill runs.

This section should call out uncertainty. For example, a passed check may prove only that a heuristic matched, not that the whole debugging workflow was excellent.

## Interpretation

The interpretation should remain conservative:

- The baseline is useful because the no-skill and with-skill conditions diverged.
- The with-skill condition still missed the target behavior in two of three runs.
- The most plausible next investigation is handoff quality and unverified-fix behavior.
- Any `cities2-mod-debugging` edits need a follow-up spec and pressure tests.
- Eval-check refinements may be needed if the dossier reveals that checks are too coarse, too brittle, or hard for humans to understand.

## Next decisions

The dossier should end with a concrete decision list:

- Whether to design a focused debugging-skill improvement phase.
- Whether to refine the eval checks or summary tooling before changing the skill.
- Whether #41 is relevant, stale, or should be closed in favor of a new branch based on the baseline.
- Whether #52, #76, and #77 should be unblocked later as independent quality cleanup.

The dossier should not make those decisions itself unless the evidence is unambiguous.

## Artifact hygiene

Before the dossier can be committed, verify:

- `git ls-files evals/results` prints nothing.
- The committed diff contains no raw traces, generated workdirs, generated agent homes, local result paths, usernames, secrets, or machine-specific output.
- The committed doc does not quote long transcript passages.
- `git diff --check` passes.

If the dossier is generated or assisted by a local script, the script output must still be manually reviewed before commit. A helper script can be proposed later if this first dossier shows a stable repeatable format.

## Review plan

The dossier should receive independent review before it is treated as the basis for skill work. Reviewers should check:

- whether each run summary is supported by the local artifacts,
- whether privacy constraints were preserved,
- whether interpretation overclaims,
- whether proposed next decisions follow from the evidence.

If new commits are added after review, review evidence is stale and must be refreshed against the new tip.
