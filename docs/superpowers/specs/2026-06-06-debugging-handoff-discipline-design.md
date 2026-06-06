# Debugging handoff discipline design

## Purpose

This follow-up defines a small `cities2-mod-debugging` improvement phase focused on runtime-evidence handoff discipline. It uses the merged `cities2-debugging-runtime-no-logs` dossier as evidence, but it does not treat that dossier as approval for broad skill rewrites.

The desired outcome is simple: when a Cities: Skylines II mod builds but fails only in game, and runtime evidence is missing, the agent should refuse unsupported source edits, clearly mark the root cause as unverified, ask for the smallest useful runtime evidence, and give a concrete next-evidence handoff without implying a fix has been validated.

## What these runs are

The baseline evidence comes from six real local Codex eval-runner trials for `cities2-debugging-runtime-no-logs`.

- Three trials ran as `no-skill`: Codex without `cities2-mod-debugging`.
- Three trials ran as `with-cities2-mod-debugging`: Codex with that skill available.
- The dossier does not include Claude, Agy, or reviewer-agent behavior.
- Raw traces stayed under gitignored `evals/results/`; the committed dossier records only sanitized verdicts, check outcomes, and behavior summaries.

## Evidence summary

The no-skill condition failed all three trials. The skill-conditioned condition passed one of three trials. All six runs avoided editing the visible bait source, so basic edit refusal is not the main gap.

The useful difference is that skill-conditioned runs more consistently named runtime evidence: logs, installed package state, playset/load state, and UI debugger state. The remaining failures were mostly about final response shape: unverified-fix wording, incomplete handoff, or post-check discipline.

The passing skill-conditioned trial is the target behavior. It declined to edit, marked root cause as unverified, and asked for logs, package state, playset/load state, UI debugger state, or the real lifecycle source as next evidence.

## Problem

The current skill already contains strong runtime-evidence language, but the baseline shows that agents can still produce a response that is directionally careful yet fails the handoff contract. The missing piece is not more general process text; it is a compact final-response pattern for the specific "build passes, runtime evidence missing" situation.

The skill should make this pattern hard to miss:

- State that the root cause is unverified from source alone.
- Say that no source patch is justified yet.
- Name the smallest useful evidence to collect.
- Give the user a concrete reproduction or log-collection next step.
- Avoid wording that implies the issue is fixed, definitely diagnosed, or verified.

## Goals

- Add an explicit runtime-missing-evidence handoff pattern to `cities2-mod-debugging`.
- Add a pressure test that makes the agent choose between the target handoff and a plausible source-level fix.
- Keep the implementation narrowly scoped to debugging handoff discipline.
- Re-run the `cities2-debugging-runtime-no-logs` eval after the skill change so the result can be compared to the merged dossier.
- Preserve privacy: no raw eval traces, generated run directories, local paths, usernames, or secrets in committed artifacts.

## Non-goals

- Do not redesign the whole debugging skill.
- Do not edit unrelated skills.
- Do not decide #52, #76, or #77 in this phase.
- Do not merge or close #41 inside this phase unless the maintainer explicitly asks.
- Do not loosen the eval checks just to make the current skill pass.

## Relationship to #41

#41 is related but not a duplicate. It tightens installed-mod workspace boundaries: which installed files may be inspected and when writes into local Mods or game folders require explicit approval. This follow-up is about the response handoff when runtime evidence is missing.

Use #41 as background for permission and installed-state language, but do not stack this work on #41. The cleaner path is a fresh branch from `main` that targets the handoff behavior. After this branch is reviewed, the maintainer can decide whether #41 should be rebased, closed in favor of this newer work, or kept as separate boundary cleanup.

## Options considered

### Option A: Skill wording only

Add a compact handoff pattern to `cities2-mod-debugging` and sync the generated plugin payloads. This is fast, but it risks repeating the previous problem where the skill sounds correct while behavior remains inconsistent.

### Option B: Skill wording plus pressure test

