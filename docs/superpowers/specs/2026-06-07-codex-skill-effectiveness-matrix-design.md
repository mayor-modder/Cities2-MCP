# Codex skill effectiveness matrix design

## Purpose

Cities2-MCP now has a working Codex eval runner, one published debugging results dossier, and several skill-quality improvements that are protected by pressure-test text and portability checks. That proves the repository can express and preserve desired skill behavior, but it does not yet prove that all shipped skills measurably change Codex behavior.

This phase creates a Codex-only directional effectiveness matrix for all five shipped Cities2 skills. The matrix should answer whether each skill produces a useful behavioral delta compared with a no-skill baseline, while publishing sanitized results that a maintainer can review without opening raw traces.

## Governing evidence model

This phase uses `superpowers:writing-skills` as the governing evidence model. Skill behavior is treated as documentation TDD:

- RED: no-skill trials establish the baseline behavior and failure modes for the same scenario.
- GREEN: with-skill trials show whether installing the target skill improves behavior.
- REFACTOR: the published result classifies whether to keep the skill as-is, revise the skill, revise the scenario or checks, or gather more evidence.

The matrix must not treat a skill edit as justified merely because a pressure test exists or a rule appears in `SKILL.md`. A proposed skill edit needs comparative evidence showing either that no-skill behavior fails in a relevant way, with-skill behavior still fails, or the existing skill creates an unintended negative effect.

## Superpowers Evals alignment

This repository's eval work is inspired by `prime-radiant-inc/superpowers-evals`. The matrix should preserve the same scenario shape unless a later phase deliberately adopts more of upstream Quorum:

- Scenario directories use `story.md`, `setup.sh`, and `checks.sh`.
- `story.md` owns the tester story, prompt, and `## Acceptance Criteria`.
- `setup.sh` creates the reproducible fixture.
- `checks.sh` proves hard evidence from the fixture, git state, files, tool calls, skill calls, and event ordering.
- Static runner and scenario checks are safe for ordinary development; live Codex evals are trusted-maintainer operations because they launch real agents and preserve sensitive raw artifacts.
- Acceptance criteria remain the behavioral contract. When a conclusion needs judgment, publish a sanitized acceptance-criteria review instead of converting it into a brittle keyword gate.

## Goals

- Cover all five shipped skills: `cities2-knowledge`, `cities2-modding`, `cities2-mod-review`, `cities2-mod-debugging`, and `cities2-mod-release`.
- Use Codex only for the first effectiveness matrix.
- Run one representative scenario per skill.
- Run three no-skill trials and three with-target-skill trials per scenario.
- Publish one sanitized, repo-visible matrix dossier under `evals/reports/`.
- Classify each skill's observed delta with conservative plain-English verdicts.
- Preserve raw traces and generated run artifacts under ignored `evals/results/`.

## Non-goals

- Do not run Claude or Antigravity in this phase.
- Do not edit `SKILL.md` files as part of the matrix phase.
- Do not build a large matrix orchestration platform before the first five-skill result is reviewed.
- Do not commit raw eval traces, full transcripts, generated workdirs, generated agent homes, local paths, usernames, secrets, or machine-specific output.
- Do not claim a skill is generally proven reliable from one scenario.

## Scenario set

Each shipped skill gets one representative scenario. The scenario should be narrow enough for automated checks to judge, but realistic enough that the skill has a meaningful chance to change behavior.

### `cities2-knowledge`

Scenario intent: a gameplay or city-management question that benefits from Cities2-MCP source lookup, such as office demand, service coverage, or known mechanics confusion.

Expected skilled behavior:

- Use the local Cities2-MCP knowledge sources instead of guessing from general memory.
- Check source status or otherwise establish available source evidence.
- Search with compact terms.
- Answer in plain English with a compact source note.
- Avoid live web browsing unless the user explicitly asks for current external information.

Primary delta: the skilled condition should show more source-grounded and less generic gameplay advice than no-skill trials.

### `cities2-modding`

Scenario intent: a user asks to scaffold or adjust a CS2 mod workflow where local workspace boundaries, install/build prerequisites, and safe handoff matter.

Expected skilled behavior:

- Work from the active workspace and avoid machine-specific assumptions.
- Use workflow tooling or project evidence before giving build/package claims.
- Keep local packaging/install advice distinct from public release readiness.
- Mention relevant review, debugging, or release follow-up skills when the task crosses those boundaries.

Primary delta: the skilled condition should produce a more repo-aware, workflow-safe modding handoff than no-skill trials.

### `cities2-mod-review`

Scenario intent: review a small mod or scaffold with tempting but unproven framework, loader, packaging, or CSS assumptions.

Expected skilled behavior:

- Lead with findings ordered by severity.
- Distinguish observed project facts, MCP/project documentation support, and inferred recommendations.
- Avoid naming React, loader requirements, runtime requirements, or packaging requirements without project or source evidence.
- Treat unloaded CSS as no current effect, with future styling risk conditional on loading.

Primary delta: the skilled condition should reduce plausible but unsupported review claims compared with no-skill trials.

### `cities2-mod-debugging`

Scenario intent: a CS2 mod builds, but in-game behavior fails and the user has not provided runtime logs, installed package evidence, playset/load state, or UI debugger evidence.

Expected skilled behavior:

- Avoid source edits before runtime evidence.
- Mark the root cause as unverified when evidence is insufficient.
- Ask for the smallest useful runtime evidence.
- Provide a concrete log, package-state, playset, UI-debugger, or playtesting handoff.
- Avoid broad installed-mod inspection unless explicitly authorized by the scenario.

Primary delta: the skilled condition should improve runtime-evidence handoff discipline compared with no-skill trials.

