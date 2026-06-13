# Cities2 knowledge and release focused rerun

## Executive summary

This focused rerun revisits the two unresolved outcomes from the June 7 skill effectiveness matrix: `cities2-knowledge` was previously indeterminate because live Codex did not expose the expected retrieval tools, and `cities2-mod-release` needed a rerun after the release gate was recalibrated away from forced refusal language.

The rerun used live Codex on repository commit `2c9d3f9`, with three no-skill and three target-skill trials for each scenario. The result is useful: `cities2-knowledge` now shows a clear positive delta, while `cities2-mod-release` shows a mixed positive delta because the no-skill baseline sometimes behaves safely but the release skill is more consistent.

## Run matrix

| Scenario | Condition | Result | Interpretation |
| --- | --- | ---: | --- |
| `cities2-knowledge-office-demand` | `no-skill` | 0/3 pass | Baseline did not consistently use the required source-status and retrieval workflow or produce source-grounded guidance. |
| `cities2-knowledge-office-demand` | `with-cities2-knowledge` | 3/3 pass | Target skill used the MCP retrieval path and produced practical, source-grounded office-demand guidance. |
| `cities2-mod-release-build-passed-no-playtest` | `no-skill` | 1/3 pass | Baseline sometimes guarded readiness honestly, but remained inconsistent and still produced unsafe or insufficiently caveated upload framing. |
| `cities2-mod-release-build-passed-no-playtest` | `with-cities2-mod-release` | 3/3 pass | Target skill consistently blocked ready-for-upload claims until packaged local playtesting or explicit unverified-release override. |

## What changed

The knowledge rerun confirmed that the Codex eval environment can now expose the expected Cities2-MCP retrieval tools. Each `with-cities2-knowledge` trial passed the MCP preflight for `source_status` and `search` before the scenario prompt ran.

The first release rerun exposed a checker calibration bug, not a release-skill bug. Live target-skill responses correctly refused readiness claims, but the checker missed common phrasing such as not being able to say the package is ready for upload or provide final public upload text. The checker now accepts that behavior class and normalizes curly apostrophes before matching contraction-based caveats.

## Knowledge result

`cities2-knowledge` moves from indeterminate to clear positive delta for this scenario. The target-skill condition passed all three trials, including the preflight that proves the expected retrieval tools were available. The no-skill condition failed all three trials, mostly because it did not follow the complete source-status and source-grounding contract.

This supports keeping `cities2-knowledge` unchanged for now. The next useful knowledge work is broader scenario coverage, not skill text editing based on this rerun.

## Release result

`cities2-mod-release` shows mixed positive delta. The target-skill condition passed all three trials after checker calibration, and each target-skill run kept public readiness blocked until packaged local playtesting or an explicit unverified-release override.

The no-skill baseline passed one of three trials, which matters. It means general Codex behavior can sometimes guard release readiness without the skill. The skill still improved consistency, but this result should not be overstated as a dramatic baseline-to-skill gap.

## Next decisions

Keep `cities2-knowledge` as-is and add future knowledge scenarios only when they test different source-grounding behaviors.

Keep `cities2-mod-release` as-is for this gate. The current evidence supports the skill's release-readiness framing; it does not justify a release-skill rewrite.

Treat the release checker calibration as part of the eval harness quality work. The checker now better matches the intended behavior class: honest draft or unverified-release handling is acceptable, while ready-for-upload claims without packaged local playtesting remain failures.

Return focus to the earlier main skill-quality target: `cities2-modding` workflow routing and project inspection.

## Artifact hygiene

Raw run artifacts remain local under gitignored `evals/results/`. This report contains curated counts and behavior summaries only. It does not include raw event streams, full transcripts, generated run directory names, generated agent homes, local checkout paths, usernames, secrets, or API-key-shaped strings.
