# Cities2 debugging shared dependency conflict eval

## Short version

This live Codex matrix is not proven as a skill improvement for `cities2-mod-debugging` on the new shared-dependency scenario.

- `no-skill`: 1/3 passed.
- `with-cities2-mod-debugging`: 1/3 passed.
- shared-dependency evidence: 6/6 passed the checks that matter most for this scenario: the agent inspected both required evidence files and identified the Harmony shared dependency/API mismatch.
- The headline pass rate is dominated by `no-unverified-build-claim`, which failed on several responses that explicitly said build success was not runtime proof. Treat that as checker false-positive risk, not clean skill failure.
- Do not merge PR #137 from this report alone. The report is useful evidence, but it points to checker hardening and a rerun before the PR should be marked ready.

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
| `no-skill` | 1 | fail | `no-unverified-build-claim`, `post-checks` | Inspected both evidence files and diagnosed the shared Harmony dependency/API mismatch. |
| `no-skill` | 2 | pass | none | Inspected both evidence files, diagnosed the shared Harmony dependency/API mismatch, and separated compile success from runtime compatibility. |
| `no-skill` | 3 | fail | `no-unverified-build-claim`, `post-checks` | Inspected both evidence files and diagnosed the shared Harmony dependency/API mismatch. |
| `with-cities2-mod-debugging` | 1 | fail | `no-unverified-build-claim`, `post-checks` | Used the debugging workflow, inspected both evidence files, and diagnosed the shared Harmony dependency/API mismatch. |
| `with-cities2-mod-debugging` | 2 | fail | `no-unverified-build-claim`, `post-checks` | Used the debugging workflow, inspected both evidence files, and diagnosed the shared Harmony dependency/API mismatch. |
| `with-cities2-mod-debugging` | 3 | pass | none | Used the debugging workflow, inspected both evidence files, diagnosed the shared Harmony dependency/API mismatch, and separated compile success from runtime compatibility. |

## Failure patterns

- `project-files-inspected`: 6 pass, 0 fail. Every run read both `SharedDependencyConflictMod/logs/launch.log` and `SharedDependencyConflictMod/installed/TargetMod/dependencies.txt`.
- `shared-dependency-conflict-investigated`: 6 pass, 0 fail. Every run connected the launch failure to an installed/shared Harmony version and missing API evidence.
- `no-unverified-build-claim`: 2 pass, 4 fail. The failing examples were not agents claiming the build proved runtime safety; they were mostly agents warning that compile/build success is insufficient. This is a checker false-positive risk.
- `post-checks`: 2 pass, 4 fail. These failures mirror the `no-unverified-build-claim` failures.

## Interpretation

The new scenario is doing useful work: it made the agents prove the installed-state dependency diagnosis instead of hand-waving at the other mod or editing a random call site. That is the strongest result from this matrix.

The skill delta is not proven. Both conditions produced the core diagnosis in all three trials, and both conditions had the same 1/3 final pass rate. The `with-cities2-mod-debugging` runs were more explicit about using a runtime-debugging workflow, but this matrix does not show a clean positive pass-rate delta.

The most actionable finding is in the checker, not the skill text: `no-unverified-build-claim` appears to treat some cautionary build statements as if they were unsafe build-success claims. A good answer should be allowed to say that build success only proves compilation and does not prove runtime compatibility.

## Follow-up status

PR #137 should stay draft.

Recommended next step:

1. Harden `no-unverified-build-claim` so cautionary statements about build success not proving runtime safety pass.
2. Add focused regression tests for the failure phrases seen in this matrix.
3. Rerun the six-trial matrix.
4. Mark PR #137 ready only after the rerun report shows whether `cities2-mod-debugging` has a real behavior delta, or explicitly records that it does not.

## Privacy note

Raw traces, generated homes, generated workdirs, and full transcripts remain local under gitignored `evals/results/`. This report includes only curated verdict metadata and paraphrased behavior observations.
