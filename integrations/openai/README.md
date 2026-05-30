# OpenAI Codex Distribution

Cities2 MCP and Modding Toolkit publishes a Codex plugin through this repository's plugin
marketplace:

- `.agents/plugins/marketplace.json` is the Codex marketplace catalog.
- `plugins/cities2-mcp/` is the plugin package.
- `plugins/cities2-mcp/.codex-plugin/plugin.json` is the Codex plugin manifest.
- `plugins/cities2-mcp/.mcp.json` starts the bundled MCP server.

Install from Codex CLI:

```sh
codex plugin marketplace add mayor-modder/Cities2-MCP
```

The plugin vendors the Python server and corpus, so users do not need `uvx` for
the Codex plugin path.

Current Codex plugin behavior starts the bundled MCP server from the installed
plugin cache. Knowledge tools work immediately, but direct MCP workflow tools
may reject writes to arbitrary project folders with a workspace allowlist error.
The bundled `cities2-modding` skill handles that case by copying the packaged
templates into the current Codex workspace and building them with normal shell
access.

The plugin includes five agent skills: `cities2-knowledge`, `cities2-modding`,
`cities2-mod-review`, `cities2-mod-debugging`, and `cities2-mod-release`.
