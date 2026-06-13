# Cities2 Codex skill effectiveness matrix

## Executive summary

This run exercised five Cities2 skills in Codex with paired `no-skill` and target-skill conditions, three trials per condition, for 30 live verdicts. The results are directional evidence, not a guarantee of future behavior across clients, models, prompts, or MCP configurations. This dossier includes the June 11 calibration update: missing required MCP retrieval tools are now treated as an invalid eval environment, and the release scenario now checks readiness honesty rather than forced refusal to draft copy.

The strongest result is `cities2-mod-debugging`: the no-skill baseline failed all three runtime-no-logs trials, while the target skill passed all three. The most actionable skill gap is `cities2-modding`: it did not consistently force project-file inspection, public-readiness guarding, or explicit release/debugging routing. The `cities2-mod-review` scenario passes in both baseline and target-skill conditions, which means the current scenario is not strong enough to prove incremental skill value.

The most actionable infrastructure finding is that the knowledge scenario could not exercise Cities2-MCP retrieval tools in live Codex. The agent read the skill but the expected retrieval calls were unavailable. That must be recorded as indeterminate environment failure, not as evidence that `cities2-knowledge` failed.

## Scenario matrix

| Scenario | Skill under test | Baseline result | Target-skill result | Primary behavior under test |
| --- | --- | ---: | ---: | --- |
| `cities2-knowledge-office-demand` | `cities2-knowledge` | 0/3 pass | Indeterminate: retrieval tools unavailable | Uses Cities2-MCP retrieval before giving practical, sourced office-demand guidance |
| `cities2-modding-workflow-safe-handoff` | `cities2-modding` | 0/3 pass | 0/3 pass | Inspects project evidence, avoids unverified build claims, gives local playtest and follow-up routing |
| `cities2-mod-review-tsx-no-react-evidence` | `cities2-mod-review` | 3/3 pass | 3/3 pass | Reviews fixture evidence without inventing React-loader or CSS-runtime claims |
| `cities2-debugging-runtime-no-logs` | `cities2-mod-debugging` | 0/3 pass | 3/3 pass | Refuses source-only runtime certainty and requests logs/playset/UI-debugger evidence before edits |
| `cities2-mod-release-build-passed-no-playtest` | `cities2-mod-release` | 0/3 pass | Needs rerun after gate calibration | Keeps public readiness honest until packaged local playtesting exists |

## Deterministic check results

The runner now supports target conditions for all five Cities2 skills and records current Codex `command_execution` and `mcp_tool_call` events. This matters because earlier trace normalization made real file reads invisible.

The scenario checks now avoid exact answer wording for the new matrix cases. They verify observable behavior such as actual file-inspection commands, source/tool use, unsafe release-readiness claims, unsupported React assertions, runtime-evidence handoff, and follow-up routing.

Current failed-check counts by target condition, before the June 11 calibration:

| Target condition | Failed checks |
| --- | --- |
| `with-cities2-knowledge` | Reclassified: missing required retrieval-tool exposure is indeterminate, not skill failure |
| `with-cities2-modding` | `project-files-inspected` 1, `public-readiness-guarded` 2, `routes-debug-release-followups` 3 |
| `with-cities2-mod-review` | none |
| `with-cities2-mod-debugging` | none |
| `with-cities2-mod-release` | Obsolete strict-gate failures; rerun under readiness-honesty gate |

## Acceptance-criteria review results

The deterministic results align with manual acceptance criteria review of representative transcripts:

- `cities2-mod-debugging` consistently did the desired thing: it requested runtime evidence and did not edit or claim a root cause from source alone.
- `cities2-mod-review` and the no-skill baseline both passed the TSX evidence-grounding scenario after the checks were calibrated around hypotheses versus unsupported findings. The scenario is useful as a regression guard but not currently strong enough to prove the skill helps.
- `cities2-modding` often produced a reasonable local playtest handoff, but it did not consistently inspect the exact project files and did not reliably route release and runtime-failure follow-ups. This is the main skill-quality target from the run.
- `cities2-mod-release` recognized missing local playtesting. The original eval incorrectly required a hard refusal to provide final public copy. The calibrated gate should allow draft/unvalidated copy while rejecting ready-for-upload or validated-release claims.
- `cities2-knowledge` gave plausible gameplay advice, but the run did not prove source-grounded retrieval because the expected MCP calls were not available. Treat this as an invalid run until tool exposure is fixed.

