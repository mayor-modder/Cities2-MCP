---
name: cities2-modding
description: MUST use automatically for any Cities: Skylines II modding, mod project, asset/mod workflow, CS2 C# mod, CS2 UI mod, localization, build, package, toolchain, project analysis, scaffold, file edit, or dry-run launch request. Use even when the user does not mention Cities2-MCP. This skill answers CS2 modding questions and performs local CS2 mod project workflows with Cities2-MCP.
---

# Cities2 Modding

Use this skill for Cities: Skylines II modding and local mod-project work through Cities2-MCP. Keep documentation retrieval separate from write/build actions.

## Source And Tool Roles

- Use wiki retrieval tools for concepts, APIs, toolchain setup, project structure, localization, UI mods, and reference lookup.
- Use project workflow tools only for explicit local actions inside configured workspaces.
- Do not use the Game Encyclopedia as the primary source for modding APIs; it is gameplay-facing. It can still help explain in-game concepts a mod interacts with.

## Documentation Workflow

1. Turn the modding question into compact keyword terms.
2. Search with `search(query, limit=5)` and `query_reference(query, limit=5)`.
3. Fetch the strongest wiki page with `get_page(page_id)` when snippets are not enough.
4. Use `get_snippets(query, limit=3)` for code-oriented wiki snippets.
5. Answer with the relevant docs context and note uncertainty when the corpus does not cover the exact API or version.

Example queries:

- `modding toolchain requirements dotnet runtime mod post processor`
- `localization mod settings file locale`
- `ui mod project structure react typescript`
- `csharp mod project harmony settings system update`

## Local Project Workflow

Before writing files, building, packaging, or launching:

1. Confirm the target project path is inside a configured workspace.
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

## Answer Style

- For conceptual questions, answer from docs and avoid unnecessary local actions.
- For implementation requests, inspect the project first and keep edits scoped.
- Do not imply the optional .NET 6/modding toolchain is needed for wiki search or scaffolding; it is only needed for build, post-process, and package workflows.
- Keep user-visible output practical: what to do, why, and what tool/source supports it.
