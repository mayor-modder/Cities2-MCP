# Cities2-MCP Codex Plugin

This is the Codex plugin package for Cities2-MCP. It bundles the two user-facing skills and a plugin-local MCP server launcher.

The plugin `.mcp.json` points at `bin/cities2-mcp-launcher.js`, which runs the vendored Python package from `vendor/cities2_mcp`. In Codex, the MCP workspace is the current project folder, so wiki and Encyclopedia tools work immediately and mod workflow tools are scoped to the project you opened.

Install from this repository marketplace:

```powershell
codex plugin marketplace add mayor-modder/Cities2-MCP
```
