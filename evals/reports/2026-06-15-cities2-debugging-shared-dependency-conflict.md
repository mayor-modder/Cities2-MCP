# Cities2 debugging shared dependency conflict eval

## Short version

This live Codex matrix is not proven as a skill improvement for `cities2-mod-debugging` on the shared-dependency scenario.

- `no-skill`: 3/3 passed.
- `with-cities2-mod-debugging`: 3/3 passed.
- shared-dependency evidence: 6/6 passed the checks that matter most for this scenario: the agent inspected both required evidence files and identified the Harmony shared dependency/API mismatch.
- checker false-positive regressions are covered for cautionary build-success wording and escaped quoted Windows paths in tool traces.
- No positive skill delta appears in this matrix. The scenario is useful as a debugging behavior regression, but it is too easy for baseline Codex to prove `cities2-mod-debugging` improves the outcome.

## Run matrix

Scenario: `cities2-debugging-shared-dependency-conflict`

Code/eval commit reported by runner: `3ba4c24`

Backend: `codex`

Run date: 2026-06-15

Conditions:

- `no-skill`: clean-room Codex run with no Cities2 skill installed.
- `with-cities2-mod-debugging`: clean-room Codex run with only `cities2-mod-debugging` installed.

The fixture contained a launch log with `MissingMethodException`, an installed dependency inventory showing `0Harmony.dll` version `2.2.2.0`, and local comparison evidence that `HarmonyMethod.op_Implicit(MethodInfo)` is absent in `2.2.2.0` but present in `2.3.3.0`.

## Verdict table

| Condition | Trial | Final | Failed checks | Useful behavior observed |
| --- | ---: | --- | --- | --- |
| `no-skill` | 1 | pass | none | Inspected both evidence files and diagnosed the shared Harmony dependency/API mismatch. |
| `no-skill` | 2 | pass | none | Inspected both evidence files and diagnosed the shared Harmony dependency/API mismatch. |
| `no-skill` | 3 | pass | none | Inspected both evidence files and diagnosed the shared Harmony dependency/API mismatch. |
| `with-cities2-mod-debugging` | 1 | pass | none | Used the debugging workflow, inspected both evidence files, and diagnosed the shared Harmony dependency/API mismatch. |
| `with-cities2-mod-debugging` | 2 | pass | none | Used the debugging workflow, inspected both evidence files, and diagnosed the shared Harmony dependency/API mismatch. |
| `with-cities2-mod-debugging` | 3 | pass | none | Used the debugging workflow, inspected both evidence files, and diagnosed the shared Harmony dependency/API mismatch. |

## Failure patterns

- `project-files-inspected`: 6 pass, 0 fail.
- `shared-dependency-conflict-investigated`: 6 pass, 0 fail.
- `no-unverified-build-claim`: 6 pass, 0 fail.
- `post-checks`: 6 pass, 0 fail.

Earlier runs exposed two eval-plumbing defects before this final matrix:

- `no-unverified-build-claim` falsely failed cautionary statements such as build success only proving compilation and not runtime compatibility.
- `project-files-inspected` missed real file reads when Codex emitted PowerShell commands with escaped double-quoted Windows paths.

Both defects now have focused regression coverage.

## Interpretation

The scenario is doing useful regression work: it checks that agents read installed-state evidence, identify the shared Harmony dependency/API mismatch, and keep compile success separate from runtime launch verification.

The skill delta is not proven. Baseline Codex passed the same scenario 3/3, so this matrix does not show that installing `cities2-mod-debugging` improves the outcome. The skill-conditioned runs were more explicit about following a runtime-debugging workflow, but the deterministic pass/fail result is a tie.

The actionable conclusion is to keep the checker hardening, but avoid claiming PR #137 proves `cities2-mod-debugging` is better. To prove a skill improvement, the next scenario needs a harder failure mode where the skill should change behavior that baseline Codex does not already perform reliably.

## Follow-up status

PR #137 can merge as a scenario, checker, and report improvement if the intended claim is limited to: this adds a shared-dependency regression scenario and fixes eval plumbing false positives.

PR #137 should not be described as proving `cities2-mod-debugging` improves behavior on this scenario. No positive skill delta was observed.

Recommended next step:

1. Add or revise a debugging scenario that is harder for baseline Codex, for example one that requires respecting installed-mod workspace boundaries, refusing source edits when only installed evidence exists, or using client/runtime-specific debugging handoff steps.
2. Run the same `no-skill` versus `with-cities2-mod-debugging` matrix.
3. Mark a skill improvement only if the skill condition beats baseline on behavior that matters.

## Privacy note

Raw traces, generated homes, generated workdirs, and full transcripts remain local under gitignored `evals/results/`. This report includes only curated verdict metadata and paraphrased behavior observations.
