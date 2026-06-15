---
name: cities2-modding
description: "Use when working on Cities: Skylines II modding, mod projects, C#/UI mods, localization, scaffold, analyze, build, package, or playtesting handoff requests."
metadata:
  short-description: "Use CS2 docs and mod workflow tools"
---

# Cities2 Modding

Use this skill for Cities: Skylines II modding and local mod-project work through Cities2-MCP. Keep documentation retrieval separate from write/build actions.

Trigger this skill for asset/mod workflows, toolchain questions, project analysis, file edits, scaffolding, build/package/install work, or local playtesting handoffs, even when the user does not mention this plugin.

## Source And Tool Roles

- Use wiki retrieval tools for concepts, APIs, toolchain setup, project structure, localization, UI mods, and reference lookup.
- Use project workflow tools only for explicit local actions inside configured workspaces.
- Do not use the game encyclopedia as the primary source for modding APIs; it is gameplay-facing. It can still help explain in-game concepts a mod interacts with.

## Specialized Skill Routing

Use this skill as the general entry point, then load the focused skill when the task calls for it:

- Use `cities2-mod-review` for review, audit, quality, readiness, maintainability, safety, user-value, or "what should I improve?" requests.
- Use `cities2-mod-debugging` for build failures, package failures, runtime errors, game logs, UI debugger issues, or in-game mod behavior that does not work.
- Use `cities2-mod-release` for public package, publish, upload, distribute, release, Paradox Mods preparation, or public sharing requests.

When a general modding answer includes these follow-up areas, make the route explicit in the user-visible handoff: name `cities2-mod-release` for release readiness or public distribution follow-up, and name `cities2-mod-debugging` for runtime, log, UI debugger, or in-game failure follow-up. Do this even when you also provide immediate next steps. In the final answer, say which focused workflow should handle each follow-up, for example: "Use `cities2-mod-release` for release readiness after local playtesting" and "Use `cities2-mod-debugging` if the in-game UI does not appear."

Local package/install steps after a build or fix are allowed when their purpose
is playtesting. Treat them as playtesting handoff moments, not distribution. For
public package, publish, upload, distribute, or release requests, require the
release-readiness workflow.

## Documentation Workflow

1. Turn the modding question into compact keyword terms.
2. Search with `search(query, limit=5)` and `query_reference(query, limit=5)`.
3. For implementation, review, debugging, or release decisions, search for task-specific documented best practices and negative constraints. Useful terms include `best practice`, `recommended`, `should`, `do not`, `should not`, `must not`, `cannot`, `can't`, and `won't`.
4. Fetch the strongest wiki page with `get_page(page_id)` when snippets are not enough.
5. Use `get_snippets(query, limit=3)` for code-oriented wiki snippets.
6. Keep track of source page titles, URLs, and snippet topics.
7. Answer with the relevant docs context and note uncertainty when the corpus does not cover the exact API or version.

Example queries:

- `modding toolchain requirements dotnet runtime mod post processor`
- `localization mod settings file locale`
- `ui mod project structure react typescript`
- `csharp mod project harmony settings system update`

## Local Project Workflow

Before writing files, building, packaging, or preparing playtesting handoff steps:

1. Confirm the target project path is inside a configured workspace.
   - If no trusted mod projects folder is configured, or the requested project
     is outside it, do not present this as a tool failure. Tell the user the
     knowledge tools still work, but local mod workflow tools need an allowed
     folder before they can read/write/build projects.
   - Offer the user the practical fix: add the specific mod project folder, or
     preferably add the parent folder that contains all of their CS2 mod
     projects so future projects under it work too.
   - In Claude desktop, direct the user to the plugin/extension
     settings and the `Trusted mod projects folder` option. If the agent has
     local file/command access, offer to fix the Claude desktop setting directly:
     identify the relevant settings file or app-managed config, ask before
     editing it, back it up, and set the folder to either this project or a
     shared parent folder. In Claude Code, project-scoped plugin installs
     normally use the current project automatically.
   - In Codex, plugin-bundled MCP servers may launch from the installed plugin
     cache rather than the current session folder. If a Codex MCP workflow tool
     is allowlist-blocked for the active project, do not describe that as a
     successful MCP workflow-tool run. Either help the user add a project-scoped
     MCP configuration for that workspace, or use normal Codex workspace file
     edits/shell commands as an explicit fallback and say the MCP workflow tool
     was blocked.
   - If falling back after `scaffold_project` is blocked, do not hand-roll a new
     mod template from wiki prose. Copy the bundled template files
     from the installed package/plugin cache when available, preserving the
     bundled structure, dependencies, and current corpus-derived game metadata.
     If the bundled template is not reachable, ask whether to configure MCP
     workspace access before creating files manually.
   - Keep fallback scaffolds minimal and faithful to the requested template. Do
     not add extra libraries, visual polish, demo dashboards, Vite configs, or a
     `game_version`/`gameVersion` value not provided by the bundled template or
     MCP scaffold metadata unless the user explicitly asks for them.
