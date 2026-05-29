# Google Distribution

`antigravity-plugin/` is the supported Google package for Cities2-MCP. It targets Google Antigravity's plugin format and bundles the same MCP server and agent skills as the Claude and Codex packages.

Gemini CLI extension packaging is intentionally not included. Gemini CLI is being replaced by Antigravity, and Antigravity uses a different plugin structure.

Refresh generated package payloads from the repository root with:

```sh
python -m cities2_mcp.plugin_packages sync
```

Check for stale generated payloads with:

```sh
python -m cities2_mcp.plugin_packages check
```
