# Cities2 MCP and Modding Toolkit

<!-- mcp-name: io.github.mayor-modder/cities2-mcp -->

Cities2 MCP and Modding Toolkit is a local MCP server and agent skill bundle for Cities: Skylines II game knowledge and modding workflows.

It gives AI agents access to a local, searchable version of the Cities: Skylines II Wiki. It also lets them search the game encyclopedia, if the game is installed locally. This gives agents the ability to answer general knowledge questions about playing the game and offer advice on how to solve problems in your city. It also includes agent skills for creating, inspecting, building, and packaging CS2 mod projects. The modding skills are designed to ensure that mods built with this plugin conform to the best practices documented in the wiki.

## Quick Install

Choose your client: [Claude Code](INSTALL.md#install-in-claude-code) | [Claude desktop](INSTALL.md#install-in-claude-desktop) | [Codex CLI](INSTALL.md#install-in-codex-cli) | [the Codex app](INSTALL.md#install-in-the-codex-app) | [Google Antigravity](INSTALL.md#install-in-google-antigravity)

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

When Cities: Skylines II is installed locally, the MCP server also tries to read the in-game Encyclopedia from the user's own game files. This source is enabled by default when the server can find `Cities2_Data/Content/Game/Locale.cok`, especially for standard Steam installs.

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

Marketplace installs include five user-facing skills:

- `cities2-knowledge`: answers gameplay, city-system, and player-facing patch/update questions.
- `cities2-modding`: handles general modding questions and local mod project workflows.
- `cities2-mod-review`: reviews CS2 mods for safety, maintainability, user value, packaging hygiene, and verification gaps.
- `cities2-mod-debugging`: helps debug CS2 mod build, packaging, runtime, log, UI debugger, and in-game behavior issues.
- `cities2-mod-release`: checks release readiness before packaging, uploading, publishing, or distributing a mod.

The modding quality skills use documented CS2 best practices and negative constraints as defaults, and they require local playtesting before distribution unless you explicitly choose to package an unverified build.

The marketplace install includes these skills. In Claude:

```text
/cities2-knowledge what's new in the latest Cities: Skylines II patch?
/cities2-modding Scaffold a small Cities: Skylines II UI mod in this project folder, then build it.
/cities2-mod-review Review this mod before I publish it.
/cities2-mod-debugging The mod builds but the UI button does not appear in game.
/cities2-mod-release Check whether this mod is ready to package for distribution.
```

In Codex, run `/skills` or type `$` to mention them:

```text
$cities2-mcp:cities2-knowledge what's new in the latest Cities: Skylines II patch?
$cities2-mcp:cities2-modding Scaffold a small Cities: Skylines II UI mod in this project folder, then build it.
$cities2-mcp:cities2-mod-review Review this mod before I publish it.
$cities2-mcp:cities2-mod-debugging The mod builds but the UI button does not appear in game.
$cities2-mcp:cities2-mod-release Check whether this mod is ready to package for distribution.
```

In Antigravity, type `/cities2` and choose a Cities2 skill.

Gameplay and update answers should include compact source notes that mention the
local Game Encyclopedia entries and link to the relevant CS2 Wiki pages when
available.

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

The MCP server runs locally and does not collect telemetry. See
[PRIVACY.md](PRIVACY.md) for details.

## Licensing

The MCP server code is licensed under the MIT License. The included `cities2_mcp/data` corpus is licensed under Creative Commons Attribution-ShareAlike 3.0; source attribution and transformation notes are in `cities2_mcp/data/ATTRIBUTION.md`.

This project is not developed by, endorsed by, reviewed by, or approved by
Paradox Interactive, Iceflake Studios, Colossal Order, Paradox Wikis, or any
related company. Cities: Skylines II and related names are used referentially.
The bundled wiki corpus contains text adapted from the Cities: Skylines II Wiki
under CC BY-SA 3.0. Non-text wiki media is not included, and local game
Encyclopedia text is read from your own installed game files rather than shipped
with this package. Additional third-party notices are in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
