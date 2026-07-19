# OpenAI Codex distribution

Cities2 MCP and Modding Toolkit publishes a Codex plugin through the shared plugin marketplace catalog `mayor-modder/Mayor-Modder-Cities2-Plugins`:

- `dist/.agents/plugins/marketplace.json` is the generated Codex marketplace catalog snapshot.
- `dist/plugins/cities2-mcp/` is the generated Codex plugin package exported to the shared catalog.
- `dist/plugins/cities2-mcp/.codex-plugin/plugin.json` is the generated Codex plugin manifest.
- `dist/plugins/cities2-mcp/.mcp.json` starts the bundled MCP server.

Install from Codex CLI:

```sh
codex plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins
```

The plugin vendors the Python MCP server, the bundled Cities: Skylines II Wiki corpus, curated research reports, the skill files, and the local project workflow templates, so users do not need `uvx` for the Codex plugin path. It can separately read the user's locally extracted game encyclopedia when Cities: Skylines II is installed; that encyclopedia content is not bundled.

Current Codex plugin behavior starts the bundled MCP server from the installed plugin cache. Knowledge tools work immediately, but direct MCP workflow tools may reject writes to arbitrary project folders with a workspace allowlist error. The bundled `cities2-modding` skill handles that case by copying the packaged templates into the current Codex workspace and building them with normal shell access.

The plugin includes five agent skills: `cities2-knowledge`, `cities2-modding`, `cities2-mod-review`, `cities2-mod-debugging`, and `cities2-mod-release`.
