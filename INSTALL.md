# Install Cities2 MCP and Modding Toolkit

Choose your client: [Claude Code](INSTALL.md#install-in-claude-code) | [Claude desktop](INSTALL.md#install-in-claude-desktop) | [Codex CLI](INSTALL.md#install-in-codex-cli) | [Codex app](INSTALL.md#install-in-the-codex-app) | [Google Antigravity](INSTALL.md#install-in-google-antigravity)

Marketplace installs include the bundled wiki corpus, the optional local game encyclopedia lookup, five agent skills, and the plugin-local MCP server launcher. Use the direct MCP command only when a client cannot install plugins or when you want to pin the Python package directly.

## Claude

### Install in Claude Code

Run these inside Claude Code:

```text
/plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins
```

```text
/plugin install cities2-mcp@cities2-mcp
```

Start a new Claude Code session in your mod project folder. The plugin starts `cities2-mcp` there so workflow tools can scaffold, read, write, build, and package files.

### Install in Claude desktop

1. Open either the **Cowork** or **Code** tab.
2. Select **Customize** in the sidebar.
3. Next to **Personal plugins**, click **+**.
4. Choose **Create Plugin** > **Add marketplace**.
5. Enter `mayor-modder/Mayor-Modder-Cities2-Plugins`.
6. Install and enable **Cities2 MCP and Modding Toolkit**.

### Using skills in Claude

```text
/cities2-knowledge Why is my office demand stuck near zero?
```

```text
/cities2-modding Scaffold a small Cities: Skylines II UI mod in this project folder, then build it.
```

```text
/cities2-mod-review Review this Cities: Skylines II mod before I install it.
```

## Codex

### Install in Codex CLI

In your system terminal, add this repository as a Codex plugin marketplace:

```sh
codex plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins
```

Then start Codex from your project folder:

```sh
codex
```

Enter `/plugin`, install **Cities2 MCP and Modding Toolkit**, then restart Codex in the same folder.

### Install in the Codex app

1. Open the Codex app and choose **Plugins** from the sidebar.
2. Click the arrow on the side of the **Create** button to open the dropdown.
3. Click **Add marketplace**.
4. Enter source `mayor-modder/Mayor-Modder-Cities2-Plugins` and click **Add marketplace**.
5. Install and enable **Cities2 MCP and Modding Toolkit**.
6. Fully exit Codex and restart.

### Using skills in Codex

```text
$cities2-mcp:cities2-knowledge How can I get more people to use my subway line?
```

```text
$cities2-mcp:cities2-modding Scaffold a small Cities: Skylines II UI mod in this project folder, then build it.
```

```text
$cities2-mcp:cities2-mod-review Review this Cities: Skylines II mod before I install it.
```

You can also check available skills with `/skills` and type `$` to pick one.

Known Codex behavior: plugin-bundled MCP servers currently launch from the installed plugin cache, so direct MCP workflow tools may be allowlist-blocked. The bundled `cities2-modding` skill handles this by copying the bundled template as an explicit fallback, building with normal Codex workspace access, and stopping after build verification.

## Google Antigravity

### Install in Google Antigravity

Run this once in PowerShell:

```powershell
agy plugin install https://github.com/mayor-modder/Cities2-MCP/
```

Then restart the Google Antigravity app, or open Antigravity CLI with `agy` from your mod workspace.

### Using skills in Google Antigravity

Type `/cities2` and choose one of the Cities2 skills.

```text
/cities2-knowledge Why are my commercial companies complaining about not enough customers?
```

```text
/cities2-modding Scaffold a small Cities: Skylines II UI mod in this project folder, then build it.
```

```text
/cities2-mod-review Review this Cities: Skylines II mod before I install it.
```

## Workspace access

Game knowledge and encyclopedia lookup work immediately after install. Mod workflow tools need a trusted workspace, and Claude and Codex usually use the project you opened:

- In Claude Code and Codex CLI, start the client from the mod project folder.
- If a tool reports `Path must stay inside configured workspaces`, add the mod project folder or a trusted parent folder and restart the client.
- In Claude desktop, that setting is called **Trusted mod projects folder**.

Codex plugin MCP servers may launch from the plugin cache. If a direct workflow tool is allowlist-blocked, invoke `cities2-modding`; it has a bundled-template fallback.

Builds run project commands through `npm`, `dotnet`, and packaging steps; only build projects you trust. The skills should still hand local playtesting back to you before calling a mod ready to share.

## Optional build prerequisites

Knowledge, encyclopedia, and scaffold tools do not require the Cities: Skylines II modding toolchain. Builds may need:

- UI-only mods need Node.js and npm.
- C# and hybrid mods need the Cities: Skylines II modding toolchain installed from inside the game.
- C# and hybrid builds also need `dotnet` on `PATH` and `Microsoft.NETCore.App 6.` in `dotnet --list-runtimes`.

If a build prerequisite is missing, the agent should stop, explain what is missing, and ask whether you want to install it, keep the scaffold, or continue with edits.

## Direct MCP command

The plugin marketplace path is recommended. Use a direct MCP command only for a client that cannot install plugins:

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

The package includes wiki data, so `--data-dir` is not needed. Omit `--workspace` when you only want wiki and local encyclopedia tools.

To check or pin the package:

```sh
uvx cities2-mcp --version
uvx --refresh cities2-mcp --version
```

Some clients can load local agent skills separately from MCP server settings. For those clients, install the bundled skills with:

```sh
uvx cities2-mcp install-agent-assets
```

For a source checkout, run `python -m cities2_mcp.mcp_server --workspace <folder>` from the repository root.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Server does not appear after install | Fully quit and restart the client you installed into. |
| `Path must stay inside configured workspaces` | Add the mod project folder, or a trusted parent folder containing your mods, to the client or plugin workspace setting. |
| Codex workflow tools are allowlist-blocked | Invoke `$cities2-mcp:cities2-modding`; the skill can use the bundled-template fallback inside the current Codex workspace. |
| `npm.ps1` is blocked on Windows | Use `npm.cmd install` and `npm.cmd run build`. |
| C# build says .NET is missing | Install the .NET 6 runtime and confirm with `dotnet --list-runtimes`. |
| Game encyclopedia unavailable | Wiki tools still work. Set `CITIES2_GAME_DIR` or `CITIES2_LOCALE_COK` only if the game is installed somewhere unusual. |