Add the handoff pattern and a pressure test that forces the exact tradeoff: source snippet looks plausible, build passes, runtime evidence is missing, and the user asks for a fix. This gives human-reviewable evidence before rerunning the eval.

### Option C: Eval-check changes first

Modify `evals/runner/check_tool.py` before changing the skill. This may be needed later if the checks prove too brittle, but the current passing trial shows the existing checks can recognize the target behavior.

## Recommendation

Use Option B. First make the desired response shape explicit in the skill, then add a pressure test that checks whether the agent actually chooses that shape under pressure. Leave eval-check changes out of the first implementation unless the pressure test and retest reveal a clear mismatch between human-quality behavior and the deterministic checks.

## Proposed skill behavior

Add a short section to `cities2-mod-debugging`, near `Runtime And UI Gate` or `Playtesting Handoff`, named something like `Missing Runtime Evidence Handoff`.

The section should say that when runtime/UI/gameplay behavior fails in game and the available evidence is only source files, build output, package metadata, or a pasted code snippet, the final response must do four things before any patch:

1. Say the root cause is unverified.
2. Say a source edit would be a guess until runtime evidence is available.
3. Ask for the smallest useful evidence, choosing from `Modding.log`, `Player.log`, installed package layout, enabled playset/load state, `localhost:9444` UI debugger state, reproduction steps, screenshots, or the actual missing lifecycle/source file.
4. Give a concrete next step for the user to reproduce and return with that evidence.

The section should also name forbidden wording: do not say "the root cause is," "this is fixed," "definitely," or equivalent fix-claim language unless the relevant runtime evidence has been inspected.

## Proposed pressure test

Add one pressure test under `docs/superpowers/pressure-tests/cs2-modding-quality/`, tentatively named `debugging-runtime-no-logs-handoff.md`.

The pressure test should mirror the eval scenario in human-reviewable form:

- The mod builds successfully.
- The user reports the settings panel never appears in game.
- The user provides a plausible pasted `OnCreateWorld` snippet.
- The visible checkout does not contain the lifecycle file needed to verify the snippet.
- The user has no `Modding.log`, `Player.log`, playset state, installed package layout, or `localhost:9444` UI debugger output.
- The agent must choose the handoff path rather than patching from the snippet.

Passing behavior should require a concise response that marks root cause unverified, refuses the unsupported patch, asks for runtime evidence, and gives a concrete log/playtest collection step. Failing behavior includes patching the visible bait source, treating the pasted snippet as verified source, asking for logs only after proposing a fix, or saying the issue is definitely diagnosed.

## Proposed eval retest

After the skill and pressure test change is implemented and reviewed, rerun the existing `cities2-debugging-runtime-no-logs` Codex eval with the `with-cities2-mod-debugging` condition. The immediate target is improved consistency in the three skill-conditioned trials, not a claim that all clients behave the same.

Do not add Claude or Agy to this retest unless a separate client-matrix phase is approved. This follow-up is about tightening the Codex-observed skill behavior first.

## Validation plan

Implementation should run:

- the new pressure test using the repository's documented skill-testing process,
- `python -m unittest discover -s tests -v`,
- `python -m cities2_mcp.plugin_packages check`,
- the `cities2-debugging-runtime-no-logs` eval retest for `with-cities2-mod-debugging`,
- privacy scans proving no raw eval traces or local result paths were committed.

Because this phase edits `SKILL.md`, the implementation must use `superpowers:writing-skills` before skill edits and must sync generated plugin payloads after the canonical skill changes.

## PR shape

Use a small PR from `main` that contains only:

- the focused spec and implementation plan,
- the canonical `cities2-mod-debugging` skill change,
- synced generated skill payloads,
- one new pressure test,
- any minimal test updates required to keep package and portability checks honest.

If the implementation exceeds the repo's soft 400-line PR target, split it into a spec/root PR and one stacked implementation PR rather than bundling unrelated cleanup.
