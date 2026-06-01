# Agent rules

*For maintaining the Cities2-MCP repo*

## Workspace safety

- Do not delete protected files, including `.DS_Store`, unless the user explicitly asks.
- Before editing, run `git status --short --branch`.
- Do not edit the `main` checkout for branch or PR work unless the user explicitly asks.
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

## Markdown style

- Use sentence case for Markdown headings.
- For Markdown prose, use semantic line breaks at sentence or clause boundaries,
  and avoid orphaned single-word lines.
- Follow the file's dominant wrapping style when editing existing docs.
- Do not reflow unrelated text unless the user explicitly asks.
- Do not wrap code blocks, tables, URLs, generated output, front matter,
  or text where line breaks are meaningful.

## Search tooling

- `rg`/ripgrep is optional, not required.
- Prefer `rg` when available; if it is missing, blocked, or fails,
  immediately fall back.
- Mention ripgrep as an optional local install at most once,
  and only if fallback searches were noticeably slower.
- Recommended fallbacks:
  - PowerShell file list: `Get-ChildItem -Recurse -File`
  - PowerShell text search: `Get-ChildItem -Recurse -File | Select-String -Pattern "term"`
  - CMD text search: `findstr /S /N /I "term" *`
  - POSIX text search: `grep -RIn --exclude-dir=.git "term" .`