## Skill verdicts

| Skill | Verdict | What this proves or disproves |
| --- | --- | --- |
| `cities2-knowledge` | Indeterminate | The live Codex eval setup did not expose the retrieval tools required by the skill. This is an eval environment error, not a skill failure. |
| `cities2-modding` | Not proven | The skill did not consistently force project-file inspection or explicit routing to release/debugging workflows. |
| `cities2-mod-review` | Scenario too weak | The target-skill and no-skill conditions both passed, so this scenario no longer proves incremental skill value. |
| `cities2-mod-debugging` | Proven for this scenario | The skill reliably blocked source-only runtime fixes and asked for the right evidence in all target-skill trials. |
| `cities2-mod-release` | Needs rerun | The old gate was too strict. Rerun under the calibrated standard: advise against release without playtesting, do not claim readiness, and label any provided copy as draft or unvalidated. |

## Per-skill observations

`cities2-knowledge`: the agent read the knowledge skill but reported that Cities2-MCP evidence tools were not exposed. The runner now has `required-tool-called`, which can mark this case indeterminate. Next work should make Codex eval runs launch with the MCP server available, then rerun this scenario before editing the skill text.

`cities2-modding`: the target skill knew local playtesting mattered, but follow-up routing stayed too implicit. The skill should more directly say when to hand off to `cities2-mod-release` and `cities2-mod-debugging`, and the scenario may need a follow-up test that separates “reasonable playtest handoff” from “specialized workflow routing.”

`cities2-mod-review`: the scenario now verifies that safe React hypotheses and evidence requirements are allowed while unsupported React requirements are blocked. Because the no-skill baseline also passes, the next review eval should define success around review usefulness: evidence-grounded findings, severity/order, concrete fix guidance, and no unsupported framework/runtime claims.

`cities2-mod-debugging`: this is the current positive control. Keep the scenario as a regression guard for runtime debugging behavior.

`cities2-mod-release`: the target skill acknowledged the missing playtest. The scenario has been recalibrated so the important failure is not "agent drafted copy" but "agent misrepresented readiness." The gate should pass honest draft/unvalidated copy and fail ready-for-upload language.

## Check and instrumentation notes

The evals now use a Quorum-style scenario shape with `story.md`, `setup.sh`, and `checks.sh`, plus deterministic runner checks. The new checks are still transparent predicates, not a hidden model judge.

Important harness changes from this implementation:

- Added a shared condition registry for all five skill conditions.
- Added behavior checks for release gates, unsupported review claims, project file inspection, build-claim safety, local playtest handoff, workflow routing, public readiness, and knowledge grounding.
- Updated trace normalization for current Codex command and MCP event shapes.
- Replaced brittle knowledge transcript word checks with source-grounded behavior checks and an indeterminate path when required retrieval tools are not exposed.
- Added scenario layout tests that forbid transcript-substring checks in the new matrix scenarios.

## Next decisions

1. Fix Codex eval MCP exposure before changing `cities2-knowledge`.
2. Focus skill work on `cities2-modding`: project inspection, release/debug routing, and public-readiness guarding.
3. Rerun `cities2-mod-release` under the readiness-honesty gate before editing the release skill.
4. Replace or strengthen the `cities2-mod-review` scenario so the no-skill baseline fails for a meaningful reason.
5. Keep `cities2-mod-debugging` as the known-good positive control while expanding debugging scenarios.

## Artifact hygiene

Raw generated run artifacts are local and gitignored under `evals/results/`. This dossier intentionally records aggregate verdicts and interpretation only; it does not include raw event logs, generated workdirs, generated agent homes, private local paths, credentials, or model transcripts.
