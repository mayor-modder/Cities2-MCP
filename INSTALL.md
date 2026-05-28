# Installing the Cities2-MCP Server

This guide is written for AI coding agents. If a user asks you to install this MCP server, follow these steps in order.

## Preferred packaged install

For normal users, install through the published Python package with `uvx`:

```json
{
  "mcpServers": {
    "cities2-mcp": {
      "command": "uvx",
      "args": [
        "cities2-mcp",
        "--workspace",
        "<TRUSTED_MOD_PROJECT_OR_PARENT_FOLDER>"
      ],
      "env": {
        "CITIES2_MODS_DIR": "<CITIES2_MODS_DIR>"
      }
    }
  }
}
```

The packaged server includes the bundled wiki corpus, so `--data-dir` is not
needed. Omit `--workspace` only for wiki and local Encyclopedia search; add one
or more `--workspace` entries when the user wants workflow tools to write,
analyze, build, or package local mod projects.

If the user asks for a fresh install or asks you to ignore previous local
checkouts, still prefer the packaged install. Do not clone this repository just
to run the MCP server. Use `uvx cities2-mcp` for the latest published release,
or `uvx --refresh cities2-mcp==0.1.7` when you need to force a clean package
resolution for the current release.

The MCP install command only configures the server. To install the bundled
slash-command skills too, run the package helper after the MCP server is
configured:

```sh
uvx cities2-mcp install-agent-assets
```

Use `--client codex` or `--client claude` to target one client. The helper
copies the two current user-facing assets, `cities2-knowledge` and
`cities2-modding`, and removes the old `cities2-game-updates` asset name from
the target client folders.

Use the source checkout instructions below when developing this repository or
when a user explicitly wants to run from a local clone.

## 1. Prerequisites

Before configuring any client, verify these prerequisites:

### Search tooling

`rg`/ripgrep is optional. If it is not installed, not on `PATH`, or fails to run
with an error such as Windows `Access is denied`, do not block the install.
Use a platform fallback instead:

- **Windows PowerShell file list:** `Get-ChildItem -Recurse -File`
- **Windows PowerShell text search:** `Get-ChildItem -Recurse -File | Select-String -Pattern "term"`
- **Windows CMD text search:** `findstr /S /N /I "term" *`
- **macOS / Linux text search:** `grep -RIn --exclude-dir=.git "term" .`

### Python 3

Find the **full absolute path** to the Python interpreter. Run one of these commands depending on platform:

- **Windows:** `py -3 -c "import sys; print(sys.executable)"`
- **macOS / Linux:** `python3 -c "import sys; print(sys.executable)"`

Store the output as `PYTHON_PATH`. Example: `C:\Users\You\AppData\Local\Programs\Python\Python311\python.exe`

**Important:** Do NOT use `py`, `py.exe`, `python3`, or `python` as the command value in any config. MCP clients spawn processes directly and may not resolve PATH entries, shell aliases, or the Windows `py` launcher. Always use the full absolute path.

### Optional: mod build and package workflows

The base MCP server, wiki search tools, and project scaffolding tools do not require the .NET runtime checks below. They only need Python and the local corpus.

If the user wants the MCP tools to build, post-process, or package Cities: Skylines II mods, also verify the CS2 mod build prerequisites:

1. The Cities: Skylines II modding toolchain is installed from inside the game.
2. `dotnet` is available on `PATH`.
3. `dotnet --list-runtimes` includes `Microsoft.NETCore.App 6.`.

The CS2 toolchain's `ModPostProcessor` and `ModPublisher` target `Microsoft.NETCore.App` version `6.0.0`. A newer runtime such as .NET 8 does not necessarily satisfy this requirement. If `Microsoft.NETCore.App 6.` is missing and the user asked for mod build/package readiness, install the Microsoft .NET 6 runtime for the current platform or tell the user exactly what is missing and that wiki/search-only MCP use is still available.

## 2. Resolve local values

You need four required values. There is also one optional game-directory override for non-standard installs. Determine them now before writing any config.

