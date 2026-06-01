# Cities2-MCP evals

This directory contains skill eval scenarios for Cities2-MCP.

Scenarios use the Superpowers/Quorum-compatible contract:

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

Runner code will be added in follow-up stacked PRs.