2. Explain the intended local action briefly.
3. Use the narrowest tool for the task:
   - `scaffold_project` for new mod templates.
   - `list_project_tree` before editing unfamiliar projects.
   - `write_project_file` for explicit file changes.
   - `analyze_project` before or after edits to catch structure/toolchain problems.
   - `build_project` for trusted workspace code build/package diagnostics. Do not use it for arbitrary untrusted repositories.
   - `package_project` for distributable output.
   - Provide manual Cities: Skylines II launch and playtesting steps instead of invoking a launch tool.

If a write/build tool returns diagnostics, summarize the actionable errors first and include paths or commands that matter.

When inspecting an unfamiliar or incomplete project, explicitly report package-state evidence before giving build, playtest, or release advice. If package markers or tool output say no generated build output exists, say that no generated build output is present and that there is no installable local artifact yet. Do not call that a successful package, public release candidate, or playable handoff. The next workflow is to restore or scaffold a real project, analyze/build it, then create or install a package/installable artifact for local playtesting.

On Windows, use `npm.cmd` for both install and build commands; do not
try bare `npm` first because execution policy can block `npm.ps1`. Use
native file listing (`Get-ChildItem`) when checking template files or
build outputs instead of assuming `rg` is installed. Verify generated outputs by
checking file existence, size, and a short relevant snippet only; do not dump
large generated files such as `package-lock.json` into the transcript. If the
user asked only to scaffold and build, stop after build verification; do not
start a dev server or browser preview unless the user also asks to run or
preview the UI. In Windows sessions, report Windows paths rather than WSL-style
`/mnt/c/...` paths.

For hybrid C#/UI mods, verify the actual target deploy folder after any local
build or install handoff. The managed DLL, native companion files, UI bundles,
CSS, images, and dependency DLLs should all appear in the intended
`Mods\<ModName>` or package output folder with expected timestamps. Make UI
build scripts emit to the same MSBuild deploy directory, such as `$(DeployDir)`
or an explicit output override, instead of a default live Mods path; otherwise a
temporary or custom C# deploy can silently split managed and UI outputs.

When a build, install, or fix needs in-game validation, provide a playtesting
handoff instead of saying the work is done. Name what was installed, where it was
installed, whether the game or playset must be restarted, the exact in-game
checks to perform, the expected success signal, the likely failure signal, and
relevant evidence such as `Modding.log`, Unity/Player logs, UI debugger output
at `localhost:9444`, installed files, or playset state.

For incomplete-project handoffs, keep the local playtest section concrete even when playtesting is not ready yet: state the package/installable artifact status, then list the evidence required for a future handoff: launch, playset, logs, UI debugger, and confirmation. If there is no installable local artifact, say local playtesting is blocked until one exists, then name the exact package/install step that would unblock it.

Cities: Skylines II must be closed before installing or replacing a local mod
build. If the game is running, stop and tell the user to close Cities: Skylines II before install. After install, tell the user to launch the game,
enable or confirm the playset/mod if needed, and then run the playtest scenario.

If a workflow tool returns a workspace/allowlist/configuration error, pause MCP
workflow-tool retries and help the user configure access before trying that MCP
tool again. Phrase it as a normal setup step, not as a crash: "This plugin can
work on that project after you add its folder, or a shared parent folder, to
Trusted mod projects folder." In Codex, when the plugin cache allowlist blocks
MCP workflow tools, you may use the explicit bundled-template or normal Codex
workspace fallback described above, while saying the MCP workflow tool was
blocked.

When scaffolding a new project, `scaffold_project` chooses a default `game_version`
from the bundled corpus and returns `game_version`, `game_version_source`,
`bundled_game_version`, and any installed-game warning. If the warning says the
installed game appears newer than the bundled package, tell the user
the project was still created and recommend checking for an updated package
release before deeper modding work. If the user names a newer target game
version than the bundled default, pass `metadata.game_version` explicitly.

Do not publish, upload, distribute, or prepare a public release immediately
after code changes or a build unless local playtesting has been confirmed. A
successful build is not enough. Do not block packaging or installing a local
build whose purpose is playtesting; label it as a local playtest artifact, not a
distribution release. If the user has not tested locally before public release,
route to `cities2-mod-release` and provide a tailored playtest checklist. If the
user explicitly overrides the gate, label the result as not gameplay-verified.

## Answer Style

- For conceptual questions, answer from docs and avoid unnecessary local actions.
- For implementation requests, inspect the project first and keep edits scoped.
- Do not imply the optional .NET 6/modding toolchain is needed for wiki search or scaffolding; it is only needed for build, post-process, and package workflows.
- Keep user-visible output practical: what to do, why, and what tool/source supports it.
- When docs were used, include a compact source note at the end. Prefer one short sentence or a `Sources:` line naming the wiki page or snippet topic, with Markdown links for wiki URLs when available.
