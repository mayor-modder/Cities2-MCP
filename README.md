# Cities2-MCP

Cities2-MCP — a local MCP server for Cities: Skylines II game knowledge and modding tools.

It gives AI assistants access to a prepared local corpus of Cities: Skylines II Wiki text, plus tools for creating, inspecting, building, and packaging CS2 mod projects.

## What It Can Do

### Search Game And Modding Information

The server includes a prepared text corpus from the Cities: Skylines II Wiki. An AI assistant can:

- search the bundled wiki corpus
- fetch full pages by page id
- retrieve reference-style snippets for game systems and modding topics
- answer questions without browsing the live wiki during your session

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

### Use Agent Skills

Cities2-MCP ships Agent Skills that teach compatible agents how to query and interpret the MCP sources effectively:

- `cities2-knowledge` answers gameplay and city-system questions from both the bundled wiki corpus and the local game Encyclopedia.
- `cities2-modding` answers modding questions and guides local mod project workflows.

These skills are stored in `skills/`. Install or copy them into your agent's skill directory if your client supports Agent Skills. They are the recommended way to get natural answers to questions like "how do I grow office demand?" because they tell the agent to use keyword queries, fetch full pages or entries, compare source authority, synthesize an answer, and include compact source notes naming the Game Encyclopedia entries and linked wiki pages used.

### Use Slash-Command Style Prompts

Cities2-MCP also exposes MCP prompts that clients can present as slash commands, prompt templates, or picker entries depending on client support:

- `/cities2` answers with both the bundled wiki corpus and the local game Encyclopedia when available.
- `/cities2-wiki` answers using only the bundled wiki corpus.
- `/cities2-encyclopedia` answers using only the local in-game Encyclopedia read from the user's installed game files.
- `/cities2-modding` answers modding questions with docs and, when explicitly requested, local mod project workflow tools.

These prompts do not load the entire corpus into the model context. They guide the host assistant to check source availability, retrieve the relevant pages or entries, and synthesize an answer with clear source labels. Client support for MCP prompts varies, so use the Agent Skills when available.

## Licensing

The MCP server code is licensed under the MIT License. The internal retrieval layer includes code originally split out as `wiki-mcp`; its MIT notice is preserved in `THIRD_PARTY_NOTICES.md`. The included `data` corpus is licensed under Creative Commons Attribution-ShareAlike 3.0; source attribution and transformation notes are in `data/ATTRIBUTION.md`.

## Prerequisites

Clone the repository:

```bash
git clone https://github.com/mayor-modder/Cities2-MCP.git
```

The wiki retrieval code is included directly under `server/retrieval`, so no submodule setup is required.

Optional mod build/package workflows need the Cities: Skylines II modding
toolchain, `dotnet`, and a .NET 6 runtime. Check with:

```bash
dotnet --list-runtimes
```

Look for `Microsoft.NETCore.App 6.`. This is only required for tools that build,
post-process, or package CS2 mods; wiki search and project scaffolding do not
need it.

## Install In Claude Desktop, Claude Code, Codex, Cursor, etc.

See [INSTALL.md](INSTALL.md) for step-by-step setup instructions. The install guide covers client detection, config file locations, and troubleshooting for supported platforms.

Reference config templates with placeholders are also available at:

- `mcp.config.example.json` for JSON clients
- `INSTALL.md` includes the Codex TOML shape

## Start MCP Server

Run from the repository root:

```bash
CITIES2_MODS_DIR="$HOME/Library/Application Support/Colossal Order/Cities Skylines II/Mods" \
python3 server/mcp_server.py \
  --data-dir data \
  --workspace .
```

Transport is stdio with `Content-Length` framing. The server also accepts newline-delimited JSON for compatibility.

Repeat `--workspace` to allow additional project roots. Relative tool paths resolve from the first workspace. Absolute project paths must live inside one of the configured workspaces.

## Included Wiki Corpus

The server reads the prepared corpus from `data` by default. The corpus contains page metadata and JSONL indexes used by the MCP retrieval tools.

Corpus layout:

- `data/LICENSE`
- `data/ATTRIBUTION.md`
- `data/manifest.json`
- `data/index/pages.jsonl`
- `data/index/chunks.jsonl`

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

## MCP Prompts

Clients that support MCP prompts can expose these as slash commands or prompt templates:

- `cities2(question)` - use both wiki and local Encyclopedia sources.
- `cities2-wiki(question)` - use only the bundled wiki corpus.
- `cities2-encyclopedia(question)` - use only the local game Encyclopedia.
- `cities2-modding(question)` - use docs and local mod project workflow tools for modding tasks.

## Agent Skills

Skills live under `skills/`:

- `skills/cities2-knowledge/SKILL.md`
- `skills/cities2-modding/SKILL.md`
- `skills/cities2-game-updates/SKILL.md`

Install them into a compatible client's skill folder, or keep them in the repo as project-level guidance where supported. The skills depend on the `cities2-mcp` MCP server being configured. Gameplay answers should include compact source notes that mention the local Game Encyclopedia entries and link to the relevant CS2 Wiki pages when available.

Project templates are stored at:

- `server/templates/cities2-csharp`
- `server/templates/cities2-ui`
- `server/templates/cities2-hybrid`

## Migration From Older Tool Names

- `create_mod_project` -> `scaffold_project`
- `add_file` / `update_file` -> `write_project_file`
- `list_project_files` -> `list_project_tree`
- `build_mod` -> `build_project`
- `check_errors` -> integrated in `build_project` diagnostics output
- `package_mod` -> `package_project`
- `export_mod_copy` -> removed; use `package_project` plus an external copy step if needed
- `launch_game_with_flags` -> `launch_cities2`

## Smoke Test

```bash
python3 tests/smoke_mcp.py
```

The smoke test validates MCP initialize/list plus wiki retrieval and mod workflow tools end-to-end.

## Direct CLI

```bash
python3 scripts/workbench_cli.py list-tools
python3 scripts/workbench_cli.py scaffold "My Mod" cities2-csharp
python3 scripts/workbench_cli.py analyze mods/my-mod --profile auto --strict
python3 scripts/workbench_cli.py build mods/my-mod --profile release --steps ui,dotnet
```
