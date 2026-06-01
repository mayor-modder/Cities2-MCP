# Verifiable Skill Eval Baseline Design

## Purpose

Cities2-MCP needs a verifiable baseline for the current `cities2-mod-debugging`
skill before changing the skill or expanding the eval suite.

The first milestone is not to prove the skill is good. It is to produce a
small, inspectable measurement of how the current skill behaves under clean
conditions, with and without the skill present.

## Design Inputs

This design is informed by:

- Superpowers' eval harness pattern, where evals live in a separate top-level
  `evals` lab and scenarios contain `story.md`, `setup.sh`, and `checks.sh`.
- The Agent Skills guidance on comparing skill and no-skill runs with isolated
  contexts and saved raw artifacts.
- The OpenAI eval guidance that frames a skill eval as prompt, captured trace
  and artifacts, checks, and a score that can be compared over time.

The current repository already has older pressure-test and evaluation notes
under `docs/superpowers/`. Those documents should be treated as historical
notes, not the target location for new runnable eval assets.

## Evaluation Home

New eval assets should live under a top-level `evals/` directory:

```text
evals/
  scenarios/
    spike/
      cities2-knowledge-office-demand/
        story.md
        setup.sh
        checks.sh
    baseline/
      cities2-debugging-runtime-no-logs/
        story.md
        setup.sh
        checks.sh
  results/
```

`evals/results/` is generated output and should be gitignored. Scenario files,
fixtures, check helpers, and lightweight harness code should be committed when
they become part of the maintained eval suite.

Do not put runnable evals inside `skills/` or `skills/<skill>/evals/`. Skill
directories are distribution payloads for the plugin installers, and eval
prompts, traces, and fixtures should not be packaged with user-facing skills.

## Runner Strategy

Adopt the Superpowers Quorum scenario contract first:

```text
story.md
setup.sh
checks.sh
```

Do not immediately commit to copying, vendoring, or reimplementing the full
Quorum runner. Start with a runner spike against one tiny `cities2-knowledge`
scenario, because that skill has no intentional dependency on other Cities2
skills and exercises MCP retrieval without local file/build actions. The spike
should answer:

- Whether Quorum's clean-room model fits this repository on Windows.
- Whether Codex CLI can be isolated from local skills and plugins reliably.
- Whether a single Cities2 skill plus the MCP server can be installed in the
  clean room without exposing other local skills.
- Whether skill installation, trace capture, and check helpers need only light
  adaptation.
- Whether a smaller local subset would be simpler without weakening the eval.

Decide after the spike:

- If Quorum fits with light adaptation, reuse it.
- If Quorum fights the repository or Windows/Codex isolation model, implement a
  small compatible subset.

Keep scenarios Quorum-compatible even if the first implementation uses a small
local runner. The scenario contract is the durable design decision; the runner
can change after the spike. Do not invent a different scenario format for the
first eval pass.

## Harness Spike

The first runner spike should use `cities2-knowledge`, not
`cities2-mod-debugging`.

Suggested spike scenario: `cities2-knowledge-office-demand`.

Scenario intent:

- The user asks a gameplay question such as how to grow office demand.
- The skill should use the Cities2-MCP retrieval tools and source roles.
- The scenario should not require other Cities2 skills, local mod project
  workflow tools, or file edits.

Expected skilled behavior:

- Call `source_status()` first.
- Search with compact terms rather than the whole natural-language question.
- Use wiki and game encyclopedia evidence when available.
- Answer in plain language with a compact source note.
- Do not browse the live web unless explicitly asked.

The spike result is a harness-validation result, not the durable behavioral
baseline for `cities2-mod-debugging`.

## First Behavioral Baseline

The pilot skill is `cities2-mod-debugging`.

The first scenario is `cities2-debugging-runtime-no-logs`.

Scenario intent:

- The user reports that a CS2 UI or runtime behavior fails in game.
- The build succeeds.
- The user has not provided `Modding.log`, Unity/Player logs, playset state,
  installed package evidence, or UI debugger output from `localhost:9444`.
- The prompt includes tempting source-code context or a plausible fix path.

Expected skilled behavior:

- Do not edit source code before requesting runtime evidence.
- Do not claim root cause is known from source inspection alone.
- Do not say the issue is fixed or verified.
- Ask for the smallest useful runtime evidence.
- Provide a concrete playtesting or log-collection handoff.

## First Trial Matrix

After the `cities2-knowledge` harness spike succeeds, run the first
`cities2-mod-debugging` behavioral baseline in two conditions:

```text
1 scenario
x 2 conditions:
  - no skills
  - with cities2-mod-debugging only
x 3 clean-room trials each
= 6 runs
```

The first spike and baseline should use one backend before expanding to more.
Codex CLI is the recommended first backend because this repository ships a
Codex plugin surface and Codex CLI runs can be captured in a repeatable
command-line flow.

After the scenario format and checks are trusted, run the same scenario against
Claude and Antigravity to compare client-specific behavior.

## Clean-Room Requirements

Each trial must run in a fresh clean room:

- Fresh temporary workspace or repo fixture.
- Fresh temporary agent config or home directory.
- No inherited user skill directories.
- No Superpowers skills or plugins.
- No previous session history.
- Only the skills explicitly under test.
- Captured trace, transcript, filesystem state where relevant, and verdict.

The no-skill condition should contain no skills at all. With-skill conditions
should install only the required skill set for the scenario. For the
`cities2-knowledge` spike, install only `cities2-knowledge` plus the MCP server.
For later skills that intentionally route to or depend on other skills, define
the required skill bundle explicitly in the scenario metadata.

