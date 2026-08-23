# Agent rules

*For maintaining the Cities2-MCP repo*

## Workspace safety

- Do not delete protected files, including `.DS_Store`, unless the user explicitly asks.
- Before editing, run `git status --short --branch`.
- Do not edit the `main` checkout for branch or PR work unless the user explicitly asks.
- Use the active client's native workspace or worktree mechanism when the maintainer needs in-client review tools. Fall back to manual Git worktrees only when no native mechanism is available.
- If the checkout is stale, detached, behind remote, or not the intended branch, stop and switch to the correct worktree before editing.
- Preserve touched files' existing line-ending style. If Git warns about line endings, check and normalize only touched files back to the repository/indexed style.

## Commit and PR safety

- Do not commit or push unless the user explicitly asks for the current branch or PR.
- Preparing a diff is allowed. Committing and pushing require user agreement.
- After a pushed branch has an open PR, offer to update the PR description or metadata to reflect pushed changes unless the user has asked otherwise.
- When writing, editing, or commenting on a PR, append a co-author line naming the acting agent at the bottom on its own line, such as `*Co-authored by Codex.*` or `*Co-authored by Claude.*`.

## Public-facing writing

- Public documentation, pull request text, release notes, changelogs, issue text, and user-facing messages must contain only information useful to their intended audience: product behavior, relevant context, decisions, instructions, limitations, and verification evidence.
- Do not publish agent inner monologue, reasoning traces, workflow narration, self-justification, conversational asides, or explanations of why the agent chose particular wording, labels, version numbers, or routine process steps unless that rationale is itself necessary for the audience to act correctly.

## Merge and release gates

- Do not merge PRs, tag releases, publish packages, or perform irreversible release actions while a user-stated validation gate is pending.
- If the user has said they want to test, review, or verify something first, stop after preparatory work and report that the gate is still pending.
- Never merge to `main` unless a human explicitly directs that exact action.
- Never bump MCP server or plugin version numbers unless a human explicitly directs that exact action.
- Apply `release:none` to pull requests limited to repository policy, contributor guidance, or other changes that do not alter published package, plugin, server, corpus, or distribution artifacts. Do not use it for changes that affect shipped artifacts.
- Squash merging is the default for ordinary PRs.
- Merge commits are allowed for explicitly stacked PRs. A stacked PR must name its parent PR or branch in the PR description, using a line such as `Stacked on: #123` or `Stacked on: branch-name`.
- Use a merge commit for a stacked PR when landing it with squash would force dependent branches to be restacked. For GitHub CLI merges, use `gh pr merge <number> --merge`.
- Do not squash a PR that has dependent open PRs unless the stack owner has already restacked them or explicitly asks for the squash.
- Unless a PR is explicitly marked as stacked, or the user requests a different allowed strategy, use `gh pr merge <number> --squash`.
- Do not manually delete branches unless asked.

## Required test gates

- Do not merge a PR until every documented test gate relevant to that PR has passed.
- Code/package changes require `python -m unittest discover -s tests -v`.
- Plugin payload changes require: `python -m cities2_mcp.plugin_packages check`.
- Plugin metadata files such as `plugin.json`, `.mcp.json`, plugin `README.md`, `marketplace.json`, and `mcp_config.json` are generated from `cities2_mcp/plugin_metadata.py`; run `python -m cities2_mcp.plugin_packages sync` instead of editing them by hand.
- Skill behavior changes require the relevant pressure tests in: `docs/superpowers/pressure-tests/cs2-modding-quality/`.
- For plugin install or client-integration changes, run the client install and all-skills smoke process documented in: `evals/reports/`.
- The all-skills smoke test means installing the plugin in the affected client, confirming the MCP server starts, and exercising `cities2-knowledge`, `cities2-modding`, `cities2-mod-review`, `cities2-mod-debugging`, and `cities2-mod-release`.
- If the needed evaluation document is absent, stop and ask where the current documented procedure lives.

## Skill work

- Agent contributors editing `SKILL.md` files must have access to Superpowers. Before editing a skill file, use `superpowers:writing-skills`, then follow the repository's documented skill-testing protocol.
- For multi-agent skill-quality work, follow: `docs/superpowers/specs/2026-06-01-skill-quality-agent-workflow.md`.

## Markdown style

- Use sentence case for Markdown headings while preserving proper nouns, product names, acronyms, and code identifiers.
- For Markdown prose, keep each paragraph on a single logical line instead of hard-wrapping at a fixed width.
- When editing existing docs, reflow touched prose to paragraph-per-line style unless the file uses line breaks as meaningful structure.
- Do not reflow unrelated text unless the user explicitly asks.
- Leave these as-is: code blocks, tables, URLs, generated output, metadata blocks, lists where each line is a distinct item, and text where line breaks are meaningful.