| Value | How to resolve |
|---|---|
| `PYTHON_PATH` | The full absolute path from step 1. |
| `REPO_ROOT` | The absolute path to this repository's root directory (the directory containing this `INSTALL.md` file). |
| `CITIES2_MODS_DIR` | **Windows:** Expand `%LOCALAPPDATA%Low\Colossal Order\Cities Skylines II\Mods` (typically `C:\Users\<username>\AppData\LocalLow\Colossal Order\Cities Skylines II\Mods`). **macOS:** `~/Library/Application Support/Colossal Order/Cities Skylines II/Mods`. **Linux:** `~/.local/share/Colossal Order/Cities Skylines II/Mods`. |
| `CITIES2_GAME_DIR` | Optional. Usually auto-detected for Steam installs. Set this only when `source_status()` reports that the Game Encyclopedia was not found. Point it at the Cities: Skylines II install directory, not the `Cities2_Data` directory. |
| `WORKSPACE_ROOTS` | Trusted folders where MCP workflow tools may read/write/build projects. Always include `REPO_ROOT`. If the user wants to analyze, build, package, or edit existing mod repos, also include those repo paths or a trusted parent folder containing them, such as the user's mod-projects folder. |

Advanced: if `CITIES2_GAME_DIR` is not enough, set `CITIES2_LOCALE_COK` to the full path of the specific `Locale.cok` file.

`--workspace` is a safety allowlist for workflow tools that write, build, or package projects. Repeat it once for each entry in `WORKSPACE_ROOTS`. Absolute project paths outside the configured workspaces are rejected with `Path must stay inside configured workspaces`.

### Slash commands

Cities2-MCP ships slash-command skills in the `skills/` directory. These are recommended because they teach the agent how to query the wiki and local Encyclopedia with keywords, fetch full source records, compare source authority, synthesize answers, and include compact source notes with Encyclopedia entry names and wiki links.

- `skills/cities2-knowledge` - gameplay, city-system, patch, and game-update questions using wiki plus local Encyclopedia.
- `skills/cities2-modding` - modding questions and local mod project workflows.

Install these skills into the client's supported skill directory if the client does not load project-level skills automatically. The skills depend on the `cities2-mcp` MCP server being configured first.

## 3. Detect installed clients

A client can be installed even if its config file does not exist yet — many clients only create config files on demand.

> **IMPORTANT — always include yourself.** If you are an AI agent running inside a client (Claude Code, Cursor, Codex, etc.), that client is installed by definition. Add it to the detected list regardless of whether its config file exists yet. Do not skip yourself.

Do not collapse Claude clients into one entry. Claude Desktop app MCP settings and Claude Code MCP settings are separate, even when Claude Code is used inside the Desktop app. An agent may not be able to tell which one the user means from context. If the user asks to install for "Claude" or "Claude Code" and both surfaces might matter, ask the user which Claude surface they want: Claude Desktop app MCP settings, Claude Code MCP settings, or both.

Use all of the following checks to build the full list of installed clients:

1. **You are a client.** Identify which client you are running in and include it unconditionally.
2. **Config file exists:** Check the standard paths below for each platform.
3. **Binary on PATH:** Also check if other client commands are available (e.g. `claude --version`, `cursor --version`, `codex --version`). Include any that respond.

For each detected config file, read it and check for existing Cities2-MCP entries:

1. **Current name:** `cities2-mcp` (in `mcpServers` for JSON clients, or `[mcp_servers.cities2-mcp]` for Codex TOML).
2. **Legacy names:** also check for `cities2-modding-workbench`, `cities2Workbench`, `cities2-workbench`, or any key containing `cities2` (case-insensitive). These are older versions of this server config.

Classify each detected client into one of three states:

