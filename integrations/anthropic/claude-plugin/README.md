# Cities2-MCP Claude Code Plugin

This is the Claude Code plugin package for Cities2-MCP. It bundles the two user-facing skills.

The plugin gives Claude Code:

- `/cities2-mcp:cities2-knowledge`
- `/cities2-mcp:cities2-modding`

The plugin does not configure an MCP server by itself because the simple Claude Code MCP command path uses `uvx`, and `uvx` must already be installed on the user's machine. That is too easy to miss for a directory install.

After installing the plugin, configure the MCP server separately. For users with `uvx` available:

```sh
claude mcp add --scope local cities2-mcp -- uvx cities2-mcp --workspace .
```

Omit `--workspace .` for wiki, Encyclopedia, and patch/update questions only.

Validate from the repository root:

```sh
claude plugin validate integrations/anthropic/claude-plugin --strict
```
