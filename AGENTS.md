# Agent rules

*For maintaining the Cities2-MCP repo*

## Workspace safety

- Do not delete protected files, including `.DS_Store`, unless the user explicitly asks.
- Before editing, run `git status --short --branch`.
- Do not edit the `main` checkout for branch or PR work unless the user explicitly asks.
- Use the active client's native workspace or worktree mechanism when available,
  especially when the maintainer needs in-client review tools.
  Fall back to manual Git worktrees only when no native mechanism is available.
- If the checkout is stale, detached, behind remote, or not the intended branch,
  stop and switch to the correct worktree before editing.
- Preserve touched files' existing line-ending style.
  If Git warns about line endings,
  check and normalize only touched files back to the repository/indexed style.

## Commit and PR safety

- Do not commit or push unless the user explicitly asks for the current branch or PR.
- Preparing a diff is allowed; committing and pushing require user agreement.
- After a pushed branch has an open PR,
  offer to update the PR description or metadata to reflect pushed changes
  unless the user has asked otherwise.
- When writing, editing, or commenting on a PR,
  append a co-author line naming the acting agent at the bottom on its own line,
  such as `*Co-authored by Codex.*` or `*Co-authored by Claude.*`.

## Merge and release gates

- Do not merge PRs, tag releases, publish packages,
  or perform irreversible release actions while a user-stated validation gate is pending.
- If the user has said they want to test, review, or verify something first,
  stop after preparatory work and report that the gate is still pending.
- This repository uses squash merging.
  Use `gh pr merge <number> --squash`
  unless the user explicitly requests a different allowed strategy.
- Do not manually delete branches unless asked.

## Required test gates

- Do not merge a PR until every documented test gate relevant to that PR has passed.
- Code/package changes require `python -m unittest discover -s tests -v`.
- Plugin payload changes require `python -m cities2_mcp.plugin_packages check`.
- Skill behavior changes require the relevant pressure tests under
  `docs/superpowers/pressure-tests/cs2-modding-quality/`.
- Plugin install or client-integration changes require the client install
  and all-skills smoke process documented under `docs/superpowers/evaluations/`.
- The all-skills smoke test means installing the plugin in the affected client,
  confirming the MCP server starts,
  then exercising `cities2-knowledge`, `cities2-modding`, `cities2-mod-review`,
  `cities2-mod-debugging`, and `cities2-mod-release`.
- If the needed evaluation document is absent,
  stop and ask where the current documented procedure lives.

## Skill work

- Agent contributors editing `SKILL.md` files must have access to Superpowers.
  Before editing a skill file, use `superpowers:writing-skills`,
  then follow the repository's documented skill-testing protocol.
- For multi-agent skill-quality work,
  follow `docs/superpowers/specs/2026-06-01-skill-quality-agent-workflow.md`.

## Markdown style

- Use sentence case for Markdown headings,
  preserving proper nouns, product names, acronyms, and code identifiers.
- For Markdown prose, use semantic line breaks at sentence or clause boundaries,
  and avoid orphaned single-word lines.
- Follow the file's dominant wrapping style when editing existing docs.
- Do not reflow unrelated text unless the user explicitly asks.
- Do not wrap code blocks, tables, URLs, generated output, front matter,
  or text where line breaks are meaningful.
