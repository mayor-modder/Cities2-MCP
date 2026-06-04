# Cities2-MCP evals

This directory contains Quorum-compatible skill eval scenarios and the local
runner spike for Cities2-MCP.

Scenarios use this contract:

```text
story.md
setup.sh
checks.sh
```

Generated run artifacts belong under `evals/results/`, which is gitignored.
Raw traces, transcripts, generated agent homes, and workdirs must not be
committed.

The first spike scenario is:

```text
evals/scenarios/spike/cities2-knowledge-office-demand/
```

Run the required offline harness smoke:

```powershell
python -m unittest tests.test_eval_runner_cli -v
```

This uses a local test process that emits Codex-style events to validate
clean-room setup, trace capture, checks, verdict writing, and `evals/results/`
handling without live model auth.

The runner CLI invokes the real Codex client and is reserved for optional
maintainer-local smoke runs:

```powershell
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition with-cities2-knowledge --trial 1
python -m evals.runner evals/scenarios/spike/cities2-knowledge-office-demand --condition no-skill --trial 1
```

The runner creates a fresh `CODEX_HOME` inside each run directory and installs
only the skill files declared by the condition. Future client adapters should
preserve the same isolation contract for `codex`, `claude`, and `agy`.
