# Cities2 modding multiagent eval protocol

## Executive summary

This note prepares the next `cities2-modding` eval round. The goal is not to declare a cross-agent winner from weak evidence; it is to make the workflow-safe handoff scenario harder to game, then run a labeled exploratory pilot before using results to edit skills.

Two read-only subagent reviews informed this pass. One generated adversarial checker cases for false positives and false negatives. The other reviewed the scenario for acceptance-criteria gaps and report overclaim risk. The implementation hardens the deterministic checks first, because cross-agent results are only useful when the checks actually represent the behavior we care about.

## What changed

The `cities2-modding-workflow-safe-handoff` scenario now requires inspection of `WorkflowHandoffMod/package/package-state.txt` in addition to the README and source file. That file contains the decisive fixture evidence: no generated build output is present. Without requiring it, an agent could pass the old project-inspection check without reading the evidence needed for build/package/readiness claims.

The checker now rejects several brittle or misleading pass cases: reading `OtherMod/README.md` when `WorkflowHandoffMod/README.md` was required, searching for a filename string instead of inspecting the file, mentioning release/debugging workflows only to reject them, saying release is blocked but still telling the user to publish now, and giving shallow local-playtest handoffs that only say to collect a log.

The checker also accepts useful non-magic wording: root-relative project reads, tool-call-record reads, natural release blocks such as not publishing before build/package/local playtest evidence, withheld release notes, and specific release/debug follow-up routing without exact skill-name wording.

## Pilot matrix

| Backend | Condition | Status | Notes |
| --- | --- | --- | --- |
| Codex | `no-skill` | Ready for automated pilot | Existing runner and trace format are supported. |
| Codex | `with-cities2-modding` | Ready for automated pilot | Same scenario/checks as baseline. |
| Claude | `no-skill` / `with-cities2-modding` | Exploratory only | Use the same story and deterministic checklist, but do not compare against Codex until trace, skill-call, and tool-call visibility are documented. |
| Agy | `no-skill` / `with-cities2-modding` | Exploratory only | Treat empty or unavailable tool output as instrumentation risk unless independently verified. |

## Evidence model

Each run should report deterministic evidence separately from manual acceptance review. Deterministic evidence includes backend, condition, scenario id, commit, skill checksum or version source, trial count, pass/fail/indeterminate checks, and whether required tools were exposed. Manual acceptance review should paraphrase whether the answer actually met the story criteria without embedding raw transcripts.

Checker reliability should be a first-class section in the report. Hard evidence includes required file-inspection events and explicit pass/fail check records. Transcript heuristics such as routing and release-readiness guards should be labeled as heuristics, with known false-positive and false-negative risks.

Environment failures are not skill failures. Missing required tools, missing skill-call visibility, unavailable model adapters, or incomplete traces should be reported as indeterminate instrumentation states.

## Success gates

The next report can support a `cities2-modding` skill edit only if the target-skill runs show a repeated behavior gap that survives manual acceptance review and is not explained by checker weakness or runner instrumentation.

The next report should not claim decision-quality cross-agent comparison until Claude and Agy trace semantics are proven against the same evidence contract as Codex. Before that, cross-agent runs are useful as an exploratory pilot and source of adversarial examples.

## Artifact hygiene

Raw run artifacts remain local under gitignored `evals/results/`. Public reports should contain curated counts, check names, and sanitized behavior summaries only. Do not include raw event streams, full transcripts, generated run directory names, generated agent homes, local checkout paths, usernames, secrets, or API-key-shaped strings.
