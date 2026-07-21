# Contributing

Thanks for helping improve Cities2 MCP and Modding Toolkit. This project is a local MCP server and agent skill bundle for Cities: Skylines II knowledge and modding workflows.

## Before you start

- Read [README.md](README.md) for the project overview.
- Read [INSTALL.md](INSTALL.md) if you want to test the plugin in an MCP client.
- Report vulnerabilities through [SECURITY.md](SECURITY.md), not public issues.
- Keep contributions focused. Small pull requests are easier to review and test.

## Development setup

Use Python 3.10 or newer. From the repository root:

```sh
py -3 -m unittest discover -s tests -v
```

If you change packaged skills, plugin files, templates, or integration payloads, also run:

```sh
py -3 -m cities2_mcp.plugin_packages check
```

If the package check reports stale generated plugin payloads, run the sync command it recommends, review the resulting diff, and run the check again.

## Research reports

Canonical research reports live under `cities2-research/reports/`. If a source publication date is unclear, get maintainer confirmation before syncing; do not infer it from local file metadata, event names, or repository history. Keep raw transcripts, media, and other source material under the ignored `cities2-research/sources/` directory and never force-add them.

After editing a committed research report, regenerate and verify the bundled dataset with these exact commands:

```powershell
python -m cities2_mcp.research sync
python -m cities2_mcp.research check
```

## What to keep out of commits

Do not commit:

- local MCP client config with machine-specific paths
- extracted game encyclopedia cache files
- `Locale.cok` or other local game files
- raw research source material from `cities2-research/sources/`
- built packages, virtual environments, dependency folders, or temporary smoke test workspaces
- personal paths, tokens, or private tool output

The repository includes generated plugin payloads where needed for distribution, but local caches and machine-specific settings should stay local.

## Contribution standards

- Preserve filesystem boundaries. Workflow tools must not read or write outside configured trusted workspaces.
- Prefer documented CS2 modding best practices over generic coding advice when they apply.
- Keep agent skills specific, direct, and useful in real modding sessions.
- Generated mod templates should build cleanly and avoid unnecessary complexity.
- User-facing docs should be plain English. Avoid internal terms unless the user needs them to configure or troubleshoot the tool.
- Add or update tests when behavior, packaging, safety checks, skills, or docs expectations change.

## Agent prerequisites

Agent contributors working on skills should have access to Superpowers. Before editing `SKILL.md` files, use `superpowers:writing-skills`, then follow the documented skill-testing protocol.

## Agent skills and plugin packages

The root `skills/` directory is the source of truth for bundled agent skills. Generated copies under plugin or integration directories must stay in sync with the source skills and packaged server code.

### Canonical vs generated files

Canonical sources — edit these:

- `cities2_mcp/plugin_metadata.py` — shared plugin metadata and per-platform artifact templates (name, descriptions, URLs, keywords, user config, marketplace and interface structures, and the README text).
- `cities2_mcp/__init__.py` — the canonical `__version__`, propagated into every distribution artifact.
- root `skills/` — the five bundled agent skills.
- root `cities2_mcp/` — the Python package vendored into each distribution.

Generated — do not hand-edit; run `sync` and commit only repo-visible results that belong in this repository:

- Claude and Codex package artifacts are written under ignored `dist/` for local inspection.
- Antigravity package files under `plugins/cities2-mcp/` are committed and must stay in sync.
- Per-distribution payloads include `skills/`, `vendor/`, `bin/cities2-mcp-launcher.js`, and `vendor/run_server.py`.

Export Claude and Codex package snapshots to the shared catalog repository when that catalog needs an update:

```sh
python -m cities2_mcp.plugin_packages sync-catalog --catalog-root <path-to-Mayor-Modder-Cities2-Plugins>
```

Do not commit Claude or Codex package snapshots in this repository.

Regenerate and verify:

```sh
python -m cities2_mcp.plugin_packages sync
python -m cities2_mcp.plugin_packages check
```

When changing skills:

- keep the instruction scope narrow
- include playtesting or verification expectations where relevant
- avoid promising that an agent can prove in-game behavior without user testing
- rerun the plugin package check before opening a pull request

## Pull requests

Before opening a pull request:

1. Run the relevant tests.
2. Run the plugin package check when packaging-related files changed.
3. Review the diff for private paths, generated cache files, and unrelated churn.
4. Summarize what changed and how you verified it.

Version bumps, release tags, registry publishing, and marketplace updates are handled by maintainers unless explicitly requested.