### `cities2-mod-release`

Scenario intent: a build/package step succeeds, but the packaged mod has not been locally playtested and the user asks for release/upload text or a ready-for-upload claim.

Expected skilled behavior:

- Treat successful build/package output as insufficient for public release.
- Require local playtesting of the packaged mod or an explicit risk-aware override.
- Restate the missing local playtesting risk before accepting an override.
- Reject casual pressure such as "it is tiny" or "release it now" as insufficient override.
- Avoid creating a distribution package, final upload text, or ready-for-public-upload handoff without playtesting or explicit override.

Primary delta: the skilled condition should enforce the release gate more reliably than no-skill trials.

## Trial matrix

For each scenario, run six Codex trials:

| Condition | Trials | Skill installation |
| --- | ---: | --- |
| no-skill | 3 | no Cities2 skill installed |
| with-target-skill | 3 | only the target skill installed, plus required MCP/tool configuration |

Do not install all five skills during a with-skill trial. Each scenario should test the target skill's marginal effect in isolation.

If a scenario requires MCP access, both conditions may receive the same MCP server configuration so the measured difference is the skill text, not tool availability. The dossier must state which tools were available in each condition.

## Checks and verdicts

Each scenario should use checks that map to observable behavior rather than broad subjective quality. Checks may inspect normalized assistant text, tool-call records, generated files, and post-run artifacts where appropriate.

Deterministic pass gates should prove behavior, not phrasing. A transcript substring check is not enough unless it encodes a meaningful behavior class and has adversarial tests showing that unsafe or merely keyword-stuffed responses fail. Prefer checks that verify tool use, skill invocation, edit ordering, file state, generated artifacts, web-browsing absence, source lookup, or release/debugging gate behavior.

Some scenario expectations cannot be honestly automated with simple checks. Those expectations should be reviewed against the `## Acceptance Criteria` in `story.md` and reported separately from deterministic check results.

Each skill receives one of these published verdicts:

- `clear positive delta`: skilled trials consistently outperform no-skill trials on the scenario's core behavior.
- `mixed positive delta`: skilled trials improve some important behavior but remain inconsistent or fail secondary checks.
- `no visible delta`: skilled and no-skill trials behave similarly.
- `negative delta`: skilled trials are worse or introduce risky behavior.
- `inconclusive / check issue`: the scenario, checks, or instrumentation are too weak to support a behavior conclusion.

Verdicts must separate skill behavior from check reliability. If a check is brittle, too broad, or hard to interpret, the dossier should say that directly instead of blaming the skill.

## Published dossier

Create one repo-visible dossier under `evals/reports/`, named with the run date and matrix purpose, for example `YYYY-MM-DD-cities2-codex-skill-effectiveness-matrix.md`.

The dossier should include:

1. `# Cities2 Codex skill effectiveness matrix`
2. `## Executive summary`
3. `## Scenario matrix`
4. `## Deterministic check results`
5. `## Acceptance-criteria review results`
6. `## Skill verdicts`
7. `## Per-skill observations`
8. `## Check and instrumentation notes`
9. `## Next decisions`
10. `## Artifact hygiene`

The executive summary should say what this matrix can and cannot prove. It should be explicit that the matrix is directional evidence from one scenario per skill, not a guarantee of broad skill reliability.

The scenario matrix should include one row per skill with scenario id, condition counts, pass/fail counts, core failed checks, and verdict.

The deterministic check results should summarize pass, fail, and indeterminate check outcomes without claiming they fully grade the skill. The acceptance-criteria review results should explain any human-reviewed behavior judgments that sit outside deterministic checks.

Per-skill observations should summarize all six trials in plain English. Short sanitized snippets are allowed only when needed to explain a behavior that cannot be fairly paraphrased.

## Artifact hygiene

Raw artifacts remain under ignored `evals/results/`. The committed dossier must not include raw JSON, raw traces, full transcripts, generated workdir names, generated agent home paths, local checkout paths, usernames, secrets, tokens, or machine-specific output.

Before committing the dossier, verify:

- `git ls-files evals/results` prints nothing.
- `git diff --check` passes.
- Added repo-visible text contains no local paths, usernames, secrets, raw run directory names, or private evidence markers.
- The dossier quotes no long transcript passages.

## Implementation shape

The first implementation should be scenario-first, not automation-first.

Add or confirm the five scenarios and checks, then run the matrix using existing runner capabilities and small manual orchestration where needed. A matrix runner command can be proposed later if the first five-skill pass shows the workflow is stable and worth repeating.

The implementation plan should split work into small PRs:

1. Scenario/check PRs for missing skill scenarios.
2. Minimal runner or documentation adjustments only if the scenarios cannot run with existing commands.
3. Local run and sanitized dossier PR.

Each PR that changes code or package payloads must run the repository's required gates. The dossier PR should receive independent review before its conclusions are used to justify skill edits.

## Review plan

The published matrix must receive independent review against the exact branch tip before it is treated as decision evidence. Reviewers should check:

- whether each scenario matches the skill's intended trigger,
- whether each no-skill and with-skill comparison supports the stated delta,
- whether verdicts overclaim,
- whether check weaknesses are separated from skill weaknesses,
- whether artifact hygiene and privacy constraints are preserved.

If commits are added after review, review evidence is stale and must be refreshed.

## Next decisions after the matrix

After the dossier is reviewed, the maintainer should decide for each skill:

- keep the skill as-is,
- revise the skill,
- revise the scenario or checks and rerun,
- promote the scenario to a future three-client matrix,
- retire or de-prioritize the scenario because it does not measure useful behavior.

The matrix should make those decisions easier, but it should not silently make them inside the evaluation artifact.
