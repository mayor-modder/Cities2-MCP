# Agent Rules

- Do not delete protected files. This includes system metadata files like `.DS_Store` and any other files the user has not explicitly asked to remove.
- Do not merge PRs, tag releases, publish packages, delete branches, or perform other irreversible repo/release actions while a user-stated validation gate is still pending. Casual approval is enough only when it directly responds to that action and no earlier stated gate remains unresolved. If the user has said they want to test, review, or verify something first, stop after preparatory work and report that the gate is still pending.
- In this Windows workspace, skip `rg`/ripgrep. It commonly fails here with Windows `Access is denied`, so use the PowerShell search fallbacks directly.
- `rg`/ripgrep is optional tooling, not a requirement. In other workspaces, prefer it only when it is available and successfully runs; if it is missing, blocked, or fails, immediately fall back instead of stopping.
- Recommended search fallbacks:
  - PowerShell file list: `Get-ChildItem -Recurse -File`
  - PowerShell text search: `Get-ChildItem -Recurse -File | Select-String -Pattern "term"`
  - CMD text search: `findstr /S /N /I "term" *`
  - POSIX text search: `grep -RIn --exclude-dir=.git "term" .`
