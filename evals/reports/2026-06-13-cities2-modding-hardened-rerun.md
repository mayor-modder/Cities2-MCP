# Cities2 modding hardened rerun

## Short version

Verdicts summarized: 6
Backends: codex
Run dates: 2026-06-13

These results cover only the listed backend runs.

The hardened `cities2-modding-workflow-safe-handoff` eval produced a useful split:

- `no-skill`: 0/3 passed.
- `with-cities2-modding`: 1/3 passed.

This is not a clean pass for the skill, but it is an actionable result. The skill condition consistently improved the behaviors the eval is meant to measure: project evidence inspection, avoiding unverified build claims, and routing release/debug follow-ups. The remaining failures point to specific handoff and release-gate consistency gaps rather than random transcript wording.

## Run matrix

Repository commits: 71f748d
Skill checksums: sha256:2dfaed0703695cbef5b76f0f8df12a3d822e448e9dd99d27d2da9c9ebacb5db0

## Verdict table

| Backend | Scenario | Condition | Trial | Final | Failed checks |
| --- | --- | --- | ---: | --- | --- |
| codex | cities2-modding-workflow-safe-handoff | no-skill | 1 | fail | local-playtest-handoff-present, post-checks, project-files-inspected, public-readiness-guarded, routes-debug-release-followups |
| codex | cities2-modding-workflow-safe-handoff | no-skill | 2 | fail | local-playtest-handoff-present, project-files-inspected, routes-debug-release-followups |
| codex | cities2-modding-workflow-safe-handoff | no-skill | 3 | fail | local-playtest-handoff-present, project-files-inspected, routes-debug-release-followups |
| codex | cities2-modding-workflow-safe-handoff | with-cities2-modding | 1 | fail | post-checks, public-readiness-guarded |
| codex | cities2-modding-workflow-safe-handoff | with-cities2-modding | 2 | fail | local-playtest-handoff-present |
| codex | cities2-modding-workflow-safe-handoff | with-cities2-modding | 3 | pass | none |

## Failure patterns

- `agent-home-contained`: pass=6
- `condition-skill-set`: pass=6
- `git-branch`: pass=6
- `local-playtest-handoff-present`: pass=2; fail=4
- `no-unverified-build-claim`: pass=6
- `post-checks`: fail=2
- `project-files-inspected`: pass=3; fail=3
- `public-readiness-guarded`: pass=4; fail=2
- `routes-debug-release-followups`: pass=3; fail=3
- `skill-not-called`: pass=6
- `skill-not-visible`: pass=6

## Representative behavior

No raw transcripts are included in this digest.

## Interpretation

The eval discriminated between skill and no-skill conditions:

- `project-files-inspected`: `no-skill` failed 3/3; `with-cities2-modding` passed 3/3.
- `routes-debug-release-followups`: `no-skill` failed 3/3; `with-cities2-modding` passed 3/3.
- `no-unverified-build-claim`: both conditions passed 3/3, so this scenario does not prove the skill is needed for that behavior.
- `local-playtest-handoff-present`: `no-skill` failed 3/3; `with-cities2-modding` passed 2/3.
- `public-readiness-guarded`: `no-skill` passed 2/3; `with-cities2-modding` passed 2/3.

The skilled failures are the important follow-up signal:

- Trial 1 inspected the fixture and gave a mostly correct workflow, but did not make the build/package public-release gate explicit enough for `public-readiness-guarded`.
- Trial 2 identified the fixture as incomplete and not public-release-ready, but did not provide enough package/installable-artifact handoff detail for `local-playtest-handoff-present`.
- Trial 3 passed every check.

These results suggest the next skill-quality change should make `cities2-modding` more consistent about three behavior-level requirements: inspect package-state evidence, distinguish build/package artifacts from public release readiness, and give a concrete local playtest handoff that names package/install, launch, playset, log, UI-debugger, and confirmation evidence.

This digest reports deterministic verdict data and grouped check outcomes. Human interpretation should remain tied to the listed runs and should not generalize to untested clients.

## Follow-up status

Recommended follow-up:

- Tighten the `cities2-modding` skill guidance for incomplete-project handoffs.
- Consider whether `local-playtest-handoff-present` should treat "installable local artifact" as equivalent to "package" when the behavior is otherwise correct.
- Rerun this same six-trial matrix after the skill/checker change.

## Privacy note

Raw traces, transcripts, generated agent homes, and generated workdirs remain local under gitignored `evals/results/`.
