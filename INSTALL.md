# Install Cities2 MCP and Modding Toolkit

The Cities2 MCP and Modding Toolkit adds Cities: Skylines II knowledge and
modding workflows to Claude, Codex, and Antigravity.

Choose your client: [Claude Code](INSTALL.md#install-in-claude-code) | [Claude Desktop](INSTALL.md#install-in-claude-desktop) | [Codex CLI](INSTALL.md#install-in-codex-cli) | [Codex Desktop](INSTALL.md#install-in-codex-desktop) | [Antigravity](INSTALL.md#install-in-antigravity)

## Claude

### Install in Claude Code

Run these inside Claude Code:

```text
/plugin marketplace add mayor-modder/Cities2-MCP
```

```text
/plugin install cities2-mcp@cities2-mcp
```

Start a new Claude Code session in your mod project folder. The plugin starts
`cities2-mcp` there so workflow tools can scaffold, read, write, build, and package files.

### Install in Claude Desktop

1. Open either the **Cowork** or **Code** tab.
2. Select **Customize** in the sidebar.
3. Next to **Personal plugins**, click **+**.
4. Choose **Create Plugin** > **Add marketplace**.
5. Enter `mayor-modder/Cities2-MCP`.
6. Install and enable **Cities2 MCP and Modding Toolkit**.

### Using Skills in Claude

```text
/cities2-knowledge what's new in the latest Cities: Skylines II patch?
```

```text
/cities2-modding Scaffold a small Cities: Skylines II UI mod in this project folder, then build it.
```

```text
/cities2-mod-review Review this Cities: Skylines II mod before I share it.
```

```text
/cities2-mod-debugging Debug this Cities: Skylines II mod build failure and Modding.log excerpt.
```

```text
/cities2-mod-release Check this Cities: Skylines II mod release package for upload readiness.
```

## Codex

### Install in Codex CLI

Add this repository as a Codex plugin marketplace:

```sh
codex plugin marketplace add mayor-modder/Cities2-MCP
```

Then start Codex in your project folder:

```sh
codex
```

Enter `/plugin`, install **Cities2 MCP and Modding Toolkit**, then restart
Codex in the same folder.

### Install in Codex Desktop

1. Open the Codex app and choose **Plugins** from the sidebar.
2. Next to the "Search plugins" input, click **Built by OpenAI**.
3. Click **+ Add more**.
4. Enter Source `mayor-modder/Cities2-MCP` and click **Add Marketplace**.
5. Install and enable **Cities2 MCP and Modding Toolkit**.
6. Fully exit Codex and restart.

### Using Skills in Codex

```text
$cities2-mcp:cities2-knowledge what's new in the latest Cities: Skylines II patch?
```

```text
$cities2-mcp:cities2-modding Scaffold a small Cities: Skylines II UI mod in this project folder, then build it.
```

```text
$cities2-mcp:cities2-mod-review Review this Cities: Skylines II mod before I share it.
```

```text
$cities2-mcp:cities2-mod-debugging Debug this Cities: Skylines II mod build failure and Modding.log excerpt.
```

```text
$cities2-mcp:cities2-mod-release Check this Cities: Skylines II mod release package for upload readiness.
```

Use `/skills` or type `$` to browse installed Codex skills.

## Antigravity

### Install in Antigravity

Clone the plugin into Antigravity's plugin folder:

```sh
git clone --depth 1 https://github.com/mayor-modder/Cities2-MCP ~/.gemini/config/plugins/cities2-mcp
```

Then start `agy` from your mod workspace, or restart Antigravity Desktop. Desktop and CLI read this plugin folder.
If you download the GitHub ZIP instead, extract the repository contents there so `plugin.json` is directly inside it.

To update later:

```sh
git -C ~/.gemini/config/plugins/cities2-mcp pull --ff-only
```

Direct URL installs are not currently supported for this plugin.

### Using Skills in Antigravity

Type `/cities2` and choose one of the Cities2 skills.

```text
/cities2-knowledge What is the latest Cities: Skylines II patch in the bundled sources? Include compact source notes.
```

## Workspace Access

Game knowledge and Encyclopedia lookup work immediately. Workflow tools that
read, write, build, package, or launch local mod projects need a trusted workspace:

- In Claude Code and Codex CLI, start the client from the mod project folder.
- If a tool reports `Path must stay inside configured workspaces`, add the mod
  project folder or a trusted parent folder and restart the client.
- In Claude Desktop, that setting is called **Trusted mod projects folder**.

Codex plugin MCP servers may launch from the plugin cache. If a direct workflow tool is
allowlist-blocked, invoke `cities2-modding`; it has a bundled-template fallback.

## Optional Build Prerequisites

Knowledge, Encyclopedia, and scaffold tools do not require the Cities: Skylines II
modding toolchain. Builds may need:

- UI-only mods need Node.js and npm.
- C# and hybrid mods need the Cities: Skylines II modding toolchain installed
  from inside the game.
- C# and hybrid builds also need `dotnet` on `PATH` and
  `Microsoft.NETCore.App 6.` in `dotnet --list-runtimes`.

If a build prerequisite is missing, the agent should stop, explain what is missing,
and ask whether you want to install it, keep the scaffold, or continue with edits.

## Direct MCP Command

The plugin marketplace path is recommended. Use a direct MCP command only for a
client that cannot install plugins:

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

The package includes wiki data, so `--data-dir` is not needed. Omit `--workspace`
when you only want wiki and local Encyclopedia tools.

To check or pin the package:

```sh
uvx cities2-mcp --version
uvx --refresh cities2-mcp==0.2.0 --version
```

If your client supports MCP servers but not plugin skills, install the bundled
agent skills separately:

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
| Game Encyclopedia unavailable | Wiki tools still work. Set `CITIES2_GAME_DIR` or `CITIES2_LOCALE_COK` only if the game is installed somewhere unusual. |
