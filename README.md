# Cities2-MCP

<!-- mcp-name: io.github.mayor-modder/cities2-mcp -->

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

### Use Slash Commands

Cities2-MCP ships two slash-command skills that teach compatible agents how to query and interpret the MCP sources effectively:

- `cities2-knowledge` answers gameplay, city-system, and player-facing patch/update questions from both the bundled wiki corpus and the local game Encyclopedia.
- `cities2-modding` answers modding questions and guides local mod project workflows.

These skills are stored in `skills/`. Install or copy them into your agent's skill directory if your client supports Agent Skills. They are the recommended way to get natural answers to questions like "how do I grow office demand?" or "what changed in the latest patch?" because they tell the agent to use keyword queries, fetch full pages or entries, compare source authority, synthesize an answer, and include compact source notes naming the Game Encyclopedia entries and linked wiki pages used.

## Licensing

The MCP server code is licensed under the MIT License. The internal retrieval layer includes code originally split out as `wiki-mcp`; its MIT notice is preserved in `THIRD_PARTY_NOTICES.md`. The included `cities2_mcp/data` corpus is licensed under Creative Commons Attribution-ShareAlike 3.0; source attribution and transformation notes are in `cities2_mcp/data/ATTRIBUTION.md`.

## Privacy Policy

Cities2-MCP runs locally on the user's machine. It does not collect telemetry,
send usage data to mayor-modder, or require an account.

The server reads the bundled wiki corpus from the installed package. When
available, it can read the user's local Cities: Skylines II game files to build
a local in-game Encyclopedia cache. If workflow tools are enabled with
`--workspace`, it can read and write files only inside the configured trusted
workspace paths. Build, package, and launch tools may run local development
commands on the user's machine when explicitly invoked by the connected agent.

Cities2-MCP does not share data with third parties. Local cache files remain on
the user's machine. Users can remove the package, MCP client configuration, and
local Encyclopedia cache at any time. Privacy or security issues can be reported
through the GitHub issue tracker.

## Quick Install

The packaged server includes the bundled wiki corpus and can be launched by MCP
clients through `uvx`:

```json
{
  "mcpServers": {
    "cities2-mcp": {
      "command": "uvx",
      "args": [
        "cities2-mcp",
        "--workspace",
        "/absolute/path/to/trusted/mod/workspace"
      ]
    }
  }
}
```

Omit `--workspace` if you only want wiki and local Encyclopedia search. Add one
or more `--workspace` entries when you want the project workflow tools to write,
analyze, build, or package local mod projects.

To install the bundled slash-command skills for Codex and Claude Code, run:

```bash
uvx cities2-mcp install-agent-assets
```

The plain MCP install command only connects the server. This helper installs
the two user-facing agent assets too: `cities2-knowledge` and
`cities2-modding`. For Claude Code it also writes `/cities2-knowledge` and
`/cities2-modding` command files under `~/.claude/commands`.

## Prerequisites

Clone the repository:

```bash
git clone https://github.com/mayor-modder/Cities2-MCP.git
```

The wiki retrieval code is included directly under `cities2_mcp/retrieval`, so no submodule setup is required.

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

## Anthropic Distribution

Cities2-MCP includes two Anthropic package shapes under
`integrations/anthropic/`:

- `claude-plugin/` is the Claude plugin. It bundles the two skills and a
  plugin-local launcher so installing the plugin provides slash commands and
  starts the MCP server automatically. Claude Desktop's Plugins installer can
  also use this package when distributed as a `.zip` or `.plugin` archive.
- `claude-mcpb/` is the Claude Desktop MCPB source. It uses Anthropic's `uv`
  runtime support and vendors the server for one-click local desktop-extension
  installs without asking users to install `uvx` manually.

Local PyPI MCP servers are not listed directly in Anthropic's Connectors
Directory. The plugin is the friendliest install path when users want slash
commands plus the local MCP server. The MCPB is the lower-level Claude Desktop
extension path for extension testing and Connectors Directory submission.

Both Anthropic package shapes expose optional path settings. Wiki search uses
the bundled corpus without any user folder. Mod workflow tools require a trusted
mod projects folder and reject project paths outside that folder.

Before official listing, Claude Code users can add this repository as a plugin
marketplace and install the plugin:

```text
/plugin marketplace add mayor-modder/Cities2-MCP
/plugin install cities2-mcp@cities2-mcp
```

## Start MCP Server

Run from the repository root:

```bash
CITIES2_MODS_DIR="$HOME/Library/Application Support/Colossal Order/Cities Skylines II/Mods" \
python3 server/mcp_server.py \
  --workspace .
```

Transport is stdio with `Content-Length` framing. The server also accepts newline-delimited JSON for compatibility.

Repeat `--workspace` to allow additional project roots. Relative tool paths resolve from the first workspace. Absolute project paths must live inside one of the configured workspaces.

## Included Wiki Corpus

The packaged server reads the prepared corpus from `cities2_mcp/data` by default. The corpus contains page metadata and JSONL indexes used by the MCP retrieval tools.

Corpus layout:

- `cities2_mcp/data/LICENSE`
- `cities2_mcp/data/ATTRIBUTION.md`
- `cities2_mcp/data/manifest.json`
- `cities2_mcp/data/index/pages.jsonl`
- `cities2_mcp/data/index/chunks.jsonl`

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

## Slash Commands

Skills live under `skills/`:

- `skills/cities2-knowledge/SKILL.md`
- `skills/cities2-modding/SKILL.md`

Install them into a compatible client's skill folder, or keep them in the repo as project-level guidance where supported. The skills depend on the `cities2-mcp` MCP server being configured. Gameplay and update answers should include compact source notes that mention the local Game Encyclopedia entries and link to the relevant CS2 Wiki pages when available.

Packaged installs can copy these assets from the wheel:

```bash
uvx cities2-mcp install-agent-assets
```

Use `--client codex` or `--client claude` to target one client. The installer
also removes the old `cities2-game-updates` asset name from the target client
folders so stale commands do not linger after upgrading.

Project templates are stored at:

- `cities2_mcp/templates/cities2-csharp`
- `cities2_mcp/templates/cities2-ui`
- `cities2_mcp/templates/cities2-hybrid`

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
