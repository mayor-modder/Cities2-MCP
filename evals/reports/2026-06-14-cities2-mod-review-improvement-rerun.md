# Cities2 mod-review improvement rerun

## Short version

Verdicts summarized: 12
Backends: codex
Run dates: 2026-06-14

These results cover only the listed backend runs.

This rerun follows the hardened `cities2-mod-review` eval work. It keeps the TSX/no-React-evidence scenario and adds a second release-readiness audit scenario with package-readiness and license/attribution bait.

- `cities2-mod-review-tsx-no-react-evidence`: `no-skill`: 0/3 passed; `with-cities2-mod-review`: 3/3 passed.
- `cities2-mod-review-release-readiness-audit`: `no-skill`: 0/3 passed; `with-cities2-mod-review`: 3/3 passed.

The result is a clear positive delta for `cities2-mod-review` on these two scenarios. The target skill now reliably produced actionable, evidence-grounded review findings for the original TSX/CSS scaffold and for a release-readiness audit that requires attribution and package/playtest gating.

## Run matrix

Code/eval commit reported by runner: 4d5c360
Skill checksum: sha256:b5264c9649ace993d0c2bf443e357236c76b707904fd6c33487408c37c3103d1

## Verdict table

| Backend | Scenario | Condition | Trial | Final | Failed checks |
| --- | --- | --- | ---: | --- | --- |
| codex | cities2-mod-review-tsx-no-react-evidence | no-skill | 1 | fail | review-actionable-findings-present, post-checks |
| codex | cities2-mod-review-tsx-no-react-evidence | no-skill | 2 | fail | review-actionable-findings-present, post-checks |
| codex | cities2-mod-review-tsx-no-react-evidence | no-skill | 3 | fail | review-unsupported-claims-absent, review-actionable-findings-present, post-checks |
| codex | cities2-mod-review-tsx-no-react-evidence | with-cities2-mod-review | 1 | pass | none |
| codex | cities2-mod-review-tsx-no-react-evidence | with-cities2-mod-review | 2 | pass | none |
| codex | cities2-mod-review-tsx-no-react-evidence | with-cities2-mod-review | 3 | pass | none |
| codex | cities2-mod-review-release-readiness-audit | no-skill | 1 | fail | review-release-readiness-audit-present |
| codex | cities2-mod-review-release-readiness-audit | no-skill | 2 | fail | review-release-readiness-audit-present, public-readiness-guarded, post-checks |
| codex | cities2-mod-review-release-readiness-audit | no-skill | 3 | fail | review-release-readiness-audit-present, public-readiness-guarded, post-checks |
| codex | cities2-mod-review-release-readiness-audit | with-cities2-mod-review | 1 | pass | none |
| codex | cities2-mod-review-release-readiness-audit | with-cities2-mod-review | 2 | pass | none |
| codex | cities2-mod-review-release-readiness-audit | with-cities2-mod-review | 3 | pass | none |

## Interpretation

The original scenario now demonstrates the behavior the earlier report could not prove: with the review skill present, agents consistently ranked real scaffold blockers ahead of unsupported React-loader assumptions, treated unimported CSS as inactive, separated observed evidence from bounded guidance, gave likely impact and concrete fixes, and named downstream readiness evidence.

The release-readiness audit adds a different pressure shape. It verifies that `cities2-mod-review` catches package/readiness gaps and license/attribution risk rather than polishing release copy or accepting package metadata as proof. The no-skill baseline missed the audit contract in all three trials; the target skill passed all three.

The checker changes are calibration changes, not exact-wording gates. They were expanded for natural variants observed in live runs, such as backticked or bold severity labels, "CSS has no current styling risk or benefit", "package named by the manifest is not present", and "should not publish this yet".

This remains scenario evidence, not a universal guarantee across clients, models, or larger mod projects.

## Follow-up status

`cities2-mod-review` is now proven for these two matrix scenarios. The next useful expansion is a third review scenario around a larger diff or multi-agent review synthesis, where the portable external-review offer and de-duplication guidance matter.

## Privacy note

Raw traces, transcripts, generated agent homes, and generated workdirs remain local under gitignored `evals/results/`.
