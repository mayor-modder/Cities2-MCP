# Shared plugin catalog export design

## Goal

Cities2-MCP should export its generated Claude and Codex plugin snapshots into the shared `mayor-modder/Mayor-Modder-Cities2-Plugins` catalog repository, matching the release flow used by Cities2 Chief of Staff. The shared catalog is the install source for both Claude and Codex users who want Mayor Modder's Cities: Skylines II plugins.

## Scope

In scope:

- Add a catalog sync path to `cities2_mcp.plugin_packages`.
- Move generated Claude and Codex plugin package snapshots out of committed repository paths and into ignored `dist/` paths during local packaging.
- Remove committed Claude and Codex packaged plugin snapshots from this repository.
- Export the generated Claude package and Claude marketplace files into the shared catalog layout.
- Export the generated Codex package and Codex marketplace files into the shared catalog layout.
- Update Claude and Codex installation instructions to use `mayor-modder/Mayor-Modder-Cities2-Plugins`.
- Add tests that prove catalog sync copies the expected package payloads and marketplace metadata.

Out of scope:

- Changing Google Antigravity installation behavior or documentation.
- Moving development ownership out of this repository.
- Publishing, pushing, or updating the shared catalog repository during normal package checks.

## Catalog layout

The default local generated Claude and Codex package root is `dist/`, which is not committed. The default catalog root is `../Mayor-Modder-Cities2-Plugins`, overridable by CLI argument. Cities2-MCP exports these paths under that catalog root:

- `.claude-plugin/marketplace.json`
- `integrations/anthropic/claude-plugin/`
- `.agents/plugins/marketplace.json`
- `plugins/cities2-mcp/`

The catalog repository remains a snapshot repository. Source changes continue to happen in `mayor-modder/Cities2-MCP`; generated installable package snapshots are copied into the catalog during release preparation.

Marketplace files in the shared catalog may contain entries for multiple plugins. Cities2-MCP catalog sync updates or inserts only the Cities2-MCP entries and preserves unrelated plugin entries such as Cities2 Chief of Staff.

## Packaging behavior

`python -m cities2_mcp.plugin_packages sync` writes generated Claude and Codex package artifacts under `dist/` instead of the committed source tree. This gives contributors a local build output to inspect without keeping Claude or Codex packaged plugin snapshots in this repository.

`python -m cities2_mcp.plugin_packages sync-catalog` first syncs the local generated package artifacts, then copies the generated Claude and Codex outputs into the catalog root. It fails before copying if the catalog root itself does not look like the shared catalog, but it may create missing marketplace directories or files inside an otherwise valid catalog checkout. It updates catalog marketplace manifests by upserting the Cities2-MCP entries instead of replacing the whole manifest.

The copy operation replaces only the Cities2-MCP-owned package directories and marketplace files listed in this design. It does not alter other plugin package folders, including Cities2 Chief of Staff.

`check` verifies that generated metadata builders and package payload assembly remain internally consistent. It does not require committed Claude or Codex package snapshots in this repository, and it does not inspect a sibling catalog checkout by default because contributors may not have that repository cloned.

## Install instructions

Claude Code and Claude desktop instructions should point users at:

```text
mayor-modder/Mayor-Modder-Cities2-Plugins
```

Codex CLI and Codex app instructions should also point users at:

```text
mayor-modder/Mayor-Modder-Cities2-Plugins
```

Client-specific install steps stay otherwise unchanged. Google Antigravity instructions remain unchanged.

## Testing

Focused tests should cover:

- `sync-catalog` copies the Claude marketplace file, Claude package directory, Codex marketplace file, and Codex package directory into a catalog fixture.
- `sync-catalog` preserves unrelated marketplace plugin entries while replacing stale Cities2-MCP entries.
- The catalog sync refuses to run when the catalog root is missing or lacks the expected top-level catalog structure.
- Existing local package sync/check tests are updated to expect generated artifacts under `dist/`.
- Repository portability tests prove Claude and Codex packaged plugin snapshots are no longer committed under the old package paths.
- Install docs mention the shared catalog repository for Claude and Codex and do not change Antigravity expectations.

Required gates for the implementation are:

```sh
python -m unittest tests.test_packaging tests.test_portability -v
python -m cities2_mcp.plugin_packages check
```