| State | Meaning | Action in step 4 |
|---|---|---|
| **Up to date** | Has a `cities2-mcp` entry using packaged `uvx cities2-mcp`, or a source checkout entry with the current `--data-dir` flag | Exclude from the picker — already installed |
| **Outdated** | Has a legacy-named entry or uses old flags (`--chunks`, `--pages` instead of `--data-dir`) | Include in the picker — describe as "outdated entry will be replaced" |
| **Not installed** | No matching entry found | Include in the picker — describe as "entry needs to be added" (or "config file will be created" if the file doesn't exist yet) |

When writing the config in step 4, if replacing an outdated entry, remove the old entry entirely before adding the new one.

If *all* detected clients are already up to date, inform the user that it is already installed everywhere and skip to step 5 (Verify).

### Windows

| Client | Global config path |
|---|---|
| Claude Desktop | Agents can edit `claude_desktop_config.json` directly. Use `Settings > Developer > Edit Config` only to confirm the active file if needed. Default path: `%APPDATA%\Claude\claude_desktop_config.json`. |
| Claude Code | `%USERPROFILE%\.claude.json` |
| Codex | `%USERPROFILE%\.codex\config.toml` |
| Cursor | `%USERPROFILE%\.cursor\mcp.json` |

### macOS

| Client | Global config path |
|---|---|
| Claude Desktop | Agents can edit `claude_desktop_config.json` directly. Use `Settings > Developer > Edit Config` only to confirm the active file if needed. Default path: `~/Library/Application Support/Claude/claude_desktop_config.json`. |
| Claude Code | `~/.claude.json` |
| Codex | `~/.codex/config.toml` |
| Cursor | `~/.cursor/mcp.json` |

### Linux

| Client | Global config path |
|---|---|
| Claude Code | `~/.claude.json` |
| Codex | `~/.codex/config.toml` |
| Cursor | `~/.cursor/mcp.json` |

### Project-level alternatives

Global config is the tested install path for this guide. If the user explicitly requests project-level install, first check that the target client supports project-level MCP configuration and use that client's documented project config path. Claude Code's shared project-level MCP config is `.mcp.json` at the project root. If you cannot verify project-level support for the requested client, install globally and tell the user why.

### Ask the user

Ask the user which detected clients to install into. If your runtime has an interactive question tool, use it with an "All detected (Recommended)" option plus one option per detected client. If no such tool is available, ask in plain text.

Install globally by default. Only use project-level config if the user explicitly requests it.

## 4. Write the config

### JSON clients (Claude Desktop, Cursor)

These clients all use a `mcpServers` key in their JSON config. Add the following entry inside the existing `mcpServers` object. If `mcpServers` does not exist, create it.

**If the config file already exists**, read it, add the entry, and write it back — do not overwrite unrelated settings. **If the config file does not exist**, create it with just the `mcpServers` key containing the entry below.

Replace `PYTHON_PATH`, `REPO_ROOT`, `CITIES2_MODS_DIR`, and any additional
workspace paths with the values resolved in step 2. On Windows, use
double-backslash escaping in JSON strings (e.g., `C:\\Users\\You\\...`). On
macOS and Linux, use forward slashes.

In the examples below, the first `--workspace` entry is `REPO_ROOT`. Add more
`"--workspace", "<TRUSTED_MOD_PROJECT_OR_PARENT_FOLDER>"` pairs for any existing
mod repos the user wants the MCP workflow tools to operate on.

```json
{
  "cities2-mcp": {
    "command": "<PYTHON_PATH>",
    "args": [
      "<REPO_ROOT>/server/mcp_server.py",
      "--data-dir",
      "<REPO_ROOT>/data",
      "--workspace",
      "<REPO_ROOT>"
    ],
    "env": {
      "CITIES2_MODS_DIR": "<CITIES2_MODS_DIR>"
    }
  }
}
```

Do not add `CITIES2_GAME_DIR` unless automatic discovery fails or the user has a non-standard install location. If needed, add it to the MCP server environment with the game install directory as its value.

This block goes **inside** the `mcpServers` key, not at the top level. For example, if the file already has:

```json
{
  "mcpServers": {
    "some-other-server": { ... }
  }
}
```

It should become:

```json
{
  "mcpServers": {
    "some-other-server": { ... },
    "cities2-mcp": {
      "command": "<PYTHON_PATH>",
      "args": [
        "<REPO_ROOT>/server/mcp_server.py",
        "--data-dir",
        "<REPO_ROOT>/data",
        "--workspace",
        "<REPO_ROOT>"
      ],
      "env": {
        "CITIES2_MODS_DIR": "<CITIES2_MODS_DIR>"
      }
    }
  }
}
```

Do not add `CITIES2_GAME_DIR` unless automatic discovery fails or the user has a non-standard install location. If needed, add it to the MCP server environment with the game install directory as its value.

### Claude Code

Prefer the Claude Code MCP command instead of hand-editing `~/.claude.json`:

```sh
claude mcp add-json cities2-mcp '{"type":"stdio","command":"<PYTHON_PATH>","args":["<REPO_ROOT>/server/mcp_server.py","--data-dir","<REPO_ROOT>/data","--workspace","<REPO_ROOT>"],"env":{"CITIES2_MODS_DIR":"<CITIES2_MODS_DIR>"}}' --scope user
```

On Windows PowerShell, avoid complex command-line escaping by using a here-string:

```powershell
$json = @'
{"type":"stdio","command":"<PYTHON_PATH>","args":["<REPO_ROOT>/server/mcp_server.py","--data-dir","<REPO_ROOT>/data","--workspace","<REPO_ROOT>"],"env":{"CITIES2_MODS_DIR":"<CITIES2_MODS_DIR>"}}
'@
claude mcp add-json cities2-mcp $json --scope user
```

Do not add `CITIES2_GAME_DIR` unless automatic discovery fails or the user has a non-standard install location. If needed, add it to the MCP server environment with the game install directory as its value.

Use `--scope project` only if the user explicitly wants a shared project-level `.mcp.json` file.
If the user wants workflow tools to operate on existing mod repos, add more
`"--workspace","<TRUSTED_MOD_PROJECT_OR_PARENT_FOLDER>"` pairs to the JSON before
running the command. If the Claude Code command fails because of shell quoting,
edit `~/.claude.json` directly using the JSON client shape above, preserving all
unrelated settings.

### Codex (TOML)

Add this block to the Codex config file. If the file does not exist, create it.

```toml
[mcp_servers.cities2-mcp]
command = "<PYTHON_PATH>"
args = [
  "<REPO_ROOT>/server/mcp_server.py",
  "--data-dir",
  "<REPO_ROOT>/data",
  "--workspace",
  "<REPO_ROOT>"
]

[mcp_servers.cities2-mcp.env]
CITIES2_MODS_DIR = "<CITIES2_MODS_DIR>"
```

Do not add `CITIES2_GAME_DIR` unless automatic discovery fails or the user has a non-standard install location. If needed, add it to the MCP server environment with the game install directory as its value.

### Other / generic MCP client

For any MCP client not listed above, use the JSON shape from the "JSON clients" section. Consult that client's documentation for where to place MCP server configuration.

## 5. Install Agent Skills

If the selected client supports Agent Skills, install the bundled Cities2-MCP skills after configuring the MCP server. These skills teach the agent how to query and interpret the wiki corpus plus local Game Encyclopedia, then cite the specific source pages or entries used.

Install the user-facing skill folders:

- `<REPO_ROOT>/skills/cities2-knowledge`
- `<REPO_ROOT>/skills/cities2-modding`

For packaged installs, prefer the package helper:

```sh
uvx cities2-mcp install-agent-assets
```

This installs Codex skills under `~/.codex/skills`. For Claude Code it installs
skills under `~/.claude/skills` and creates `/cities2-knowledge` and
`/cities2-modding` command files under `~/.claude/commands`. Use
`uvx cities2-mcp install-agent-assets --client codex` or
`uvx cities2-mcp install-agent-assets --client claude` when only one client
should be updated.

For a project-specific Claude Code install, run:

```sh
uvx cities2-mcp install-agent-assets --client claude --claude-scope project --claude-project-dir <PROJECT_DIR>
```

The helper removes stale `cities2-game-updates` assets by default. Add
`--keep-legacy` only if the user explicitly wants to keep that old command.

### Claude Code plugin

The tracked Claude Code plugin source lives at
`integrations/anthropic/claude-plugin`. It bundles the two skills, a
plugin-local MCP launcher, a vendored copy of the Python package, and
`.mcp.json`.

This plugin path is best for Claude Code distribution because Anthropic plugins
can bundle skills and MCP servers together. When the plugin is enabled, Claude
Code starts the plugin-provided `cities2-mcp` server automatically. The plugin
sets `--workspace` to `${CLAUDE_PROJECT_DIR}`, so workflow tools are confined
to the current Claude Code project.

Before official listing, install through this repository's marketplace:

```text
/plugin marketplace add mayor-modder/Cities2-MCP
/plugin install cities2-mcp@cities2-mcp
```

Validate the plugin from the repository root:

```sh
claude plugin validate integrations/anthropic/claude-plugin --strict
claude plugin validate . --strict
```

### Claude Desktop MCPB

The tracked Claude Desktop extension source lives at
`integrations/anthropic/claude-mcpb`. This is the correct Anthropic package
shape for a local PyPI-backed MCP server; local PyPI MCP servers are not listed
directly in the Connectors Directory. This is also the preferred path for end
users who should not have to know about `uvx`.

Build and validate it from the MCPB directory:

```sh
cd integrations/anthropic/claude-mcpb
npx @anthropic-ai/mcpb pack
```

The MCPB wrapper vendors the server package and wiki corpus, so local Desktop
testing does not depend on the matching PyPI release already existing. The
manifest includes optional Claude Desktop settings for a trusted workspace, Mods
directory, game install directory, and direct `Locale.cok` path.

### Claude Desktop plugin package

Claude Desktop's Plugins UI can also install the same plugin package used by
Claude Code when it is distributed as a `.zip` or `.plugin` archive. This is the
friendlier path when users want the slash commands and the local MCP server in
one install.

For local testing, package the contents of `integrations/anthropic/claude-plugin`
so the archive root contains `.claude-plugin/plugin.json`, `.mcp.json`,
`skills/`, `bin/`, and `vendor/`. The archive may use either `.zip` or
`.plugin`.

### Codex skills

For Codex, copy the skill directories into the user's Codex skills folder:

| Platform | Codex skills folder |
|---|---|
| Windows | `%USERPROFILE%\.codex\skills` |
| macOS / Linux | `~/.codex/skills` |

On Windows PowerShell:

```powershell
$src = "<REPO_ROOT>/skills"
$dst = "$env:USERPROFILE/.codex/skills"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -Recurse -Force "$src/cities2-knowledge" "$dst/cities2-knowledge"
Copy-Item -Recurse -Force "$src/cities2-modding" "$dst/cities2-modding"
```

On macOS or Linux:

```sh
mkdir -p ~/.codex/skills
cp -R "<REPO_ROOT>/skills/cities2-knowledge" ~/.codex/skills/
cp -R "<REPO_ROOT>/skills/cities2-modding" ~/.codex/skills/
```

### Other clients

For Claude Code, custom slash command files live in `~/.claude/commands` for
user-wide commands or `.claude/commands` for project commands. The package
helper writes those command files automatically. If installing manually, create
`cities2-knowledge.md` and `cities2-modding.md` in the appropriate commands
folder and make each command tell the agent to use the connected `cities2-mcp`
MCP server plus the matching skill workflow.

For Cursor or other clients that support skills, use that client's documented
skill-install location or project-level skill mechanism. If the client does not
support Agent Skills, skip this step; the MCP server tools still work.

Do not copy skills into a client's directory if that client does not support skills.

## 6. Verify

After writing the config, test that the server starts and responds. Run this from
`REPO_ROOT` with the same Python interpreter used in the MCP config:

```
<PYTHON_PATH> tests/smoke_mcp.py
```

The smoke test validates MCP initialize/list, wiki retrieval tools, resource
listing, and mod workflow tools using a temporary workspace. It does not require
the optional CS2/.NET build prerequisites.

`source_status()` may report that the Game Encyclopedia is unavailable on machines without Cities: Skylines II installed. That is a warning, not an install failure.

You can also do a quick local tool-list check:

```sh
<PYTHON_PATH> scripts/workbench_cli.py list-tools
```

The expected Cities2-MCP tool names are:

- `search`
- `get_page`
- `query_reference`
- `get_snippets`
- `scaffold_project`
- `write_project_file`
- `list_project_tree`
- `build_project`
- `analyze_project`
- `package_project`
- `launch_cities2`

If either command fails, check that Python 3 is working and that the repository
contains `cities2_mcp/retrieval/mcp_server.py`.

If skills were installed, verify that the copied folders contain `SKILL.md`:

- `cities2-knowledge/SKILL.md`
- `cities2-modding/SKILL.md`

New Codex sessions should list `cities2-knowledge` and `cities2-modding` in the available skills. A plain gameplay question such as "How do I grow office demand in Cities: Skylines II?" should cause the agent to use the Cities2 knowledge skill, retrieve both wiki and Encyclopedia sources when available, and include a short source note naming the Encyclopedia entries and linked wiki pages used.

## 7. Post-install

Tell the user to restart **only the clients you installed into**. Use the platform-appropriate instructions:

| Client | Windows | macOS | Linux |
|---|---|---|---|
| Claude Desktop | Right-click the Claude icon in the **system tray** and choose **Quit** (not just close the window), then reopen. | **Quit** from the menu bar or Dock (Cmd+Q), then reopen. | Fully quit and reopen. |
| Claude Code | Start a new session. | Start a new session. | Start a new session. |
| Codex | Start a new session. | Start a new session. | Start a new session. |
| Cursor | `Ctrl+Shift+P` > "Reload Window" or restart. | `Cmd+Shift+P` > "Reload Window" or restart. | `Ctrl+Shift+P` > "Reload Window" or restart. |

## Publishing

Package and MCP Registry releases are tag driven. Before pushing the first
release tag, configure a PyPI trusted publisher for:

- PyPI project: `cities2-mcp`
- GitHub owner/repository: `mayor-modder` / `Cities2-MCP`
- Workflow file: `.github/workflows/release.yml`
- Environment: `pypi`

Then create and push a tag such as `v0.1.7`. The release workflow runs tests,
builds the wheel and source distribution, publishes to PyPI, authenticates to
the MCP Registry with GitHub OIDC, and publishes `server.json` for
`io.github.mayor-modder/cities2-mcp`.

After the PyPI release exists:

1. Validate `integrations/anthropic/claude-plugin` with
   `claude plugin validate --strict`, then submit that public GitHub path to
   the Claude plugin directory.
2. Build `integrations/anthropic/claude-mcpb` with
   `npx @anthropic-ai/mcpb pack`, test the generated `.mcpb` in Claude Desktop,
   then submit it through Anthropic's desktop extension submission form.
3. Keep the MCP Registry `server.json`, Claude plugin version, MCPB manifest
   version, and PyPI version aligned for each public release.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "Server disconnected" immediately after startup | `command` is an alias (`py`, `python3`) that the MCP client cannot resolve | Use the full absolute path from `sys.executable` (step 1) |
| Server connects then disconnects during `tools/list` or `resources/list` | stdout encoding error on Windows (`cp1252` cannot encode Unicode) | Update to the latest version of this repo (the ndjson output path writes via `sys.stdout.buffer` with explicit UTF-8) |
| Server does not appear after config change | Client was still running in the background | Fully quit and restart (see step 6) |
| `ModuleNotFoundError` on startup | Missing files, wrong `REPO_ROOT`, or unavailable package command | For packaged installs, verify `uvx cities2-mcp --version`. For source installs, confirm `REPO_ROOT` points to this repository and that `cities2_mcp/retrieval/mcp_server.py` exists |
| `Path must stay inside configured workspaces` when using project tools | The target mod repo is outside every configured `--workspace` allowlist entry | Add that mod repo, or a trusted parent folder containing it, as another `--workspace` entry and restart the client |
| Claude reports InfoLoom, save analysis, live city data, or city recovery tools as part of Cities2-MCP | Claude is also loading an older or separate Cities2-related MCP server, often from a previous local tools repo | Inspect every configured MCP server whose key, command, args, or path contains `cities2`, `skylines`, `infoloom`, `dataexport`, `saveinvestigator`, or `city_recovery`. Remove stale entries from the client config, keep only the current `cities2-mcp` entry for this repo, then fully restart the client. |
