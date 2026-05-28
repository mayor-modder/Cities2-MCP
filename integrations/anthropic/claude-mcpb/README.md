# Cities2-MCP Claude Desktop MCPB

This directory is the Claude Desktop extension source for Cities2-MCP. It uses the MCPB `uv` runtime so the bundle can stay small while Claude Desktop installs the published PyPI package declared in `pyproject.toml`.

Build and validate from this directory:

```sh
npx @anthropic-ai/mcpb pack
```

The generated `.mcpb` file is the artifact to test in Claude Desktop and submit through Anthropic's desktop extension submission form.

This wrapper points at `cities2-mcp==0.1.7`, so build the public MCPB only after that PyPI version exists.
