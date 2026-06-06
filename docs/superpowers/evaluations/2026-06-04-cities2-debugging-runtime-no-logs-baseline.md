# Cities2 debugging runtime-no-logs baseline

## Short version

This document records the first `cities2-mod-debugging` behavioral baseline after the eval runner harness spike.

## Scenario

Scenario path: `evals/scenarios/baseline/cities2-debugging-runtime-no-logs/`

## Matrix

```text
1 scenario
x 1 backend:
  - codex
x 2 conditions:
  - no-skill
  - with-cities2-mod-debugging
x 3 clean-room trials each
= 6 runs
```

## Result storage

Raw traces, full transcripts, generated workdirs, and generated agent homes remain under gitignored `evals/results/`.

## Baseline results

Verdicts summarized: 6
Backends: codex
Repository commits: 9b9d9ef
Skill checksums: sha256:be093b71208add2c2285a905e52b04ba19f235f7292c35b8a8ba9ac4f2f911bd

### Final counts

- cities2-debugging-runtime-no-logs / no-skill: pass=0; fail=3; indeterminate=0
- cities2-debugging-runtime-no-logs / with-cities2-mod-debugging: pass=1; fail=2; indeterminate=0

### Check counts

- agent-home-contained: pass=6; fail=0; indeterminate=0
- condition-skill-set: pass=6; fail=0; indeterminate=0
- git-branch: pass=6; fail=0; indeterminate=0
- handoff-present: pass=1; fail=5; indeterminate=0
- no-edit-before-runtime-evidence: pass=6; fail=0; indeterminate=0
- no-unverified-fix-claim: pass=4; fail=2; indeterminate=0
- post-checks: pass=0; fail=5; indeterminate=0
- requests-runtime-evidence: pass=4; fail=2; indeterminate=0
- skill-not-called: pass=6; fail=0; indeterminate=0
- skill-not-visible: pass=6; fail=0; indeterminate=0

## Interpretation

The first baseline records current behavior only. It does not justify editing `cities2-mod-debugging` until the maintainer reviews these results.

## Codex trace-name calibration

One local calibration run was used to inspect the shape of Codex tool names. Raw trace output remains under gitignored `evals/results/` and is not committed.

Observed tool-name shape: no normalized tool calls were emitted in this calibration run.

Check helper update needed: suffix-tolerant matching was still added so future server-prefixed MCP names remain supported.

Calibration caveat: this run did not validate an actual MCP tool-call name shape. Treat suffix-tolerant matching as defensive support until a future live run emits MCP tool calls.

## Review notes

- Do not edit `SKILL.md` files as part of recording this baseline.
- If checks fail because live Codex trace tool names differ from stub names, update the deterministic checks in a separate reviewed branch before trusting the baseline.
- Generated agent homes can contain live Codex credentials. Never commit, paste, or share generated `evals/results/` contents.
