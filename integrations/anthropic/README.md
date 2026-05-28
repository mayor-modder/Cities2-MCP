# Anthropic Distribution

Cities2-MCP has two Anthropic-facing package shapes:

- `claude-plugin/` packages the Claude Code skills, a plugin-local launcher, a vendored copy of the Python package, and `.mcp.json`. This is the clean Claude Code path: installing the plugin provides slash commands and starts the MCP server automatically.
- `claude-mcpb/` packages a Claude Desktop MCPB wrapper for the local MCP server. This is the correct artifact for Claude Desktop extension testing and Connectors Directory submission, and it avoids asking end users to install `uvx` manually.

Anthropic's docs say local PyPI MCP servers are not listed directly in the Connectors Directory. Local servers should be distributed as MCPB desktop extensions, or bundled in a plugin with `.mcp.json`.

Validate from the repository root:

```sh
claude plugin validate integrations/anthropic/claude-plugin --strict
claude plugin validate . --strict
```

Validate/build the MCPB from its directory:

```sh
cd integrations/anthropic/claude-mcpb
npx @anthropic-ai/mcpb pack
```
