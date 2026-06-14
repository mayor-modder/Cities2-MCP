# Cities2 mod-review actionable findings rerun

## Short version

Verdicts summarized: 6
Backends: codex
Run dates: 2026-06-14

These results cover only the listed backend runs.

This rerun replaces the weak `cities2-mod-review` TSX scenario gate with actionable findings checks. The old scenario mostly proved that agents did not make an unsupported React-loader claim. The new gate also requires inspected project evidence, severity-ordered findings, concrete fix guidance, explicit inactive-CSS treatment, React evidence limits, and readiness evidence.

- `no-skill`: 0/3 passed.
- `with-cities2-mod-review`: 3/3 passed.

The result is a clear positive delta after a narrow skill update: the review skill now tells agents to name the downstream evidence needed to prove readiness, even when the scaffold is too incomplete to build yet.

## Run matrix

Repository commit reported by runner: fdee1bc
Skill checksum after the edit: sha256:5ec0e5312678641d3542d3110d33f90e60691ecc5f58baafd0c045c9ce9cf4b7

## Verdict table

| Backend | Scenario | Condition | Trial | Final | Failed checks |
| --- | --- | --- | ---: | --- | --- |
| codex | cities2-mod-review-tsx-no-react-evidence | no-skill | 1 | fail | review-actionable-findings-present |
| codex | cities2-mod-review-tsx-no-react-evidence | no-skill | 2 | fail | review-actionable-findings-present |
| codex | cities2-mod-review-tsx-no-react-evidence | no-skill | 3 | fail | review-actionable-findings-present |
| codex | cities2-mod-review-tsx-no-react-evidence | with-cities2-mod-review | 1 | pass | none |
| codex | cities2-mod-review-tsx-no-react-evidence | with-cities2-mod-review | 2 | pass | none |
| codex | cities2-mod-review-tsx-no-react-evidence | with-cities2-mod-review | 3 | pass | none |

## Failure patterns

- `agent-home-contained`: pass=6
- `condition-skill-set`: pass=6
- `git-branch`: pass=6
- `project-files-inspected`: pass=6
- `review-actionable-findings-present`: pass=3; fail=3
- `review-unsupported-claims-absent`: pass=6
- `skill-not-called`: pass=6
- `skill-not-visible`: pass=6

## Interpretation

The tightened eval now distinguishes between a merely non-hallucinated review and an actionable review. All six runs inspected the expected scaffold files and avoided unsupported React claims. The no-skill baseline still failed 3/3 because it did not consistently include readiness evidence, and one baseline trial also missed explicit inactive-CSS treatment. After the skill update, all three target-skill runs included actionable findings and downstream readiness evidence.

The skill change is intentionally small. It adds one readiness instruction to `cities2-mod-review`: when judging readiness, name the exact evidence that would prove the next stage, including clean build, package artifact, installed package/playset smoke launch, local playtest, relevant logs, and UI debugger or screenshots for UI mods. If a scaffold cannot build yet, the review still names those as downstream gates after build/package blockers are fixed.

This result should be treated as directional evidence for this scenario, not a guarantee across clients, prompts, models, or larger mod projects.

## Follow-up status

No further `cities2-mod-review-tsx-no-react-evidence` change is indicated by this rerun. The scenario now proves a useful positive delta for the review skill and should remain as a regression guard. The next useful expansion is a second review scenario with a larger diff or release-readiness audit where the multi-agent review offer and attribution/license checks matter.

## Privacy note

Raw traces, transcripts, generated agent homes, and generated workdirs remain local under gitignored `evals/results/`.
