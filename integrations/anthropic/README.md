# Anthropic Distribution

Cities2-MCP has two Anthropic-facing package shapes:

- `claude-plugin/` packages the Claude skills, a plugin-local launcher, a vendored copy of the Python package, and `.mcp.json`. This is the clean plugin path: installing the plugin provides slash commands and starts the MCP server automatically in Claude Code, and Claude Desktop can install the same package as a `.zip` or `.plugin` archive when its Plugins UI is available.
- `claude-mcpb/` packages a Claude Desktop MCPB wrapper for the local MCP server. This is the correct artifact for Claude Desktop extension testing and Connectors Directory submission, and it avoids asking end users to install `uvx` manually.

Anthropic's docs say local PyPI MCP servers are not listed directly in the Connectors Directory. Local servers should be distributed as MCPB desktop extensions, or bundled in a plugin with `.mcp.json`.

Validate from the repository root:

```sh
claude plugin validate integrations/anthropic/claude-plugin --strict
claude plugin validate . --strict
```

For local Desktop plugin testing, zip the contents of `claude-plugin/` so the
archive root contains `.claude-plugin/plugin.json`, `.mcp.json`, `skills/`,
`bin/`, and `vendor/`. Rename the archive to `.plugin` if desired.

Validate/build the MCPB from its directory:

```sh
cd integrations/anthropic/claude-mcpb
npx @anthropic-ai/mcpb pack
```
