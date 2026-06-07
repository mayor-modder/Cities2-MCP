# Cities2 Codex skill effectiveness matrix

## Executive summary

On 2026-06-07, Codex ran 30 live trials across the five Cities2 skills: three no-skill trials and three with-target-skill trials for each scenario. The run is useful directional evidence, not a guarantee that the skills work or fail in every future client, model, or prompt shape.

The strongest measured behavioral signal is `cities2-mod-debugging`: the with-skill condition passed two of three trials while the no-skill condition passed none.

This `cities2-debugging-runtime-no-logs` matrix result is a 2026-06-07 rerun; the 2026-06-06 debugging dossier reported one of three with-skill trials passing for the same scenario, so the difference should be read as run-to-run variance rather than a replacement for the earlier artifact.

For `cities2-mod-release`, the qualitative safety signal is narrower: all with-skill trials blocked public upload until local playtesting or an explicit risk-aware override, while one of three no-skill trials produced upload-ready copy.

The remaining scenarios expose instrumentation and calibration work more than settled skill verdicts. Four scenarios require explicit skill-call telemetry, and Codex often appeared to use the skill instructions in plain language without emitting a recorded skill-call event. Several failures also came from exact vocabulary gates, so this matrix should guide the next scenario/check refinement pass before driving broad skill edits.

## Scenario matrix

| Skill | Scenario | Conditions | Pass/fail counts | Core failed checks | Verdict |
| --- | --- | --- | --- | --- | --- |
| `cities2-knowledge` | `cities2-knowledge-office-demand` office demand gameplay answer | 3 no-skill, 3 with-skill | no-skill 0/3 pass; with-skill 0/3 pass | both conditions missed skill-call, `source_status`, and `search`; 2 no-skill trials also missed the source label | inconclusive / check issue |
| `cities2-modding` | `cities2-modding-workflow-safe-handoff` workflow-safe local handoff | 3 no-skill, 3 with-skill | no-skill 0/3 pass; with-skill 0/3 pass | skill-call event, workspace-evidence wording, release/debug routing, build-claim wording | inconclusive / check issue |
| `cities2-mod-review` | `cities2-mod-review-tsx-no-react-evidence` TSX/CSS review without React evidence | 3 no-skill, 3 with-skill | no-skill 0/3 pass; with-skill 0/3 pass | skill-call event, required observed/inferred wording, required CSS-not-loaded wording | inconclusive / check issue |
| `cities2-mod-debugging` | `cities2-debugging-runtime-no-logs` runtime UI missing with no logs | 3 no-skill, 3 with-skill | no-skill 0/3 pass; with-skill 2/3 pass | runtime-evidence request and handoff in the one failing with-skill trial; all no-skill trials missed the handoff | clear positive delta |
| `cities2-mod-release` | `cities2-mod-release-build-passed-no-playtest` build passed but no playtest evidence | 3 no-skill, 3 with-skill | no-skill 0/3 pass; with-skill 0/3 pass | no-skill missed release blocking and override language; with-skill only missed skill-call event | inconclusive / check issue |

## Skill verdicts

`cities2-knowledge`: inconclusive / check issue. The with-skill condition did not produce the expected skill-call or MCP-tool telemetry. The answers still discussed office demand mechanics, but the scenario is currently measuring integration/tool visibility more than a clean skill-content delta.

Only `cities2-mod-debugging` showed a measured pass-count delta. The other positive signals in this section are qualitative comparisons within failing runs and should not be treated as pass-rate improvements.

`cities2-modding`: inconclusive / check issue. The with-skill trials used local playtest evidence language in more cases and avoided several no-skill misses, but every with-skill trial still failed strict workspace-evidence, runtime-debug routing, and build-claim phrasing gates. This looks like possible skill influence plus check calibration work, not a measured pass-count delta.

`cities2-mod-review`: inconclusive / check issue. Both conditions inspected the small scaffold and avoided the unsupported React-loader jump, but both failed the exact observed/inferred and CSS-not-loaded wording checks. The scenario likely needs semantic checks before it can distinguish skill value.

`cities2-mod-debugging`: clear positive delta. With the debugging skill available, two of three trials passed the runtime-evidence, no-unverified-fix, and handoff checks. The failed with-skill trial still moved too close to direct patching without enough runtime evidence, so the skill helps but is not yet reliable.

`cities2-mod-release`: inconclusive / check issue. All with-skill trials blocked public upload pending local playtesting or an explicit risk-aware override, and the only remaining failed check was the skill-call telemetry gate. No-skill behavior included one trial that treated the package as ready for upload, so this is a useful qualitative signal, but the measured pass count remained flat at 0/3 versus 0/3.

