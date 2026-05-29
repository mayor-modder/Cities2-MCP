# Cities2-MCP Claude Plugin

This is the Claude plugin package for Cities2-MCP. It bundles the two user-facing skills and a plugin-local MCP server launcher.

The plugin gives Claude:

- `/cities2-knowledge`
- `/cities2-modding`
- the `cities2-mcp` MCP server, started automatically when the plugin is enabled

The plugin `.mcp.json` points at `bin/cities2-mcp-launcher.js`, which runs the vendored Python package from `vendor/cities2_mcp`. In Claude Code, it automatically sets the MCP workspace to the current project via `${CLAUDE_PROJECT_DIR}`.

Validate from the repository root:

```sh
claude plugin validate integrations/anthropic/claude-plugin --strict
```
