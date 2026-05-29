# Cities2-MCP Antigravity Plugin

This is the Google Antigravity plugin package for Cities2-MCP. It bundles the user-facing skills and a plugin-local MCP server launcher.

The plugin gives Antigravity:

- `cities2-knowledge`
- `cities2-modding`
- `cities2-mod-review`
- `cities2-mod-debugging`
- `cities2-mod-release`
- the `cities2-mcp` MCP server, started from `mcp_config.json`

The plugin `mcp_config.json` points at `bin/cities2-mcp-launcher.js`, which runs the vendored Python package from `vendor/cities2_mcp`.

Install as a workspace plugin by copying this package to one of these paths in the opened workspace:

```text
.agents/plugins/cities2-mcp/
_agents/plugins/cities2-mcp/
```

Install globally by copying this package to:

```text
~/.gemini/config/plugins/cities2-mcp/
```

Restart or reload Antigravity after installation so it rescans plugin directories.

Gemini CLI extension packaging is intentionally not included because Antigravity supersedes Gemini CLI and uses this plugin format.
