# Cities2-MCP evals

This directory contains Quorum-compatible skill eval scenarios and the local runner spike for Cities2-MCP.

Scenarios use this contract:

```text
story.md
setup.sh
checks.sh
```

Generated run artifacts belong under `evals/results/`, which is gitignored. Raw traces, transcripts, generated agent homes, and workdirs must not be committed.

The first spike scenario is:

```text
evals/scenarios/spike/cities2-knowledge-office-demand/
```

Run the required offline harness smoke:

```powershell
python -m unittest tests.test_eval_runner_cli -v
```

This uses local test processes that emit Codex-style and Claude-style events to validate clean-room setup, trace capture, checks, verdict writing, and `evals/results/` handling without live model auth.

The runner CLI invokes a real agent client and is reserved for optional maintainer-local smoke runs. Codex remains the default backend:

```powershell
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition with-cities2-knowledge --trial 1
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition no-skill --trial 1
```

Claude Code runs use the same scenario and condition contract:

```powershell
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --backend claude --condition with-cities2-knowledge --trial 1
```

Claude evals run with a generated per-run Claude config directory, a generated MCP config, and a generated plugin containing only the condition's declared skill. Live Claude evals seed that clean room from local Claude OAuth credentials, matching the Codex runner's local-auth fallback. If `ANTHROPIC_API_KEY` is explicitly present, Claude may use it instead, but maintainers normally should run with their existing Claude login. If the preflight reports `Not logged in`, run `/login` in Claude Code and retry the eval.

## Summarize local verdicts

Raw run artifacts remain under gitignored `evals/results/`. To create a committed review artifact, generate a sanitized digest from explicit verdict files:

```powershell
$output = "evals/reports/2026-06-06-cities2-debugging-runtime-no-logs-digest.md"
$verdict = Get-ChildItem "evals/results/cities2-debugging-runtime-no-logs-with-cities2-mod-debugging-trial-*/verdict.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
python -m evals.runner summarize --output $output $verdict
```

Review the generated digest before committing it. The digest writer rejects obvious private paths and generated agent config markers, but it is not a substitute for the repository privacy review.

The runner creates a fresh agent home inside each run directory and installs only the skill files declared by the condition. Client adapters should preserve the same isolation contract for `codex`, `claude`, and future `agy` support.
