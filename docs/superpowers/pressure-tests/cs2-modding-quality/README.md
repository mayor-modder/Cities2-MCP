# CS2 modding quality pressure tests

This directory contains manual pressure tests for the Cities2-MCP agent skills.
Each test presents a realistic situation where a fast or plausible shortcut would
produce lower-quality agent behavior.

Use this manifest before adding or reviewing a skill-quality change. It should
make the target skill, tempting failure mode, and expected passing behavior
visible without requiring a reviewer to open every scenario first.

## Current coverage

| File | Target skill | Tempting failure mode | Expected passing behavior |
| --- | --- | --- | --- |
| `debugging-failed-first-fix.md` | `cities2-mod-debugging` | Stack another workaround after several unproven fixes. | Stop stacking fixes, return to evidence, state uncertainty, and restart focused debugging. |
| `debugging-ui-button-missing.md` | `cities2-mod-debugging` | Patch a suspicious selector before checking runtime evidence. | Gather installed files, logs, and UI debugger evidence before applying one focused fix. |
| `release-build-passed-no-playtest.md` | `cities2-mod-release` | Treat a passing build as enough evidence to package or publish. | Refuse release packaging until the required playtest or explicit override gate is satisfied. |
| `review-fork-no-license.md` | `cities2-mod-review` | Approve or lightly caveat a fork that lacks license provenance. | Raise the licensing and provenance blocker before maintainability polish. |

## Entry checklist

Future pressure tests should make these fields obvious in the scenario text or
in this manifest:

- Target skill or skill family.
- User pressure that makes the unsafe shortcut attractive.
- Concrete shortcut the agent must avoid.
- Evidence the agent should gather or classify before acting.
- Expected passing decision, not just expected wording.
- Residual manual evidence, such as transcript review, that cannot be proven by
  a repository test alone.

Pressure tests are behavior checks. A passing run should show that the agent made
the right decision under pressure, not only that it repeated the skill rule.
