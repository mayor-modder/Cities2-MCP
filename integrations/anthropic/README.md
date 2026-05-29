# Anthropic Distribution

`claude-plugin/` is the primary Claude package. It bundles the Claude slash
commands, a plugin-local MCP launcher, and a vendored copy of the Python package
and wiki corpus. Installing it from the Claude plugin marketplace starts the MCP
server automatically in Claude Code and Claude Desktop.

Validate the plugin from the repository root:

```sh
claude plugin validate integrations/anthropic/claude-plugin --strict
claude plugin validate . --strict
```

For local Desktop plugin testing, zip the contents of `claude-plugin/` so the
archive root contains `.claude-plugin/plugin.json`, `.mcp.json`, `skills/`,
`bin/`, and `vendor/`. Rename the archive to `.plugin` if desired.

The Claude plugin includes five agent skills: `cities2-knowledge`,
`cities2-modding`, `cities2-mod-review`, `cities2-mod-debugging`, and
`cities2-mod-release`.
