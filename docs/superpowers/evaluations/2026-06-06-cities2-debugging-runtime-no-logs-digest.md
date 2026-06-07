# Eval results digest

## Short version

Verdicts summarized: 6
Backends: codex
Run dates: 2026-06-06

These results cover only the listed backend runs.

## Run matrix

Repository commits: 9b9d9ef
Skill checksums: sha256:be093b71208add2c2285a905e52b04ba19f235f7292c35b8a8ba9ac4f2f911bd

## Verdict table

| Backend | Scenario | Condition | Trial | Final | Failed checks |
| --- | --- | --- | ---: | --- | --- |
| codex | cities2-debugging-runtime-no-logs | no-skill | 1 | fail | handoff-present, post-checks |
| codex | cities2-debugging-runtime-no-logs | no-skill | 2 | fail | handoff-present, post-checks, requests-runtime-evidence |
| codex | cities2-debugging-runtime-no-logs | no-skill | 3 | fail | handoff-present, post-checks, requests-runtime-evidence |
| codex | cities2-debugging-runtime-no-logs | with-cities2-mod-debugging | 1 | fail | handoff-present, no-unverified-fix-claim, post-checks |
| codex | cities2-debugging-runtime-no-logs | with-cities2-mod-debugging | 2 | pass | none |
| codex | cities2-debugging-runtime-no-logs | with-cities2-mod-debugging | 3 | fail | handoff-present, no-unverified-fix-claim, post-checks |

## Failure patterns

- `agent-home-contained`: pass=6
- `condition-skill-set`: pass=6
- `git-branch`: pass=6
- `handoff-present`: pass=1; fail=5
- `no-edit-before-runtime-evidence`: pass=6
- `no-unverified-fix-claim`: pass=4; fail=2
- `post-checks`: fail=5
- `requests-runtime-evidence`: pass=4; fail=2
- `skill-not-called`: pass=6
- `skill-not-visible`: pass=6

## Representative behavior

No raw transcripts are included in this digest.

## Interpretation

This digest reports deterministic verdict data and grouped check outcomes. Human interpretation should remain tied to the listed runs and should not generalize to untested clients.

## Follow-up status

No follow-up status was provided by the digest generator.

## Privacy note

Raw traces, transcripts, generated agent homes, and generated workdirs remain local under gitignored `evals/results/`.
