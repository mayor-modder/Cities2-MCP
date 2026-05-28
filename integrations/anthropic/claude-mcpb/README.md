# Cities2-MCP Claude Desktop MCPB

This directory is the Claude Desktop extension source for Cities2-MCP. It uses the MCPB `uv` runtime, but the server package and wiki corpus are vendored into `vendor/cities2_mcp` so local testing does not depend on the matching PyPI release already existing.

Build and validate from this directory:

```sh
npx @anthropic-ai/mcpb pack
```

The generated `.mcpb` file is the artifact to test in Claude Desktop and submit through Anthropic's desktop extension submission form.
