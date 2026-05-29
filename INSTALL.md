# Install Cities2-MCP

Cities2-MCP adds Cities: Skylines II knowledge and modding tools to Claude and
Codex. The easiest install path is the plugin marketplace: add this repository
as a marketplace, install **Cities2-MCP**, restart the client, and use the
bundled agent skills.

## Claude

### Install in Claude Code

Claude Code is the terminal Claude app. Install from inside Claude Code:

```text
/plugin marketplace add mayor-modder/Cities2-MCP
/plugin install cities2-mcp@cities2-mcp
```

Start a new Claude Code session in your mod project folder. The plugin starts
`cities2-mcp` for that project and sets `--workspace` to the current Claude Code
project, so workflow tools can scaffold, read, write, analyze, build, and
package files there.

### Install in Claude Desktop

Use Claude Desktop's plugin marketplace UI:

1. Open either the **Cowork** or **Code** tab.
2. Select **Customize** in the sidebar.
3. Next to **Personal plugins**, click **+**.
4. Choose **Create Plugin** > **Add marketplace**.
5. Enter `mayor-modder/Cities2-MCP`.
6. Install and enable **Cities2-MCP**.

If Claude Desktop says a project is outside the trusted workspace, add that mod
repo or a trusted parent folder to the plugin's trusted mod projects folder,
then restart Claude Desktop.

### Using Skills in Claude
In either version of Claude, you can invoke the skills as slash commands. Try:

```text
/cities2-knowledge what's new in the latest Cities: Skylines II patch?
/cities2-modding Scaffold a small Cities: Skylines II UI mod in this project folder, then build it.
```

## Codex

### Install in Codex CLI

Add this repository as a Codex plugin marketplace:

```sh
codex plugin marketplace add mayor-modder/Cities2-MCP
```

Then start Codex in the project folder:

```sh
codex
```

Enter `/plugin`, install **Cities2-MCP** from the marketplace, then restart Codex
in the same folder.


### Install in Codex Desktop

Use the Codex app plugin UI:

1. Open the Codex app and choose **Plugins** from the sidebar.
2. Next to the "Search plugins" input, click the button that says **Built by OpenAI**.
3. In the dropdown menu that appears, click **+ Add more**.
4. In the dialog that appears, enter the Source `mayor-modder/Cities2-MCP` and click **Add Marketplace**.
5. Install and enable **Cities2-MCP**.
6. Fully exit Codex and restart.

### Using Skills in Codex

Codex invokes plugin skills with `$` mentions. Use:

```text
$cities2-mcp:cities2-knowledge what's new in the latest Cities: Skylines II patch?
$cities2-mcp:cities2-modding Scaffold a small Cities: Skylines II UI mod in this project folder, then build it.
```

You can also check available skills with `/skills` and type `$` to pick one.

Known Codex behavior: plugin-bundled MCP servers currently launch from the
installed plugin cache, so direct MCP workflow tools may be allowlist-blocked.
The bundled `cities2-modding` skill handles this by copying the bundled template
as an explicit fallback, building with normal Codex workspace access, and
stopping after build verification.

## Optional Build Prerequisites

Wiki search, patch answers, Game Encyclopedia search, and project scaffolding do
not require the Cities: Skylines II modding toolchain. Builds do:

- UI-only mods need Node.js and npm.
- C# and hybrid mods need the Cities: Skylines II modding toolchain installed
  from inside the game.
- C# and hybrid builds also need `dotnet` on `PATH` and
  `Microsoft.NETCore.App 6.` in `dotnet --list-runtimes`.

If a build fails because Node/npm, .NET, or the CS2 modding toolchain is missing,
the agent should stop after the failed build, explain the missing prerequisite,
and ask whether you want to install the prerequisite, keep the scaffold only, or
continue with non-build edits.

## Capabilities

Expected public MCP tools:

