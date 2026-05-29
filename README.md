# Cities2-MCP

<!-- mcp-name: io.github.mayor-modder/cities2-mcp -->

Cities2-MCP — a local MCP server for Cities: Skylines II game knowledge and modding tools.

It gives AI agents access to a local, searchable version of the Cities: Skylines II Wiki and game encyclopedia, if the game is installed. It also offers tools for creating, inspecting, building, and packaging CS2 mod projects.

## Quick Install

Choose your client: [Claude Code](INSTALL.md#install-in-claude-code) | [Claude Desktop](INSTALL.md#install-in-claude-desktop) | [Codex CLI](INSTALL.md#install-in-codex-cli) | [Codex Desktop](INSTALL.md#install-in-codex-desktop)

See [INSTALL.md](INSTALL.md) for full installation details, direct MCP config,
workspace setup, build prerequisites, and troubleshooting.

## What It Can Do

### Search Game And Modding Information

The server includes a prepared text corpus from the Cities: Skylines II Wiki. An AI assistant can:

- search the wiki
- retrieve reference-style snippets for game systems and modding topics
- answer questions during your agent session

This is useful for questions about game mechanics, modding APIs, toolchain setup, project structure, localization, UI mods, and related CS2 development topics.

### Search The Local Game Encyclopedia

When Cities: Skylines II is installed locally, Cities2-MCP also tries to read the in-game Encyclopedia from the user's own game files. This source is enabled by default when the server can find `Cities2_Data/Content/Game/Locale.cok`, especially for standard Steam installs.

The extracted Encyclopedia index is cached locally on the user's machine and rebuilt only when the source game file, detected Steam build id, locale, or extractor version changes. Extracted game text is not committed to this repository, shipped in releases, or part of the redistributed wiki corpus.

If the game install is not found automatically, set `CITIES2_GAME_DIR` to the Cities: Skylines II install directory or `CITIES2_LOCALE_COK` to the full `Locale.cok` path.

### Help With Mod Project Workflows

The server also includes local workflow tools for CS2 mod projects. An AI assistant can:

- scaffold C# code, UI, or hybrid mod project templates
- write files inside configured workspaces
- list project trees
- run project builds and analyzers
- package project output
- dry-run launching Cities: Skylines II with selected flags

These tools are meant for local development workflows. They can write files and run commands, so configure workspaces deliberately.

## Agent Skills

Skills live under `skills/`:

- `skills/cities2-knowledge/SKILL.md`
- `skills/cities2-modding/SKILL.md`

The marketplace install includes these skills. In Codex, run `/skills` or type
`$` to mention `$cities2-mcp:cities2-knowledge` or
`$cities2-mcp:cities2-modding`; Claude exposes them as `/cities2-knowledge` and
`/cities2-modding`. Gameplay and update answers should include compact source
notes that mention the local Game Encyclopedia entries and link to the relevant
CS2 Wiki pages when available.

Project templates are stored at:

- `cities2_mcp/templates/cities2-csharp`
- `cities2_mcp/templates/cities2-ui`
- `cities2_mcp/templates/cities2-hybrid`

## MCP Tools

Game and modding knowledge:

- `search(query, limit=5)`
- `get_page(page_id)`
- `query_reference(query, limit=5)`
- `get_snippets(query, limit=3)`
- `search_encyclopedia(query, limit=5)`
- `get_encyclopedia_entry(entry_id)`
- `source_status()`

Mod project workflow:

- `scaffold_project(name, template, target_dir?, metadata?, options?)`
- `write_project_file(project_dir, relative_path, content, mode=create|replace|upsert)`
- `list_project_tree(project_dir, glob="**/*", include_hidden=false, max_files=2000)`
- `build_project(project_dir, profile=debug|release, steps?, clean=false, package=false, timeout_sec=300)`
- `analyze_project(project_dir, profile=auto|cities2-csharp|cities2-ui|cities2-hybrid, strict=true)`
- `package_project(project_dir, output_dir?, package_name?, exclude_globs?)`
- `launch_cities2(executable?, flags?, platform=auto|mac|windows|linux, dry_run=true)`

## Included Wiki Corpus

The packaged server reads the prepared corpus from `cities2_mcp/data` by default. The corpus contains page metadata and JSONL indexes used by the MCP retrieval tools.

Corpus layout:

- `cities2_mcp/data/LICENSE`
- `cities2_mcp/data/ATTRIBUTION.md`
- `cities2_mcp/data/manifest.json`
- `cities2_mcp/data/index/pages.jsonl`
- `cities2_mcp/data/index/chunks.jsonl`

## Privacy

Cities2-MCP runs locally and does not collect telemetry. See
[PRIVACY.md](PRIVACY.md) for details.

## Licensing

The MCP server code is licensed under the MIT License. The included `cities2_mcp/data` corpus is licensed under Creative Commons Attribution-ShareAlike 3.0; source attribution and transformation notes are in `cities2_mcp/data/ATTRIBUTION.md`.