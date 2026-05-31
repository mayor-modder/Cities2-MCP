# Agent Rules

*For maintaining the Cities2-MCP repo*

- Do not delete protected files. This includes system metadata files like `.DS_Store` and any other files the user has not explicitly asked to remove.
- Before editing files, verify the active branch and worktree with `git status --short --branch` and make sure it matches the user's requested branch or PR. Do not edit the `main` branch checkout for branch or PR work unless the user explicitly asks to edit `main`. If a checkout is behind its remote, stale, detached, or not the branch you intend to change, stop and switch to or create the correct worktree before editing.
- Do not merge PRs, tag releases, publish packages, or perform other irreversible repo/release actions while a user-stated validation gate is still pending. Casual approval is enough only when it directly responds to that action and no earlier stated gate remains unresolved. If the user has said they want to test, review, or verify something first, stop after preparatory work and report that the gate is still pending. Do not manually delete branches unless asked; if repository settings automatically delete merged PR branches, no extra warning is needed.
- Do not commit or push changes unless the user explicitly asks you to do so for the current branch or PR. Preparing a diff is allowed, but committing and pushing require user agreement.
- After a branch has already been pushed and a PR exists, agents should offer to update the PR description or metadata to accurately reflect the pushed changes unless the user has asked them not to.
- Do not merge a PR until every documented test gate relevant to that PR has passed. At minimum, code/package changes require `python -m unittest discover -s tests -v`; plugin payload changes require `python -m cities2_mcp.plugin_packages check`; skill behavior changes require the relevant pressure tests under `docs/superpowers/pressure-tests/cs2-modding-quality/`; plugin install or client-integration changes require the client install and all-skills smoke process documented under `docs/superpowers/evaluations/`. The all-skills smoke test means installing the plugin in the affected client, confirming the MCP server starts, then exercising `cities2-knowledge`, `cities2-modding`, `cities2-mod-review`, `cities2-mod-debugging`, and `cities2-mod-release`. If the needed evaluation document is absent from the current branch, stop and ask the user where the current documented procedure lives before merging.
- This repository enforces squash merging. When merging PRs with `gh`, use `gh pr merge <number> --squash` unless the user explicitly requests a different allowed strategy.
- When writing, editing, or commenting on a PR, append `*Authored by Codex.*` at the bottom on its own line, with one blank line between it and any text above.
- `rg`/ripgrep is optional tooling, not a requirement. In other workspaces, prefer it only when it is available and successfully runs; if it is missing, blocked, or fails, immediately fall back instead of stopping.
- If fallback searches were noticeably slower because `rg` was missing or blocked, mention ripgrep as an optional local install in the final note at most once. Do not interrupt the task to suggest it or repeat the suggestion across sessions.
- Recommended search fallbacks:
  - PowerShell file list: `Get-ChildItem -Recurse -File`
  - PowerShell text search: `Get-ChildItem -Recurse -File | Select-String -Pattern "term"`
  - CMD text search: `findstr /S /N /I "term" *`
  - POSIX text search: `grep -RIn --exclude-dir=.git "term" .`