- Knowledge: `search`, `get_page`, `query_reference`, `get_snippets`,
  `search_encyclopedia`, `get_encyclopedia_entry`, `source_status`
- Mod workflow: `scaffold_project`, `write_project_file`, `list_project_tree`,
  `build_project`, `analyze_project`, `package_project`, `launch_cities2`

`source_status()` may report that the Game Encyclopedia is unavailable on
machines without Cities: Skylines II installed. That is a warning, not an install
failure.

## Advanced: Direct MCP Install

The marketplace plugin path is recommended. Use the manual paths below when you
are configuring an MCP client that cannot install plugins.

### PyPI With uvx

For clients that accept a direct MCP command, use:

```json
{
  "mcpServers": {
    "cities2-mcp": {
      "command": "uvx",
      "args": [
        "cities2-mcp",
        "--workspace",
        "<TRUSTED_MOD_PROJECT_OR_PARENT_FOLDER>"
      ]
    }
  }
}
```

The package includes the bundled wiki, so `--data-dir` is not needed.
Omit `--workspace` when you only want wiki and local Encyclopedia tools. Add one
or more `--workspace` entries when you want workflow tools to write, analyze,
build, or package local mod projects.

To force a specific package version:

```sh
uvx --refresh cities2-mcp==0.1.8 --version
```

To install standalone agent assets from the package:

```sh
uvx cities2-mcp install-agent-assets
```

Use `--client codex` or `--client claude` to target one client.

### Run From A Local Checkout

Clone this repository only if you specifically want to run the server from a
local checkout instead of the marketplace plugin or PyPI package.

#### Local Values

Resolve these before writing manual config:

| Value | Meaning |
|---|---|
| `PYTHON_PATH` | Full absolute path to Python 3.10+. Use `py -3 -c "import sys; print(sys.executable)"` on Windows or `python3 -c "import sys; print(sys.executable)"` on macOS/Linux. |
| `REPO_ROOT` | Absolute path to this repository. |
| `WORKSPACE_ROOTS` | Trusted folders where workflow tools may read, write, build, and package projects. Use a mod project folder or a trusted parent folder containing your mods. |
| `CITIES2_MODS_DIR` | Optional override for the standard local Mods folder. |
| `CITIES2_GAME_DIR` | Optional override for non-standard game installs. Point it at the Cities: Skylines II install directory, not `Cities2_Data`. |
| `CITIES2_LOCALE_COK` | Optional direct path to `Locale.cok` if game-directory discovery is not enough. |

`--workspace` is a safety allowlist for workflow tools that write, build, or
package projects. Absolute project paths outside the configured workspaces are
rejected with `Path must stay inside configured workspaces`. If that happens,
add that mod repo, or a trusted parent folder containing it, as another
`--workspace` entry and restart the client.

#### Claude Code Manual MCP

Prefer the plugin install above. For a manual source checkout install, use
Claude Code's MCP command instead of hand-editing `~/.claude.json`:

```powershell
$json = @'
{"type":"stdio","command":"<PYTHON_PATH>","args":["-m","cities2_mcp.mcp_server","--data-dir","<REPO_ROOT>/data","--workspace","<REPO_ROOT>"],"env":{"PYTHONPATH":"<REPO_ROOT>","CITIES2_MODS_DIR":"<CITIES2_MODS_DIR>"}}
'@
claude mcp add-json cities2-mcp $json --scope user
```

On macOS/Linux:

```sh
claude mcp add-json cities2-mcp '{"type":"stdio","command":"<PYTHON_PATH>","args":["-m","cities2_mcp.mcp_server","--data-dir","<REPO_ROOT>/data","--workspace","<REPO_ROOT>"],"env":{"PYTHONPATH":"<REPO_ROOT>","CITIES2_MODS_DIR":"<CITIES2_MODS_DIR>"}}' --scope user
```

Use `--scope project` only if you explicitly want Claude Code to write a shared
project-level `.mcp.json` file.

