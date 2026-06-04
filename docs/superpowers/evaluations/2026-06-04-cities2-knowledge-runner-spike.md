# Cities2 knowledge runner spike

## Short version

This was a plumbing smoke test for the eval runner. It did not test real model behavior.

The result is: keep the local Quorum-compatible runner subset for now, because it gives the project a free deterministic way to test the runner machinery before spending human or API time on real-client evals.

## What was actually tested

The required smoke ran `python -m unittest tests.test_eval_runner_cli -v`. That test uses a fake Codex process, not a real model.

This proves the runner can load the scenario, create an isolated run directory, prepare a clean agent home, run setup and check hooks, consume Codex-shaped JSONL events, normalize traces, write a verdict, and keep generated artifacts out of git.

This is useful because it gives CI a zero-cost way to catch broken runner plumbing.

## What was not tested

This did not test whether `cities2-knowledge` improves a real agent answer.

This did not compare real `with-cities2-knowledge` and `no-skill` model behavior.

This did not run Codex with ChatGPT/OAuth auth.

This did not run Claude or Antigravity.

This did not produce gameplay-quality eval results.

## Decision

Keep the local compatible subset for now. Revisit direct Quorum reuse after the local runner has proven useful and the project is ready for real-client behavior tests.

## Background

This evaluation records the first runnable harness spike for the Cities2-MCP skill eval suite. It is a harness-validation result, not the later behavioral baseline for `cities2-mod-debugging`.

## Scenario

Scenario path:
`evals/scenarios/spike/cities2-knowledge-office-demand/`

The scenario asks:

```text
How do I grow office demand?
```

## Conditions

- `no-skill`: no skills installed in the clean-room `CODEX_HOME`.
- `with-cities2-knowledge`: only `cities2-knowledge` plus the Cities2-MCP MCP server config installed in the clean-room `CODEX_HOME`.

## Result storage

Generated run artifacts are written under `evals/results/`, which is gitignored. Do not commit raw traces, full transcripts, generated agent homes, or generated workdirs.

## Required offline smoke protocol

Run the fake-Codex harness smoke:

```powershell
python -m unittest tests.test_eval_runner_cli -v
```

This is the required Task 6 gate. It validates runner orchestration with a fake client process, writes generated artifacts to a temporary results root, and validates the same result-handling path used by gitignored `evals/results/`.

## Optional real-client smoke direction

When higher-order behavior needs checking, test the supported clients rather than generic provider lanes:

- `codex`: optional maintainer-local smoke through the Codex CLI. Future OAuth support should use an eval-only `CODEX_HOME`, file-based credential storage, a disposable workdir, explicit sandbox settings, and only the skill/MCP config declared by the condition.
- `claude`: future adapter with a fresh client home/profile and only the packaged Cities2-MCP skill payload needed by the condition.
- `agy`: future Antigravity adapter with a fresh plugin/profile boundary and the same condition-scoped skill payload.

Real-client smoke is optional and local. It is not a CI gate, not a contributor gate, and not required for this harness-validation PR.

The current runner CLI invokes real Codex and may be used only for optional maintainer-local smoke after auth and isolation requirements are satisfied:

```powershell
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition with-cities2-knowledge --trial 1
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition no-skill --trial 1
```

Inspect each printed `verdict.json`. The runner may exit with `0`, `1`, or `2`; the verdict file is the source of truth for whether the run passed, failed, or was indeterminate.

## Original decision point

After the offline smoke passes, choose one:

- Reuse Quorum directly if Windows execution, Codex clean-room isolation, skill installation, trace capture, and check execution need only light adaptation.
- Keep the local compatible subset if Quorum adds friction without improving the scenario contract or determinism.

Record the decision in the smoke results section using only curated verdict status, repo-relative paths, and short rationale.

## Recorded smoke result

- Required offline fake-Codex smoke: `python -m unittest tests.test_eval_runner_cli -v` passed on 2026-06-04.

Raw run artifacts remain gitignored.

Real-client smoke for `codex`, `claude`, and `agy` belongs to a later optional adapter matrix. It is not this PR's gate.
