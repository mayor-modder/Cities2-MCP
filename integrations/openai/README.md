# OpenAI Codex Distribution

Cities2-MCP publishes a Codex plugin through this repository's plugin
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
the Codex plugin path. The MCP workspace is the current Codex project folder.