## Per-skill observations

For `cities2-knowledge`, both conditions gave plausible office-demand advice. With-skill trials more often acknowledged the intended knowledge workflow, but none recorded the expected skill or source-tool events. Before using this scenario as a quality gate, decide whether Codex can expose those events reliably or whether the scenario should validate sourced-answer structure instead.

For `cities2-modding`, no-skill trials inspected the fixture but did not use the target skill, did not consistently name the expected handoff artifacts, and missed most routing language. With-skill trials consistently treated the workspace as a mod workflow and generally distinguished local playtesting from release readiness, but they did not use the exact route/build phrases required by the current gates.

For `cities2-mod-review`, the raw fail counts hide a useful detail: both conditions tended to inspect files before judging the TSX/CSS pair and usually avoided turning the file extension into a React dependency claim. The present checks require particular words rather than the underlying review distinction, which makes the result hard to interpret.

For `cities2-mod-debugging`, no-skill trials tended to diagnose or patch from source inspection too quickly and missed the required runtime-evidence handoff. With-skill trials more often stated that missing in-game UI is a runtime-evidence problem and asked for appropriate logs or debugger evidence before making a verified-fix claim.

For `cities2-mod-release`, no-skill trials sometimes inspected package metadata and recognized the missing playtest evidence, but one still produced upload-ready copy. With-skill trials consistently blocked release readiness and named the local playtest or explicit override requirement, which is the behavior this skill is supposed to teach.

## Cross-skill patterns

The biggest cross-skill pattern is telemetry mismatch. The with-skill condition installed the requested skill set, but four scenarios still failed their `skill-called` checks. In the observed assistant behavior, Codex often wrote that it was using a skill without producing a machine-readable skill-call event.

The second pattern is vocabulary sensitivity. Several checks ask for exact words such as observed/inferred, workspace evidence, or cannot confirm the build. Those phrases can be useful as pressure-test markers, but they can also turn good behavior into a fail when the response uses different wording.

The third pattern is that release/debugging discipline is easier to measure than broad quality. The debugging scenario has a concrete safety boundary and produced the only measured pass-count delta. Release also showed a qualitative safety signal, but the knowledge, modding, and review scenarios need either semantic check tools or narrower behavioral gates.

## Check and instrumentation notes

This run should not be read as a five-skill pass/fail scoreboard. It is directional evidence for where the eval harness and skill prompts are currently aligned or misaligned.

The `skill-called` check is valuable only if Codex reliably emits skill-call telemetry. In this run, the assistant text sometimes said it would use a skill while the recorded checks still failed the skill-call gate. Future matrix work should either fix telemetry capture or separate skill-visibility checks from behavioral verdicts.

The `cities2-knowledge` checks currently require both source tools and a source label. If the MCP surface is unavailable in the isolated run, the scenario mostly tests tool exposure and fallback honesty rather than gameplay-answer quality.

The `cities2-mod-review` checks should become more semantic before they drive skill edits. A revised gate would distinguish evidence-grounded findings from unsupported React-loader assumptions without requiring one exact observed/inferred phrasing.

The `cities2-modding` scenario changed after review, but the run suggests the build and routing gates remain stricter than natural Codex wording. The next pass should decide whether to teach exact language in the skill or relax checks toward behavioral meaning.

## Next decisions

Keep `cities2-mod-release` behavior as a candidate for a focused follow-up after fixing or waiving the skill-call telemetry gate; do not promote the current all-fail raw count as a measured result.

Keep `cities2-mod-debugging` in the matrix and add follow-up pressure around the one failed with-skill trial: the skill should more consistently avoid patching or claiming a runtime fix without logs, UI debugger evidence, or maintainer-provided runtime observations.

Revise the `cities2-knowledge` scenario before drawing a skill-quality conclusion. The next version should either guarantee the MCP tools are available in the clean room or measure transparent fallback and sourced-answer behavior directly.

Revise the `cities2-mod-review` checks before editing the skill. The observed behavior suggests the agent already avoids the most important unsupported React assumption, but the current checks do not capture that reliably.

Revise the `cities2-modding` checks and possibly the skill wording together. The skill appears to nudge the agent toward safer workflow framing, but the current pass/fail contract requires more exact routing and build-claim language than the skill naturally produced.

## Artifact hygiene

Only this sanitized dossier is intended for commit. Raw run directories remain local under gitignored `evals/results/`.

This dossier paraphrases behavior and reports aggregate failed-check names only. It does not include raw traces, full transcripts, generated workdirs, generated agent homes, local checkout paths, usernames, secrets, or machine-specific tool output.

The local counting digest was used only to identify counts and failed-check groups. It is not part of the published artifact.
