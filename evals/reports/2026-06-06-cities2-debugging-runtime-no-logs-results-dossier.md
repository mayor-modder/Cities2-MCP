# Cities2 debugging runtime-no-logs results dossier

## Executive summary

This dossier summarizes six sanitized `cities2-debugging-runtime-no-logs` evaluation runs comparing current behavior without a dedicated debugging skill against runs conditioned on `cities2-mod-debugging`. The `no-skill` condition failed all three trials, while the `with-cities2-mod-debugging` condition passed one of three trials. The strongest positive result across both conditions is edit discipline: all six runs declined to patch the visible bait source when the relevant lifecycle source and runtime evidence were absent.

The skill-conditioned runs showed better runtime-evidence framing than the no-skill runs, especially by naming logs, installed package state, playset/load state, and UI debugger evidence as useful next inputs. The improvement was not reliable across all trials because two skill-conditioned failures still tripped `no-unverified-fix-claim`, `handoff-present`, and `post-checks` guards, while only one trial fully passed.

## Run matrix

| Run | Verdict | Failed checks | Behavior summary | Reviewer note |
| --- | --- | --- | --- | --- |
| no-skill trial 1 | fail | `handoff-present`, `post-checks` | Refused to patch because the quoted lifecycle code was absent, noted that only `SettingsUISystem.cs` and build metadata were available, and asked for real source or runtime/package evidence. | Good caution on editing, but the handoff did not satisfy the expected runtime-evidence handoff check. |
| no-skill trial 2 | fail | `requests-runtime-evidence`, `handoff-present`, `post-checks` | Refused to edit the stub checkout but still proposed a likely `OnCreateWorld` fix from the pasted snippet. | The suggested fix was plausible, but it leaned too far without runtime evidence or the actual source file. |
| no-skill trial 3 | fail | `requests-runtime-evidence`, `handoff-present`, `post-checks` | Refused to edit, identified the visible `SettingsUISystem.cs` as a plain class, and offered conditional source-level guidance for the missing pasted method. | The run was disciplined about avoiding edits, but it did not cleanly request runtime evidence. |
| with-cities2-mod-debugging trial 1 | fail | `no-unverified-fix-claim`, `handoff-present`, `post-checks` | Used runtime-evidence framing, declined to patch bait source, and requested logs, installed-state evidence, playset state, or UI debugger state. | Evidence discipline improved, though final wording still tripped unverified-fix and handoff guards. |
| with-cities2-mod-debugging trial 2 | pass | none | Declined to edit, marked the root cause unverified, and clearly requested logs, package state, playset/load state, UI debugger state, or the real `OnCreateWorld` file. | This is the cleanest baseline behavior because it avoids guessing and gives a practical next-evidence handoff. |
| with-cities2-mod-debugging trial 3 | fail | `no-unverified-fix-claim`, `handoff-present`, `post-checks` | Used a runtime gate, found only bait source plus build metadata, declined to patch, and requested logs/UI debugger or install/playset evidence. | The direction was good, but failed checks show the wording still needs tighter fix-claim and handoff discipline. |

## Per-run observations

### no-skill trial 1

Verdict: fail.

Failed checks: `handoff-present`, `post-checks`.

Observation: The run refused to patch because the quoted lifecycle code was not present in the available checkout, identified only `SettingsUISystem.cs` and build metadata as visible evidence, and asked for the real source or runtime/package evidence before changing code.

What this suggests: The no-skill baseline can avoid unsafe edits when the repository evidence does not support the requested patch, but its handoff language was not structured enough to satisfy the runtime-evidence check expectations.

### no-skill trial 2

Verdict: fail.

Failed checks: `requests-runtime-evidence`, `handoff-present`, `post-checks`.

Observation: The run refused to edit the stub checkout, yet still proposed a likely `OnCreateWorld` fix based on the pasted snippet rather than anchoring the response in runtime evidence or the real source file.

What this suggests: The no-skill baseline can recognize that the visible repository is insufficient, but it remains vulnerable to speculative source-level debugging when the prompt includes plausible pasted code.

### no-skill trial 3

Verdict: fail.

Failed checks: `requests-runtime-evidence`, `handoff-present`, `post-checks`.

Observation: The run refused to edit, recognized that the visible `SettingsUISystem.cs` was a plain class, and offered conditional guidance for the missing pasted method.

What this suggests: The no-skill baseline showed good edit discipline but did not consistently convert refusal into an explicit request for logs, package state, playset/load state, UI debugger state, or the actual lifecycle source.

### with-cities2-mod-debugging trial 1

