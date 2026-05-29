---
name: cities2-modding
description: "Use automatically for Cities: Skylines II modding, mod projects, C#/UI mods, localization, scaffold, analyze, build, package, and dry-run launch requests."
metadata:
  short-description: "Use CS2 docs and mod workflow tools"
---

# Cities2 Modding

Use this skill for Cities: Skylines II modding and local mod-project work through Cities2-MCP. Keep documentation retrieval separate from write/build actions.

Trigger this skill for asset/mod workflows, toolchain questions, project analysis, file edits, scaffolding, build/package/install work, or local dry-run launches, even when the user does not mention Cities2-MCP.

## Source And Tool Roles

- Use wiki retrieval tools for concepts, APIs, toolchain setup, project structure, localization, UI mods, and reference lookup.
- Use project workflow tools only for explicit local actions inside configured workspaces.
- Do not use the Game Encyclopedia as the primary source for modding APIs; it is gameplay-facing. It can still help explain in-game concepts a mod interacts with.

## Documentation Workflow

1. Turn the modding question into compact keyword terms.
2. Search with `search(query, limit=5)` and `query_reference(query, limit=5)`.
3. Fetch the strongest wiki page with `get_page(page_id)` when snippets are not enough.
4. Use `get_snippets(query, limit=3)` for code-oriented wiki snippets.
5. Keep track of source page titles, URLs, and snippet topics.
6. Answer with the relevant docs context and note uncertainty when the corpus does not cover the exact API or version.

Example queries:

- `modding toolchain requirements dotnet runtime mod post processor`
- `localization mod settings file locale`
- `ui mod project structure react typescript`
- `csharp mod project harmony settings system update`

## Local Project Workflow

Before writing files, building, packaging, or launching:

1. Confirm the target project path is inside a configured workspace.
   - If no trusted mod projects folder is configured, or the requested project
     is outside it, do not present this as a tool failure. Tell the user the
     knowledge tools still work, but local mod workflow tools need an allowed
     folder before they can read/write/build projects.
   - Offer the user the practical fix: add the specific mod project folder, or
     preferably add the parent folder that contains all of their CS2 mod
     projects so future projects under it work too.
   - In Claude Desktop, direct the user to the Cities2-MCP plugin/extension
     settings and the `Trusted mod projects folder` option. If the agent has
     local file/command access, offer to fix the Claude Desktop setting directly:
     identify the relevant settings file or app-managed config, ask before
     editing it, back it up, and set the folder to either this project or a
     shared parent folder. In Claude Code and Codex, project-scoped plugin
     installs normally use the current project automatically; if it is still
     blocked, suggest reinstalling/enabling the plugin from the desired project
     or configuring a parent folder if the host exposes plugin settings.
2. Explain the intended local action briefly.
3. Use the narrowest tool for the task:
   - `scaffold_project` for new mod templates.
   - `list_project_tree` before editing unfamiliar projects.
   - `write_project_file` for explicit file changes.
   - `analyze_project` before or after edits to catch structure/toolchain problems.
   - `build_project` for build/package diagnostics.
   - `package_project` for distributable output.
   - `launch_cities2` only as a dry run unless the user clearly asks to launch.

If a write/build tool returns diagnostics, summarize the actionable errors first and include paths or commands that matter.

If a workflow tool returns a workspace/allowlist/configuration error, stop and
help the user configure access before retrying. Phrase it as a normal setup step,
not as a crash: "Cities2-MCP can work on that project after you add its folder,
or a shared parent folder, to Trusted mod projects folder."

When scaffolding a new project, `scaffold_project` chooses a default `game_version`
from the bundled corpus and returns `game_version`, `game_version_source`,
`bundled_game_version`, and any installed-game warning. If the warning says the
installed game appears newer than the bundled Cities2-MCP package, tell the user
the project was still created and recommend checking for an updated Cities2-MCP
release before deeper modding work. If the user names a newer target game
version than the bundled default, pass `metadata.game_version` explicitly.

## Answer Style

- For conceptual questions, answer from docs and avoid unnecessary local actions.
- For implementation requests, inspect the project first and keep edits scoped.
- Do not imply the optional .NET 6/modding toolchain is needed for wiki search or scaffolding; it is only needed for build, post-process, and package workflows.
- Keep user-visible output practical: what to do, why, and what tool/source supports it.
- When docs were used, include a compact source note at the end. Prefer one short sentence or a `Sources:` line naming the wiki page or snippet topic, with Markdown links for wiki URLs when available.
