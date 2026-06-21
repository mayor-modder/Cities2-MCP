# Claude knowledge and modding matrix

## Short version

Verdicts summarized: 12
Backends: claude
Run dates: 2026-06-20

This matrix extends the exploratory Claude backend pilot after the Claude adapter and first pilot report landed on `main`. It is still client-specific evidence, not a general claim about all models, prompts, or future Claude Code releases.

- `cities2-knowledge-office-demand`: `no-skill` failed 3/3 and `with-cities2-knowledge` passed 3/3.
- `cities2-modding-workflow-safe-handoff`: `no-skill` failed 3/3 and `with-cities2-modding` failed 3/3, but the target-skill condition improved several deterministic behaviors.

The knowledge result is a clear positive Claude skill delta for this scenario. The modding result is not a pass for `cities2-modding`; it is a useful diagnostic showing better project inspection and routing while still missing local playtest or public-readiness gates.

## Run matrix

Repository commit: c7769ae

Skill checksums:
- `sha256:b55603b75b4a536ea0cef6053a853deda4fe9f98209bed89dffa4215627b311f`
- `sha256:c94bee98c0e89010840846c8a5687f884ece188d26a58bf2c297ef37e9eab008`

## Verdict table

| Backend | Scenario | Condition | Trial | Final | Failed checks |
| --- | --- | --- | ---: | --- | --- |
| claude | `cities2-knowledge-office-demand` | `no-skill` | 201 | fail | `claude-exit`, `compact-search-query`, `knowledge-office-demand-grounded`, `required-tool-called` |
| claude | `cities2-knowledge-office-demand` | `no-skill` | 202 | fail | `claude-exit`, `compact-search-query`, `knowledge-office-demand-grounded`, `required-tool-called` |
| claude | `cities2-knowledge-office-demand` | `no-skill` | 203 | fail | `claude-exit`, `compact-search-query`, `knowledge-office-demand-grounded`, `required-tool-called` |
| claude | `cities2-knowledge-office-demand` | `with-cities2-knowledge` | 201 | pass | none |
| claude | `cities2-knowledge-office-demand` | `with-cities2-knowledge` | 202 | pass | none |
| claude | `cities2-knowledge-office-demand` | `with-cities2-knowledge` | 203 | pass | none |
| claude | `cities2-modding-workflow-safe-handoff` | `no-skill` | 201 | fail | `claude-exit`, `local-playtest-handoff-present`, `post-checks`, `project-files-inspected`, `public-readiness-guarded`, `routes-debug-release-followups` |
| claude | `cities2-modding-workflow-safe-handoff` | `no-skill` | 202 | fail | `claude-exit`, `local-playtest-handoff-present`, `post-checks`, `project-files-inspected`, `public-readiness-guarded`, `routes-debug-release-followups` |
| claude | `cities2-modding-workflow-safe-handoff` | `no-skill` | 203 | fail | `claude-exit`, `local-playtest-handoff-present`, `post-checks`, `project-files-inspected`, `public-readiness-guarded`, `routes-debug-release-followups` |
| claude | `cities2-modding-workflow-safe-handoff` | `with-cities2-modding` | 201 | fail | `post-checks`, `public-readiness-guarded` |
| claude | `cities2-modding-workflow-safe-handoff` | `with-cities2-modding` | 202 | fail | `local-playtest-handoff-present` |
| claude | `cities2-modding-workflow-safe-handoff` | `with-cities2-modding` | 203 | fail | `local-playtest-handoff-present` |

## Failure patterns

- `agent-home-contained`: pass=12
- `claude-exit`: fail=6
- `claude-mcp-tool-exposure`: pass=3
- `compact-search-query`: pass=3; fail=3
- `condition-skill-set`: pass=12
- `git-branch`: pass=12
- `knowledge-office-demand-grounded`: pass=3; fail=3
- `local-playtest-handoff-present`: pass=1; fail=5
- `no-unverified-build-claim`: pass=6
- `not-tool-called`: pass=6
- `post-checks`: fail=4
- `project-files-inspected`: pass=3; fail=3
- `public-readiness-guarded`: pass=2; fail=4
- `required-tool-called`: pass=6; fail=6
- `routes-debug-release-followups`: pass=3; fail=3
- `skill-not-called`: pass=12
- `skill-not-visible`: pass=12

## Knowledge result

`cities2-knowledge` is now supported by both the one-trial pilot and this three-trial Claude matrix. The target-skill condition passed every deterministic check in all three trials, including MCP preflight, required `source_status` and `search` calls, compact query shape, grounding, and the no-web-search guard. The no-skill condition failed all three trials on source-tool use and grounding.

This is a clear positive delta for the Claude backend on `cities2-knowledge-office-demand`.

## Modding result

`cities2-modding` is not proven by this matrix. The no-skill condition failed all three trials without inspecting the required project files or producing the expected local playtest and release/debug routing handoff.

The target-skill condition did improve the behavior:

- `project-files-inspected`: target-skill passed 3/3 while no-skill failed 3/3.
- `routes-debug-release-followups`: target-skill passed 3/3 while no-skill failed 3/3.
- `no-unverified-build-claim`: all target-skill trials passed.

The target-skill failures were narrower than baseline, but still enough to fail the scenario:

- Trial 201 had all local-playtest handoff signals and failed public readiness because the checker treated a question-style readiness heading as unsafe, even though the same verdict detail recorded blocked release, build/package gates, and local-playtest gates.
- Trial 202 missed the launch-step signal in the local playtest handoff.
- Trial 203 missed package-step and launch-step signals in the local playtest handoff.

This points to a mix of skill/handoff precision work and checker calibration. The trial 201 public-readiness failure should be manually reviewed before changing either the checker or `cities2-modding`.

## Follow-up status

Recommended next steps:

- Treat `cities2-knowledge` as a proven Claude-positive scenario for this runner and scenario version.
- Keep `cities2-modding` exploratory until the local playtest handoff wording is more reliable under Claude.
- Add or adjust checker tests for question-style release-readiness headings only after reviewing the sanitized target-skill trial 201 behavior.
- If `cities2-modding` is edited, rerun this same Claude matrix and compare against the three failed target-skill trials above.

## Privacy note

Raw traces, transcripts, generated agent homes, and generated workdirs remain local under gitignored `evals/results/`. This report includes only verdict-level counts, failed check names, and summarized interpretation.
