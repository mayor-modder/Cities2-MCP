# Antigravity Plugin Design

## Purpose

Add Google Antigravity as a first-class third distribution for Cities2-MCP, equal in intent to the existing Claude and Codex plugin packages. The Antigravity package should expose the same bundled MCP server and the same agent skills, using Antigravity's native plugin structure instead of reusing the Claude or Codex manifest formats.

Gemini CLI will not get a separate extension package in this branch. Its extension format is different, but Gemini CLI is being deprecated in favor of Antigravity CLI, so supporting Antigravity directly is the focused path.

## Source Documentation

Antigravity plugin documentation defines a plugin as a directory with a root `plugin.json` file and optional `skills/`, `rules/`, `mcp_config.json`, and `hooks.json` entries. Workspace plugins are loaded from `.agents/plugins/` or `_agents/plugins/` at the workspace root, and Antigravity CLI can install a remote plugin from a GitHub URL.

Gemini CLI extension documentation was checked for comparison. Gemini CLI uses `gemini-extension.json`, `GEMINI.md`, `commands/`, and different manifest variables, so it should not be conflated with Antigravity's plugin format.

The `obra/superpowers` repository was checked as a reference for maintaining many agent integrations from one skill set. Superpowers keeps `skills/` as a canonical root-level source, commits platform manifests at the repository root, uses version-audit metadata for manifests that repeat versions, and has sync tooling for platform mirrors that must live in another repository. It also explicitly rejects integrations that merely copy skill files without proving the harness loads the bootstrap automatically.

## Maintenance Strategy

Use canonical sources plus the smallest platform-specific package surface:

- canonical skills stay in root `skills/`;
- canonical Python MCP code, data, and templates stay in `cities2_mcp/`;
- platform manifests stay small and platform-native;
- generated package payloads remain checked in only for Claude and Codex, where the marketplace expects package subdirectories;
- Antigravity uses the repository root itself as the plugin so `agy plugin install https://github.com/mayor-modder/Cities2-MCP` works without copying a buried subdirectory;
- one sync/check command refreshes generated Claude/Codex payloads from canonical sources and fails CI when a package has drifted.

Do not use symlinks for shared package contents. They are fragile across Windows, zip archives, plugin marketplaces, and GitHub source installs. Do not ask users to run manual copy steps for normal installation.

Add a Python packaging helper rather than another ad hoc shell script:

```sh
python -m cities2_mcp.plugin_packages sync
python -m cities2_mcp.plugin_packages check
```

`sync` should update the generated package contents in place. `check` should run the same generation into a temporary location or compare expected file content, then fail with a clear list of stale package paths without modifying the working tree.

## Package Layout

The Antigravity plugin lives at the repository root:

```text
+-- plugin.json
+-- mcp_config.json
+-- bin/
|   `-- cities2-mcp-launcher.js
+-- skills/
|   +-- cities2-knowledge/
|   +-- cities2-modding/
|   +-- cities2-mod-review/
|   +-- cities2-mod-debugging/
|   `-- cities2-mod-release/
`-- cities2_mcp/
```

The root plugin reuses the canonical `skills/` and `cities2_mcp/` directories directly. It should not copy those assets into a generated Google package.

The files in `integrations/anthropic/claude-plugin/` and `plugins/cities2-mcp/` should be treated as generated installable packages, except for their platform-specific manifests and README files. The sync helper should own repeated payloads: `skills/`, `bin/cities2-mcp-launcher.js`, `vendor/run_server.py`, and `vendor/cities2_mcp/`.

## Manifest Design

`plugin.json` should be intentionally small and Antigravity-native:

```json
{
  "name": "cities2-mcp",
  "description": "Cities: Skylines II knowledge and modding tools",
  "version": "0.1.9"
}
```

Use the explicit name and version so tests, docs, and install output can identify the package reliably. Avoid copying Codex-specific interface metadata or Claude-specific user configuration into this file unless Antigravity documents equivalent fields later.

`mcp_config.json` should define the `cities2-mcp` MCP server using the bundled launcher. Because Antigravity launches plugin MCP configs from the opened workspace, the config uses a small Node bootstrap to locate the installed plugin directory, then runs `bin/cities2-mcp-launcher.js` with `--workspace .`.

The launcher supports both generated package layout (`vendor/run_server.py`) and source checkout layout (`cities2_mcp/mcp_server.py`).

## Skills

Bundle the same five shared skills as Claude and Codex:

- `cities2-knowledge`
- `cities2-modding`
- `cities2-mod-review`
- `cities2-mod-debugging`
- `cities2-mod-release`

Each skill should be copied from the canonical `skills/` directory. The Antigravity package should not introduce forked skill text unless Antigravity-specific wording is required for activation or installation.

## Documentation

Update root `README.md` and `INSTALL.md` so the quick install matrix includes Antigravity beside Claude and Codex. Antigravity docs should describe the two verified install paths: `agy plugin install https://github.com/mayor-modder/Cities2-MCP` for CLI, and cloning this repository into `.agents/plugins/cities2-mcp` for Desktop.

## Tests

Extend packaging and portability tests to cover the Antigravity root plugin:

- The package sync helper updates Claude and Codex payloads from canonical sources.
- The package check helper fails if any generated package payload is stale.
- `plugin.json` exists at the repository root and has `name: cities2-mcp`.
- `mcp_config.json` exists at the repository root and starts the launcher with `node`.
- `integrations/google` does not exist as a generated package payload.
- All five shared skills are present.
- The Antigravity launcher reports `cities2-mcp 0.1.9`.
- The Antigravity launcher can serve MCP and expose the expected tools.
- Public docs mention `agy plugin install`, the Desktop workspace plugin path, `/cities2`, and do not describe Gemini CLI as a separate supported package.

Existing baseline failures in `tests/test_packaging.py::PackagingTests::test_agent_asset_installer_copies_codex_and_claude_assets` and `tests/test_portability.py::PortabilityTests::test_agent_skills_are_packaged_and_documented` should be fixed as part of implementation if they still reproduce, because they block reliable full-suite verification.

## Out Of Scope

- Publishing to an Antigravity or Google marketplace submission channel.
- A Gemini CLI extension package.
- Antigravity hooks, sidecars, or rules unless later implementation evidence shows they are necessary.
- Refactoring the runtime MCP server or skill content beyond what is needed to make package synchronization deterministic.
