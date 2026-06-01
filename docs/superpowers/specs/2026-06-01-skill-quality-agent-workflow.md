# Skill quality agent workflow

## Purpose

This spec captures the intended workflow for improving Cities2-MCP agent skills with multiple
orchestrator agents. The goal is to make skill changes evidence-driven, repeatable, and reviewable
across Codex, Claude, and Antigravity.

Superpowers is the reference standard for both skill prose and the documented process used to test
skills. The workflow should prove that a skill change changes agent behavior, not merely that the
edited skill reads better.

## Core principles

- Do not edit skills before the skill-testing protocol exists.
- Do not expand beyond one pilot skill until the protocol works end to end.
- Use GitHub issues as the work queue.
- Use a GitHub Project for structured routing and status.
- Use sub-issues for executable work items under one parent program issue.
- Assign issues to the maintainer only when human intervention is required.
- Require each orchestrator to self-review with a local subagent before opening a PR.
- Do not run external-model or plugin-style model comparisons unless the maintainer asks.
- Use cross-agent review as a pull-based process, not as traditional requested GitHub review.

## GitHub planning model

Create one parent issue for the program:

```text
Skill quality improvement program
```

All actionable work should be represented as sub-issues of that parent. Each sub-issue should be
added to the skill-quality project and should include enough detail for one agent to work
independently.

The project should use these fields:

- `Agent`: `Codex`, `Claude`, or `Antigravity`
- `Status`: `Ready`, `Claimed`, `In progress`, `Review needed`, `Blocked`, or `Done`
- `Work type`: `Protocol`, `Pilot`, `Skill update`, `Review`, or `Follow-up`

Labels should stay broad and portable:

- `skill-quality`
- `agent-work`
- `blocked`, when useful

Agent routing should primarily use the `Agent` project field, not label proliferation.

## Human intervention

Assign an issue to the maintainer only when the work requires human input. Examples include:

- unclear scope
- merge approval
- external credentials or access
- policy decisions
- unresolved disagreement between agent reviewers

When human intervention is required, set `Status` to `Blocked`, assign the issue to the maintainer,
and comment with the exact question or decision needed.

Agents should skip issues assigned to the maintainer unless explicitly asked to help.

## Work item requirements

Every skill-quality sub-issue should include:

- objective
- owning agent
- scope and files
- relevant skill or skill family
- required evidence format
- self-review requirement
- expected PR shape
- known exclusions

The required evidence format should include:

- baseline failure prompt
- baseline failure transcript or summary
- observed rationalization or failure mode
- skill edit summary
- passing retest prompt
- passing retest transcript or summary
- residual risks

## Orchestrator roles

Codex is the primary implementation orchestrator. It should take the heaviest inventory, protocol,
pilot, and repo-mechanics work.

Antigravity is the secondary implementation orchestrator. It should focus on client realism, install
flows, portability, and whether another agent can follow the protocol.

Claude is the high-leverage reviewer and protocol critic. It should focus on whether the protocol
proves behavior, whether pressure tests catch realistic rationalizations, and whether skill
descriptions trigger correctly without summarizing workflow.

These roles are defaults, not permanent ownership. The project field on each sub-issue is
authoritative.

## Agent work loop

Each orchestrator should repeat this loop until no eligible issue remains:

1. Find open sub-issues in the skill-quality project where `Agent` matches the orchestrator.
2. Skip issues assigned to the maintainer.
3. Skip issues with a recent claim by another agent.
4. Claim one issue by setting `Status` to `In progress` and commenting with the acting agent's name,
   such as `Claimed by Codex.`
5. Work only the claimed issue.
6. Run a local subagent self-review before opening a PR.
7. Open a draft PR linked to the issue.
8. Comment on the issue with the PR link and evidence summary.
9. Set the issue `Status` to `Review needed`.
10. Stop when no eligible issues remain.

Agents should not set timers, poll periodically, or create background monitors unless the maintainer
explicitly asks.

## Workspace handoff checks

Implementation work should happen in an issue-specific isolated worktree and branch. For
review-only work, agents may inspect existing worktrees, but they should not edit them unless the
reviewer first claims an implementation issue and creates or reuses the matching issue-specific
workspace.

Before editing, verify and record these local facts for the handoff:

- issue number and issue title
- branch name and worktree path
- clean baseline from `git status --short --branch`
- expected scope and files from the issue body
- whether the work starts from the intended base branch
- any unrelated local changes that must stay out of the PR

Use branch and worktree names that include the issue number when possible, such as
`codex/issue-63-worktree-handoff-checks`. Work only the claimed issue in that workspace. If an
adjacent finding belongs elsewhere, create or route a follow-up issue instead of expanding the
branch.

Do not delete branches or worktrees as part of the agent handoff unless the maintainer explicitly
asks. Report stale or confusing worktrees as residual risk, and leave cleanup to a human-directed
maintenance pass.

## Self-review before PR

Before opening a PR, the authoring orchestrator must run a local subagent self-review. The
self-review should check:

- the issue scope was followed
- the required evidence format is present
- baseline failure evidence is present
- passing retest evidence is present
- unrelated skill prose was not rewritten
- repo-visible text contains no personal identifiers
- the PR body accurately summarizes evidence and residual risk

The self-review is local subagent review only. It is not external-model evaluation,
and it should not use plugin-style model comparisons unless explicitly requested.

## Cross-agent review

Agents should look for open PRs from other orchestrators that they have not reviewed. They should
also look for issues in `Review needed` assigned to their agent in the project.

Reviewers should claim review work by commenting:

```text
Review claimed by Claude.
```

Use the acting reviewer's name in the comment.

If another recent review claim is present, skip the item.

Review output should be concrete and evidence-oriented. Reviewers should leave findings as comments
or as the repo-defined review artifact. They should not request traditional GitHub review unless the
maintainer asks.

When review is complete, comment:

```text
Review completed by Claude.
```

Use the acting reviewer's name in the comment.

The authoring orchestrator addresses review findings on its own branch.

## Merge gate

The maintainer remains the final merge gate. Agents may prepare PRs, reviews, and evidence, but they
must not merge unless explicitly asked and all documented test gates for the PR have passed.
Agents must not bump MCP server or plugin version numbers unless a human explicitly asks for that
exact action.

## Pilot sequence

The first implementation pass should proceed in this order:

1. Create the parent program issue.
2. Create the skill-quality project and fields.
3. Create the sub-issue template.
4. Create one pilot sub-issue for a single skill.
5. Run the full issue loop on that pilot skill.
6. Review the pilot PR with at least one other orchestrator.
7. Adjust the protocol if the pilot exposes gaps.
8. Only then create additional skill-family sub-issues.

## Future automation

The initial workflow is manually triggered. Agents should not poll for new issues on a timer.

If the workflow proves reliable, a future iteration may add scheduled checks
for new eligible issues.
That automation should preserve the same safeguards:

- skip maintainer-assigned issues
- respect project status
- claim before working
- self-review before PR
- require maintainer approval for merge
