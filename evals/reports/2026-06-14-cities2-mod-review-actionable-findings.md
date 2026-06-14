# Cities2 mod-review actionable findings rerun

## Short version

Verdicts summarized: 6
Backends: codex
Run dates: 2026-06-14

These results cover only the listed backend runs.

This rerun replaces the weak `cities2-mod-review` TSX scenario gate with actionable findings checks. The old scenario mostly proved that agents did not make an unsupported React-loader claim. The new gate also requires inspected project evidence, severity-ordered findings, concrete fix guidance, explicit inactive-CSS treatment, React evidence limits, evidence-level separation, likely impact, and readiness evidence.

- `no-skill`: 0/3 passed.
- `with-cities2-mod-review`: 0/3 passed.

The result is not a pass for `cities2-mod-review`. It is still useful: the target skill consistently improved the readiness-evidence part of the answer, but it did not reliably satisfy the full actionable-review contract. In particular, target-skill trials still missed or under-phrased inactive-CSS treatment, evidence-level separation, or unsupported React-claim boundaries under the strict checker.

## Run matrix

Code/eval commit reported by runner: 36b6183
Report committed after the run; use the runner commit as the evaluated code state.
Skill checksum after the edit: sha256:dbe16d18f049bb33ab02b6de75ef4931a229c85c9823531e0fd49603e23748a7

## Verdict table

| Backend | Scenario | Condition | Trial | Final | Failed checks |
| --- | --- | --- | ---: | --- | --- |
| codex | cities2-mod-review-tsx-no-react-evidence | no-skill | 1 | fail | review-actionable-findings-present, post-checks |
| codex | cities2-mod-review-tsx-no-react-evidence | no-skill | 2 | fail | review-unsupported-claims-absent, review-actionable-findings-present, post-checks |
| codex | cities2-mod-review-tsx-no-react-evidence | no-skill | 3 | fail | review-actionable-findings-present, post-checks |
| codex | cities2-mod-review-tsx-no-react-evidence | with-cities2-mod-review | 1 | fail | review-actionable-findings-present, post-checks |
| codex | cities2-mod-review-tsx-no-react-evidence | with-cities2-mod-review | 2 | fail | review-actionable-findings-present, post-checks |
| codex | cities2-mod-review-tsx-no-react-evidence | with-cities2-mod-review | 3 | fail | review-unsupported-claims-absent, review-actionable-findings-present, post-checks |

## Failure patterns

- `agent-home-contained`: pass=6
- `condition-skill-set`: pass=6
- `git-branch`: pass=6
- `post-checks`: fail=6
- `project-files-inspected`: pass=6
- `review-actionable-findings-present`: fail=6
- `review-unsupported-claims-absent`: pass=4; fail=2
- `skill-not-called`: pass=6
- `skill-not-visible`: pass=6

## Interpretation

The tightened eval now distinguishes between a merely non-hallucinated review and an actionable review. All six runs inspected the expected scaffold files, but none satisfied the full strict actionable-review check.

There is still a meaningful partial delta. The no-skill baseline missed readiness evidence in all three trials. The target-skill condition named the downstream readiness gates in all three trials: clean build, package artifact, installed package/playset smoke launch, local playtest results or notes, logs, and UI debugger or screenshots. That means the skill update improved one important behavior, but did not prove the overall review skill.

The remaining target-skill failures are actionable. Trial 1 missed the evidence-level separation check. Trial 2 missed explicit inactive-CSS treatment under the stricter wording. Trial 3 missed inactive-CSS treatment and also tripped the unsupported-claim guard. These are not exact-wording failures; they identify concrete review behaviors that still need more reliable skill guidance or a deliberately narrower acceptance contract.

This result should be treated as directional evidence for this scenario, not a guarantee across clients, prompts, models, or larger mod projects.

## Follow-up status

Do not treat `cities2-mod-review` as proven by this scenario. The hardened eval should remain as a regression guard because it now catches the exact gap the old test missed: avoiding a React-loader hallucination is not enough. The next useful work is to improve the review skill so it consistently separates observed evidence from supported guidance, names likely impact for each meaningful issue, and treats unimported CSS as currently inactive while keeping React-specific fixes conditional on project evidence.

## Privacy note

Raw traces, transcripts, generated agent homes, and generated workdirs remain local under gitignored `evals/results/`.