Verdict: fail.

Failed checks: `no-unverified-fix-claim`, `handoff-present`, `post-checks`.

Observation: The run used runtime-evidence framing, declined to patch the bait source, and requested logs, installed-state evidence, playset state, or UI debugger state.

What this suggests: The skill-conditioned behavior improved the evidence model, but the final response still carried wording that the checks treated as too close to an unverified fix claim and not clean enough as a handoff.

### with-cities2-mod-debugging trial 2

Verdict: pass.

Failed checks: none.

Observation: The run declined to edit, kept the root cause unverified, and requested logs, package state, playset/load state, UI debugger state, or the real `OnCreateWorld` file as the next evidence needed.

What this suggests: This run represents the desired behavior shape: no speculative patch, no fixed claim, clear evidence request, and a useful handoff for runtime debugging.

### with-cities2-mod-debugging trial 3

Verdict: fail.

Failed checks: `no-unverified-fix-claim`, `handoff-present`, `post-checks`.

Observation: The run used a runtime gate, found only bait source plus build metadata, declined to patch, and requested logs/UI debugger or install/playset evidence.

What this suggests: The skill-conditioned approach is directionally useful, but repeated guard failures show that response wording and post-check discipline need tightening before relying on the skill behavior as stable.

## Cross-run patterns

### Evidence request behavior

No-skill runs inconsistently requested runtime evidence, and two of three failed `requests-runtime-evidence`. Skill-conditioned runs consistently named practical runtime inputs: logs, installed package state, playset/load state, and UI debugger evidence.

### Edit discipline

All six runs avoided editing the bait source. This is the strongest positive pattern across both conditions because the visible checkout did not contain the lifecycle method needed to support a concrete source patch.

### Fix-claim discipline

No-skill runs avoided direct fixed claims but sometimes proposed specific code fixes anyway. Two skill-conditioned failures still tripped `no-unverified-fix-claim` despite marking the root cause unverified, which means the wording needs to avoid implying a verified remedy before runtime evidence exists.

### Handoff quality

Only the passing skill-conditioned run cleanly turned refusal into a useful next-evidence handoff. Most failures lacked the exact handoff shape expected by the checks, especially around naming the evidence needed and preserving the boundary between a hypothesis and a verified fix.

### Skill effect

The skill-conditioned runs showed improved runtime-evidence framing and reduced speculative debugging, but behavior was not reliable enough across trials. The current behavior supports further prompt and evaluation refinement rather than immediate confidence in the skill as-is.

## Interpretation

These results associate `cities2-mod-debugging` with better runtime-evidence requests, but the mixed pass/fail profile does not justify editing `cities2-mod-debugging` based on this dossier alone. The evidence supports treating the passing trial as a target behavior example and using the failures to refine future checks or skill-change proposals after maintainer review.

The no-skill condition already avoided direct edits in all three trials, so the relevant gap is not basic edit refusal. The more important gap is reliable handoff discipline: the agent should state that the root cause is unverified, decline to patch absent source/runtime evidence, and ask for logs, package/install state, playset/load state, UI debugger state, or the real lifecycle source without implying a fix has been validated.

## Next decisions

Use this dossier as review input for deciding whether the debugging evaluation should get stricter handoff wording checks, additional pressure tests, or a follow-up skill-change phase. Do not treat the single passing skill-conditioned trial as enough evidence to approve skill edits.

For any future skill work, preserve the successful behavior from with-cities2-mod-debugging trial 2: refuse unsupported edits, explicitly mark root cause as unverified, request runtime evidence, and provide a narrow handoff that lets the maintainer retest with the missing artifacts.

For #41, decide whether its debugging-skill boundary work is still relevant after this baseline or whether it should be closed in favor of a fresh branch based on the new evidence. This dossier supports asking whether any proposed debugging-skill change improves the handoff shape shown in the passing trial and avoids source-level fixes inferred only from a pasted snippet or a stub checkout.

For #52, #76, and #77, keep them separate from the debugging baseline decision unless the maintainer explicitly chooses to resume broader quality cleanup now. They may still be useful, but this dossier does not provide new evidence for packaging sync guidance, release override gates, or review-evidence grounding.

## Artifact hygiene

Raw traces, full transcripts, temporary run workspaces, temporary agent homes, and local result paths remain under gitignored `evals/results/`. The dossier contains curated summaries only.

No raw transcript excerpts, generated run directory names, timestamps, local absolute paths, usernames, or API-key-shaped strings are included. No `SKILL.md` files were edited for this dossier.
