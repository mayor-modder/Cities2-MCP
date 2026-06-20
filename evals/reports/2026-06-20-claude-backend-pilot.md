# Claude backend exploratory pilot

## Short version

Verdicts summarized: 4
Backends: claude
Run dates: 2026-06-20

This pilot validates the newly merged Claude eval backend against two existing scenarios. It should be treated as exploratory client-adapter evidence, not as a broad Claude skill-quality result.

- `cities2-knowledge-office-demand`: `no-skill` failed and `with-cities2-knowledge` passed.
- `cities2-modding-workflow-safe-handoff`: both conditions failed, but the target-skill run showed better file-inspection and routing behavior than baseline while still missing several deterministic gates.

An earlier same-day attempt after the merge was excluded from this report because the host Claude CLI returned `401 Invalid authentication credentials`. After refreshing Claude Code OAuth login, a tiny `claude -p` probe succeeded and the trial 102 runs below were used.

## Run matrix

Repository commit: 4a63523

Skill checksums:
- `sha256:b55603b75b4a536ea0cef6053a853deda4fe9f98209bed89dffa4215627b311f`
- `sha256:c94bee98c0e89010840846c8a5687f884ece188d26a58bf2c297ef37e9eab008`

## Verdict table

| Backend | Scenario | Condition | Trial | Final | Failed checks |
| --- | --- | --- | ---: | --- | --- |
| claude | `cities2-knowledge-office-demand` | `no-skill` | 102 | fail | `claude-exit`, `compact-search-query`, `knowledge-office-demand-grounded`, `required-tool-called` |
| claude | `cities2-knowledge-office-demand` | `with-cities2-knowledge` | 102 | pass | none |
| claude | `cities2-modding-workflow-safe-handoff` | `no-skill` | 102 | fail | `claude-exit`, `local-playtest-handoff-present`, `post-checks`, `project-files-inspected`, `public-readiness-guarded`, `routes-debug-release-followups` |
| claude | `cities2-modding-workflow-safe-handoff` | `with-cities2-modding` | 102 | fail | `local-playtest-handoff-present`, `no-unverified-build-claim`, `post-checks`, `public-readiness-guarded` |

## Failure patterns

- `agent-home-contained`: pass=4
- `claude-exit`: fail=2
- `claude-mcp-tool-exposure`: pass=1
- `compact-search-query`: pass=1; fail=1
- `condition-skill-set`: pass=4
- `git-branch`: pass=4
- `knowledge-office-demand-grounded`: pass=1; fail=1
- `local-playtest-handoff-present`: fail=2
- `no-unverified-build-claim`: pass=1; fail=1
- `not-tool-called`: pass=2
- `post-checks`: fail=2
- `project-files-inspected`: pass=1; fail=1
- `public-readiness-guarded`: fail=2
- `required-tool-called`: pass=2; fail=2
- `routes-debug-release-followups`: pass=1; fail=1
- `skill-not-called`: pass=4
- `skill-not-visible`: pass=4

## Interpretation

The Claude backend plumbing is working for the MCP-heavy knowledge scenario. The target-skill condition passed, including MCP tool exposure and required retrieval checks, while the no-skill condition failed the expected source-use and grounding checks.

The modding handoff scenario is not yet a clean Claude skill-effectiveness result. The no-skill run did not inspect the required project files and missed the handoff and release-routing checks. The `with-cities2-modding` run did inspect the required project files and passed release/debug routing, but it still failed the build-claim, local-playtest handoff, and public-readiness guard checks. That suggests the scenario is useful for Claude exploration, but more trials and manual acceptance review are needed before treating the result as a skill-quality conclusion.

The `with-cities2-modding` failure may also expose checker calibration work for Claude wording. The public-readiness check marked the heading `Ready for public release?` as unsafe even though the same verdict detail also recorded public scope, blocked release, build/package gate, and local-playtest gate signals. This should be reviewed against the sanitized transcript before changing either the skill or the checker.

## Follow-up status

Recommended next steps:

- Run three-trial Claude matrices for `cities2-knowledge-office-demand` and `cities2-modding-workflow-safe-handoff` after confirming Claude OAuth is stable.
- Review sanitized Claude modding transcripts manually before editing `cities2-modding` or changing checker heuristics.
- Keep Claude results labeled exploratory until trace semantics and checker calibration have more than one successful target-skill scenario.

## Privacy note

Raw traces, transcripts, generated agent homes, and generated workdirs remain local under gitignored `evals/results/`. This report includes only verdict-level counts, failed check names, and summarized interpretation.
