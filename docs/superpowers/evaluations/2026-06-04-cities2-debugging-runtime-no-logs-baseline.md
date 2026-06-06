# Cities2 debugging runtime-no-logs baseline

## Short version

This document records the first `cities2-mod-debugging` behavioral baseline after the eval runner harness spike.

## Scenario

Scenario path: `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/`

## Matrix

```text
1 scenario
x 2 conditions:
  - no-skill
  - with-cities2-mod-debugging
x 3 clean-room trials each
= 6 runs
```

## Result storage

Raw traces, full transcripts, generated workdirs, and generated agent homes remain under gitignored `evals/results/`.

## Baseline results

Baseline results are not recorded yet. Fill this section only after the six-run matrix has been executed and reviewed.

## Review notes

- Do not edit `SKILL.md` files as part of recording this baseline.
- If checks fail because live Codex trace tool names differ from stub names, update the deterministic checks in a separate reviewed branch before trusting the baseline.
