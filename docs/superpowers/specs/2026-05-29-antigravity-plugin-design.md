# Antigravity Plugin Design

## Purpose

Add Google Antigravity as a first-class third distribution for Cities2-MCP, equal in intent to the existing Claude and Codex plugin packages. The Antigravity package should expose the same bundled MCP server and the same agent skills, using Antigravity's native plugin structure instead of reusing the Claude or Codex manifest formats.

Gemini CLI will not get a separate extension package in this branch. Its extension format is different, but Gemini CLI is being deprecated in favor of Antigravity CLI, so supporting Antigravity directly is the focused path.

## Source Documentation

Antigravity plugin documentation defines a plugin as a directory with a root `plugin.json` file and optional `skills/`, `rules/`, `mcp_config.json`, and `hooks.json` entries. Workspace plugins are loaded from `.agents/plugins/` or `_agents/plugins/` at the workspace root; global plugins are loaded from `~/.gemini/config/plugins/`.

Gemini CLI extension documentation was checked for comparison. Gemini CLI uses `gemini-extension.json`, `GEMINI.md`, `commands/`, and different manifest variables, so it should not be conflated with Antigravity's plugin format.

## Package Layout

Create a new package at `integrations/google/antigravity-plugin/`:

```text
integrations/google/
+-- README.md
`-- antigravity-plugin/
    +-- plugin.json
    +-- mcp_config.json
    +-- README.md
    +-- bin/
    |   `-- cities2-mcp-launcher.js
    +-- skills/
    |   +-- cities2-knowledge/
    |   +-- cities2-modding/
    |   +-- cities2-mod-review/
    |   +-- cities2-mod-debugging/
    |   `-- cities2-mod-release/
    `-- vendor/
        +-- run_server.py
        `-- cities2_mcp/
```

The package should mirror the Claude and Codex vendoring model: copy the Python server and corpus into `vendor/`, include a Node launcher in `bin/`, and bundle the shared skills from the repository `skills/` directory.

## Manifest Design

`plugin.json` should be intentionally small and Antigravity-native:

```json
{
  "name": "cities2-mcp"
}
```

Antigravity's current docs only require `plugin.json` and state that `name` is optional. Use the explicit name so tests and docs can identify the package reliably. Avoid copying Codex-specific interface metadata or Claude-specific user configuration into this file unless Antigravity documents equivalent fields later.

`mcp_config.json` should define the `cities2-mcp` MCP server using the bundled launcher:

```json
{
  "mcpServers": {
    "cities2-mcp": {
      "command": "node",
      "args": [
        "./bin/cities2-mcp-launcher.js",
        "--workspace",
        "."
      ],
      "cwd": "."
    }
  }
}
```

This should match the current Codex behavior: the server starts from the installed plugin package, wiki and Encyclopedia tools work immediately, and local workflow tools remain subject to workspace trust and allowlist behavior enforced by the MCP server.

## Skills

Bundle the same five shared skills as Claude and Codex:

- `cities2-knowledge`
- `cities2-modding`
- `cities2-mod-review`
- `cities2-mod-debugging`
- `cities2-mod-release`

Each skill should be copied from the canonical `skills/` directory. The Antigravity package should not introduce forked skill text unless Antigravity-specific wording is required for activation or installation.

## Documentation

Add `integrations/google/README.md` to explain the Google distribution and make Antigravity the supported path.

Add `integrations/google/antigravity-plugin/README.md` with:

- what the plugin provides;
- the expected package contents;
- the workspace install path: `.agents/plugins/cities2-mcp/` or `_agents/plugins/cities2-mcp/`;
- the global install path: `~/.gemini/config/plugins/cities2-mcp/`;
- restart/reload guidance after installation;
- a note that Gemini CLI extension packaging is intentionally not included because Antigravity supersedes it.

Update root `README.md` and `INSTALL.md` so the quick install matrix includes Antigravity beside Claude and Codex.

## Tests

Extend packaging and portability tests to cover the Antigravity package:

- `plugin.json` exists at the Antigravity plugin root and has `name: cities2-mcp`.
- `mcp_config.json` exists and starts the bundled launcher with `node`.
- The package does not use `.codex-plugin`, `.claude-plugin`, `.mcp.json`, or `gemini-extension.json` as its primary manifest.
- All five shared skills are present.
- `vendor/run_server.py` and `vendor/cities2_mcp/mcp_server.py` are present.
- The Antigravity launcher reports `cities2-mcp 0.1.9`.
- The Antigravity launcher can serve MCP and expose the expected tools.
- Public docs mention Antigravity install paths and do not describe Gemini CLI as a separate supported package.

Existing baseline failures in `tests/test_packaging.py::PackagingTests::test_agent_asset_installer_copies_codex_and_claude_assets` and `tests/test_portability.py::PortabilityTests::test_agent_skills_are_packaged_and_documented` should be fixed as part of implementation if they still reproduce, because they block reliable full-suite verification.

## Out Of Scope

- Publishing to an Antigravity or Google marketplace, because the current Antigravity docs describe local/global plugin locations but not a marketplace submission format.
- A Gemini CLI extension package.
- Antigravity hooks, sidecars, or rules unless later implementation evidence shows they are necessary.
- Refactoring the shared vendoring process beyond what is needed to add the third package safely.
