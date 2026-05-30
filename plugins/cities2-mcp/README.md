# Cities2 MCP and Modding Toolkit Codex Plugin

This is the Codex plugin package for Cities2 MCP and Modding Toolkit. It bundles five user-facing
agent skills and a plugin-local MCP server launcher.

Included skills: `cities2-knowledge`, `cities2-modding`, `cities2-mod-review`,
`cities2-mod-debugging`, and `cities2-mod-release`.

The plugin `.mcp.json` points at `bin/cities2-mcp-launcher.js`, which runs the
vendored Python package from `vendor/cities2_mcp`. Codex currently launches the
server from the installed plugin cache, so wiki and Encyclopedia tools work
immediately, while direct MCP workflow tools may be allowlist-blocked for the
project you opened. The bundled `cities2-modding` skill includes an explicit
template-copy fallback for that case.

Install from this repository marketplace:

```sh
codex plugin marketplace add mayor-modder/Cities2-MCP
```