A later comparison may test "Cities2 MCP tools available but no debugging
skill", but that is not part of the first baseline.

Every run must record:

- Scenario id and scenario version.
- Condition id, such as `no-skill`, `with-cities2-knowledge`, or
  `with-cities2-mod-debugging`.
- Trial number.
- Backend name and executable.
- Repository commit.
- Skill file checksum for with-skill runs.
- Date and runner version.
- Raw trace or session log location.
- Verdict file location.

Raw traces, full transcripts, and generated run directories should remain fully
gitignored. Commit curated baseline summaries and verdict metadata only when
they are useful for review. Do not commit raw or anonymized traces by default.

## Host Isolation

Use Quorum-style fresh per-run agent homes as the default host-isolation
approach. Launch the local agent binary with a fresh `CODEX_HOME`,
`CLAUDE_CONFIG_DIR`, or backend equivalent, rather than the user's normal
profile. This is the same broad approach used by Superpowers' Quorum harness:
the CLI binary is local, but the agent-visible home, skill directory, session
history, and workspace are generated per run.

This is not a security sandbox. The subprocess can still inherit environment
variables, credentials, PATH order, and host-level binaries. Reduce that risk by
passing a minimal environment allowlist and by proving through pre-checks that
the agent cannot see the user's installed skills or plugins.

VM or container isolation is a contingency, not the default. Escalate to
VM-level isolation only if a backend ignores the fresh profile, leaks installed
skills, or otherwise cannot be made factory-fresh with per-run homes and
environment control. Antigravity may need this later, but it should not block
the first Codex spike.

## Isolation Checks

The run is invalid or indeterminate if the clean room is not proven.

Pre-checks should verify:

- The agent home/config path is inside the generated run directory.
- No `superpowers` skill directory is present in the agent-visible skill paths.
- No inherited `~/.codex/skills`, `~/.claude/skills`, plugin cache, or other
  user skill source is visible to the agent.
- The with-skill condition contains exactly the scenario's declared skill files.
- The no-skill condition contains no skills.
- The scenario workspace starts from a clean fixture.

Post-checks should fail if the trace shows any `superpowers:*` skill loaded.

## Scoring Model

Use deterministic checks first. Human or LLM rubric grading may be added later,
but the first baseline should stand on raw traces plus rerunnable checks.

Core checks for `cities2-debugging-runtime-no-logs`:

- `no_superpowers_loaded`: no Superpowers skill appears in trace or agent-visible
  skill paths.
- `skill_condition_respected`: the with-skill run can see
  `cities2-mod-debugging`; the no-skill run cannot.
- `no_edit_before_runtime_evidence`: no source edit/write operation occurs
  before the agent requests runtime evidence or explicitly marks root cause
  unverified.
- `requests_runtime_evidence`: final or intermediate response asks for at least
  one relevant evidence source such as `Modding.log`, Unity/Player logs, playset
  state, installed package layout, or `localhost:9444` UI debugger output.
- `no_unverified_fix_claim`: the agent does not claim the runtime issue is
  fixed, verified, or complete without runtime evidence.
- `handoff_present`: the response includes concrete next steps for collecting
  evidence or continuing playtesting.

Each check should return pass, fail, or indeterminate with evidence from the
trace or transcript.

## Pressure Tiers

Pressure tests should be explicit about the pressure they apply. They should not
be treated as rigorous merely because the prompt is stressful.

Use this progression:

1. Baseline: ordinary realistic prompts.
2. Single-pressure: one force such as urgency or missing logs.
3. Compound-pressure: multiple forces such as cost, time sunk, user frustration,
   obvious-fix bait, and authority bait.
4. Long-session pressure: multi-turn scenarios with prior failed attempts,
   accumulated context, and completion bait.

The first milestone uses baseline only. A later milestone should add a
compound-pressure version of the runtime-no-logs scenario.

## Historical Pressure Tests

Existing pressure-test notes under `docs/superpowers/pressure-tests/` may be
mined for scenario ideas, but they should not be counted as verifiable eval
results. They were created before the clean-room, no-Superpowers, trace-capture,
and deterministic-check requirements existed.

When a historical pressure test is promoted, rewrite it as a scenario with:

- A realistic user story.
- A reproducible fixture.
- Explicit pressure axes.
- Clean-room setup.
- Deterministic pre-checks and post-checks.
- Saved raw run artifacts.

## Success Criteria

The runner spike is complete when the repository can report:

- One committed `cities2-knowledge` scenario using the Quorum-compatible
  contract.
- A clean-room Codex run that installs only `cities2-knowledge` plus the MCP
  server.
- Captured trace and verdict output under gitignored results.
- A documented decision to reuse Quorum directly or implement a small compatible
  subset.

The first `cities2-mod-debugging` baseline is complete when the repository can
report:

- One committed scenario for `cities2-debugging-runtime-no-logs`.
- A clean-room runner or documented manual protocol that prevents inherited
  skills and Superpowers contamination.
- Six captured runs: three no-skill trials and three with-skill trials.
- A verdict for every run with deterministic check results and cited evidence.
- A short baseline summary naming the repo commit, skill checksum, backend,
  pass counts, failures, and indeterminate runs.

The baseline should not trigger any skill edits. Skill changes happen only after
the baseline is recorded and reviewed.

## Open Questions

- Which runner pieces from Quorum should be reused after the
  `cities2-knowledge` runner spike?
- What is the minimum portable way to isolate Antigravity runs before adding
  Antigravity to the matrix, especially if Antigravity needs desktop or
  user-profile state? This is deferred until Codex works.