The Windows example uses a PowerShell here-string to avoid brittle shell
escaping.

#### Claude Desktop Manual MCP

Prefer the plugin install above. For manual MCP config, agents can edit
`claude_desktop_config.json` directly. Use **Settings > Developer > Edit Config**
only to confirm the active file if needed.

Default paths:

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this inside `mcpServers`, preserving unrelated settings:

```json
{
  "cities2-mcp": {
    "command": "<PYTHON_PATH>",
    "args": [
      "-m",
      "cities2_mcp.mcp_server",
      "--data-dir",
      "<REPO_ROOT>/data",
      "--workspace",
      "<REPO_ROOT>"
    ],
    "env": {
      "PYTHONPATH": "<REPO_ROOT>",
      "CITIES2_MODS_DIR": "<CITIES2_MODS_DIR>"
    }
  }
}
```

#### Codex Manual MCP

Prefer the Codex plugin install above. For manual MCP config, add this to
`~/.codex/config.toml`:

```toml
[mcp_servers.cities2-mcp]
command = "<PYTHON_PATH>"
args = [
  "-m",
  "cities2_mcp.mcp_server",
  "--data-dir",
  "<REPO_ROOT>/data",
  "--workspace",
  "<REPO_ROOT>"
]

[mcp_servers.cities2-mcp.env]
PYTHONPATH = "<REPO_ROOT>"
CITIES2_MODS_DIR = "<CITIES2_MODS_DIR>"
```

#### Manual Skill Copy

For packaged installs, prefer:

```sh
uvx cities2-mcp install-agent-assets
```

For a local checkout, copy `skills/cities2-knowledge` and
`skills/cities2-modding` into your client's skill directory only if the client
does not load them from the plugin.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Server disconnected immediately after startup | Manual config uses an alias such as `py`, `python3`, or an unavailable package command | For source installs, use the full absolute `PYTHON_PATH`. For packaged installs, verify `uvx cities2-mcp --version`. |
| Server does not appear after install | The client was still running in the background | Fully quit and restart only the client you installed into. |
| `Path must stay inside configured workspaces` | The target mod repo is outside every configured `--workspace` allowlist entry | Add that mod repo, or a trusted parent folder containing it, as another workspace/trusted folder and restart the client. |
| Codex workflow tools are allowlist-blocked even though the plugin is installed | Codex plugin MCP servers launch from the installed plugin cache | Use the bundled `cities2-modding` skill fallback, or configure a manual/project-specific MCP server for that workspace. |
| `npm.ps1` is blocked on Windows | PowerShell execution policy blocks bare `npm` | Use `npm.cmd install` and `npm.cmd run build`. |
| C# build says you must install or update .NET | Missing `Microsoft.NETCore.App 6.` runtime | Install the .NET 6 runtime and confirm with `dotnet --list-runtimes`. |
| Game Encyclopedia unavailable | Cities: Skylines II is not installed, is installed in a non-standard location, or `Locale.cok` could not be found | Wiki tools still work. Set `CITIES2_GAME_DIR` or `CITIES2_LOCALE_COK` only if you need local Encyclopedia entries. |
| Claude reports InfoLoom, save analysis, live city data, or city recovery tools as part of Cities2-MCP | Claude is also loading an older or separate Cities2-related MCP server, often from a previous local tools repo | Inspect every configured MCP server whose key, command, args, or path contains `cities2`, `skylines`, `infoloom`, `dataexport`, `saveinvestigator`, or `city_recovery`. Remove stale entries and keep only the current Cities2-MCP entry. |

During manual cleanup, keep the current `cities2-mcp` entry and remove old
entries such as `cities2-modding-workbench`, `cities2Workbench`,
`cities2-workbench`, or any stale `cities2` entry that points at an old repo or
old flags.

Claude Desktop app settings and Claude Code settings are separate. If you use
both apps, install or troubleshoot Cities2-MCP in each one separately.
