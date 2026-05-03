# Installing the Cities2-MCP Server

This guide is written for AI coding agents. If a user asks you to install this MCP server, follow these steps in order.

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

You need four values. Determine them now before writing any config.

| Value | How to resolve |
|---|---|
| `PYTHON_PATH` | The full absolute path from step 1. |
| `REPO_ROOT` | The absolute path to this repository's root directory (the directory containing this `INSTALL.md` file). |
| `CITIES2_MODS_DIR` | **Windows:** Expand `%LOCALAPPDATA%Low\Colossal Order\Cities Skylines II\Mods` (typically `C:\Users\<username>\AppData\LocalLow\Colossal Order\Cities Skylines II\Mods`). **macOS:** `~/Library/Application Support/Colossal Order/Cities Skylines II/Mods`. **Linux:** `~/.local/share/Colossal Order/Cities Skylines II/Mods`. |
| `WORKSPACE_ROOTS` | Trusted folders where MCP workflow tools may read/write/build projects. Always include `REPO_ROOT`. If the user wants to analyze, build, package, or edit existing mod repos, also include those repo paths or a trusted parent folder containing them, such as the user's mod-projects folder. |

`--workspace` is a safety allowlist for workflow tools that write, build, or package projects. Repeat it once for each entry in `WORKSPACE_ROOTS`. Absolute project paths outside the configured workspaces are rejected with `Path must stay inside configured workspaces`.

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
| **Up to date** | Has a `cities2-mcp` entry with the current `--data-dir` flag | Exclude from the picker — already installed |
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

### Other / generic MCP client

For any MCP client not listed above, use the JSON shape from the "JSON clients" section. Consult that client's documentation for where to place MCP server configuration.

## 5. Verify

After writing the config, test that the server starts and responds. Run this from
`REPO_ROOT` with the same Python interpreter used in the MCP config:

```
<PYTHON_PATH> tests/smoke_mcp.py
```

The smoke test validates MCP initialize/list, wiki retrieval tools, resource
listing, and mod workflow tools using a temporary workspace. It does not require
the optional CS2/.NET build prerequisites.

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
contains `server/retrieval/mcp_server.py`.

## 6. Post-install

Tell the user to restart **only the clients you installed into**. Use the platform-appropriate instructions:

| Client | Windows | macOS | Linux |
|---|---|---|---|
| Claude Desktop | Right-click the Claude icon in the **system tray** and choose **Quit** (not just close the window), then reopen. | **Quit** from the menu bar or Dock (Cmd+Q), then reopen. | Fully quit and reopen. |
| Claude Code | Start a new session. | Start a new session. | Start a new session. |
| Codex | Start a new session. | Start a new session. | Start a new session. |
| Cursor | `Ctrl+Shift+P` > "Reload Window" or restart. | `Cmd+Shift+P` > "Reload Window" or restart. | `Ctrl+Shift+P` > "Reload Window" or restart. |

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "Server disconnected" immediately after startup | `command` is an alias (`py`, `python3`) that the MCP client cannot resolve | Use the full absolute path from `sys.executable` (step 1) |
| Server connects then disconnects during `tools/list` or `resources/list` | stdout encoding error on Windows (`cp1252` cannot encode Unicode) | Update to the latest version of this repo (the ndjson output path writes via `sys.stdout.buffer` with explicit UTF-8) |
| Server does not appear after config change | Client was still running in the background | Fully quit and restart (see step 6) |
| `ModuleNotFoundError` on startup | Missing files or wrong `REPO_ROOT` in config | Confirm `REPO_ROOT` points to this repository and that `server/retrieval/mcp_server.py` exists |
| `Path must stay inside configured workspaces` when using project tools | The target mod repo is outside every configured `--workspace` allowlist entry | Add that mod repo, or a trusted parent folder containing it, as another `--workspace` entry and restart the client |
| Claude reports InfoLoom, save analysis, live city data, or city recovery tools as part of Cities2-MCP | Claude is also loading an older or separate Cities2-related MCP server, often from a previous local tools repo | Inspect every configured MCP server whose key, command, args, or path contains `cities2`, `skylines`, `infoloom`, `dataexport`, `saveinvestigator`, or `city_recovery`. Remove stale entries from the client config, keep only the current `cities2-mcp` entry for this repo, then fully restart the client. |
