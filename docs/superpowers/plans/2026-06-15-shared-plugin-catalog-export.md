# Shared Plugin Catalog Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move Claude and Codex plugin package snapshots out of this repository and add a catalog export command that publishes Cities2-MCP snapshots into `mayor-modder/Mayor-Modder-Cities2-Plugins`.

**Architecture:** Keep canonical source in this repository, generate Claude/Codex installable packages under ignored `dist/`, and copy those generated packages into the shared catalog on demand. Catalog marketplace manifests are updated by upserting only the `cities2-mcp` entry so other plugins, including Chief of Staff, are preserved.

**Tech Stack:** Python standard library (`argparse`, `json`, `pathlib`, `shutil`, `tempfile`), `unittest`, existing `cities2_mcp.plugin_packages` and `cities2_mcp.plugin_metadata` modules.

---

## File structure

- Modify `cities2_mcp/plugin_metadata.py`: add shared catalog constants, marketplace entry builders, and update generated README install commands to use `mayor-modder/Mayor-Modder-Cities2-Plugins`.
- Modify `cities2_mcp/plugin_packages.py`: split Claude/Codex package roots into ignored `dist/` paths, keep Antigravity's existing package path, add `sync-catalog`, and add marketplace upsert helpers.
- Modify `tests/test_packaging.py`: update package sync/check expectations for `dist/`, add catalog sync/upsert tests, and update launcher smoke tests to generate package fixtures before running.
- Modify `tests/test_portability.py`: update Claude/Codex install assertions to use the shared catalog repo and assert old Claude/Codex package snapshots are not committed.
- Modify `INSTALL.md`: point Claude and Codex install instructions at `mayor-modder/Mayor-Modder-Cities2-Plugins`; leave Google Antigravity instructions unchanged.
- Modify `plugins/cities2-mcp/README.md` only if it remains generated for Antigravity-specific packaging; otherwise remove Codex-specific README expectations from this repo.
- Delete committed Claude/Codex package snapshot files:
  - `.claude-plugin/marketplace.json`
  - `.agents/plugins/marketplace.json`
  - `integrations/anthropic/claude-plugin/`
  - `plugins/cities2-mcp/.codex-plugin/`
  - `plugins/cities2-mcp/.mcp.json`
  - Codex-specific `plugins/cities2-mcp/README.md`
- Keep Antigravity package files unless a later explicit decision changes Antigravity:
  - `plugins/cities2-mcp/plugin.json`
  - `plugins/cities2-mcp/mcp_config.json`
  - `plugins/cities2-mcp/bin/`
  - `plugins/cities2-mcp/skills/`
  - `plugins/cities2-mcp/vendor/`

## Task 1: Test the new package roots and absence of committed Claude/Codex snapshots

**Files:**
- Modify: `tests/test_packaging.py`
- Modify: `tests/test_portability.py`

- [ ] **Step 1: Update package root expectations in tests**

In `tests/test_packaging.py`, update package-root tests to expect:

```python
claude_root = ROOT / "dist" / "integrations" / "anthropic" / "claude-plugin"
codex_root = ROOT / "dist" / "plugins" / "cities2-mcp"
antigravity_root = ROOT / "plugins" / "cities2-mcp"
```

For tests that should not write to the real repository, generate under a temp root:

```python
with tempfile.TemporaryDirectory(prefix="cities2-mcp-plugin-sync-") as tmp:
    root = Path(tmp)
    self._write_plugin_sync_fixture(root)
    plugin_packages.sync_packages(root)
    claude_root = root / "dist" / "integrations" / "anthropic" / "claude-plugin"
    codex_root = root / "dist" / "plugins" / "cities2-mcp"
```

- [ ] **Step 2: Add a portability test for removed Claude/Codex snapshots**

Add this test to `tests/test_portability.py`:

```python
def test_claude_and_codex_package_snapshots_are_not_committed(self) -> None:
    self.assertFalse((ROOT / ".claude-plugin" / "marketplace.json").exists())
    self.assertFalse((ROOT / ".agents" / "plugins" / "marketplace.json").exists())
    self.assertFalse((ROOT / "integrations" / "anthropic" / "claude-plugin").exists())
    self.assertFalse((ROOT / "plugins" / "cities2-mcp" / ".codex-plugin").exists())
    self.assertFalse((ROOT / "plugins" / "cities2-mcp" / ".mcp.json").exists())
```

- [ ] **Step 3: Run tests to verify they fail before implementation**

Run:

```sh
python -m unittest tests.test_packaging.PluginPackagingTests.test_check_detects_and_sync_restores_each_metadata_file tests.test_portability.PortabilityTests.test_claude_and_codex_package_snapshots_are_not_committed -v
```

Expected: FAIL because `plugin_packages` still generates into committed Claude/Codex paths and the old package snapshots still exist.

## Task 2: Refactor plugin metadata for shared catalog entries

**Files:**
- Modify: `cities2_mcp/plugin_metadata.py`
- Test: `tests/test_packaging.py`

- [ ] **Step 1: Add catalog constants and entry builders**

In `cities2_mcp/plugin_metadata.py`, add constants near existing repository constants:

```python
CATALOG_REPO = "mayor-modder/Mayor-Modder-Cities2-Plugins"
CATALOG_NAME = "mayor-modder-cities2-plugins"
CATALOG_DISPLAY_NAME = "Mayor Modder Cities2 Plugins"
```

Add entry builders:

```python
def claude_marketplace_entry() -> dict[str, object]:
    return {
        "name": NAME,
        "source": "./integrations/anthropic/claude-plugin",
        "description": CLAUDE_DESCRIPTION,
        "version": VERSION,
        "author": AUTHOR,
    }


def codex_marketplace_entry() -> dict[str, object]:
    return {
        "name": NAME,
        "source": {"source": "local", "path": "./plugins/cities2-mcp"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Coding",
    }
```

Update `claude_marketplace_json()` to use the shared catalog top-level values while still producing a single-plugin local generated manifest:

```python
def claude_marketplace_json() -> str:
    return _dumps(
        {
            "name": CATALOG_NAME,
            "description": "Mayor Modder Cities2 Claude plugin marketplace.",
            "owner": AUTHOR,
            "plugins": [claude_marketplace_entry()],
        }
    )
```

Update `codex_marketplace_json()`:

```python
def codex_marketplace_json() -> str:
    return _dumps(
        {
            "name": CATALOG_NAME,
            "interface": {"displayName": CATALOG_DISPLAY_NAME},
            "plugins": [codex_marketplace_entry()],
        }
    )
```

- [ ] **Step 2: Update Codex generated README install command**

In `codex_readme_md()`, replace:

```sh
codex plugin marketplace add mayor-modder/Cities2-MCP
```

with:

```sh
codex plugin marketplace add {CATALOG_REPO}
```

using the f-string value already returned by the function.

- [ ] **Step 3: Update packaging metadata tests**

In `tests/test_packaging.py`, update `test_generated_metadata_is_valid_and_canonical` expectations:

```python
self.assertEqual(parsed["claude_marketplace_json"]["name"], meta.CATALOG_NAME)
self.assertEqual(parsed["codex_marketplace_json"]["name"], meta.CATALOG_NAME)
self.assertEqual(
    parsed["codex_marketplace_json"]["interface"]["displayName"],
    meta.CATALOG_DISPLAY_NAME,
)
self.assertEqual(parsed["claude_marketplace_json"]["plugins"][0], meta.claude_marketplace_entry())
self.assertEqual(parsed["codex_marketplace_json"]["plugins"][0], meta.codex_marketplace_entry())
```

Update the README assertion to expect:

```python
self.assertIn(
    "codex plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins",
    meta.codex_readme_md(),
)
```

- [ ] **Step 4: Run focused metadata tests**

Run:

```sh
python -m unittest tests.test_packaging.PluginPackagingTests.test_generated_metadata_is_valid_and_canonical -v
```

Expected: PASS after the metadata changes.

## Task 3: Move Claude/Codex generated roots to `dist/`

**Files:**
- Modify: `cities2_mcp/plugin_packages.py`
- Modify: `tests/test_packaging.py`

- [ ] **Step 1: Replace package root constants**

In `cities2_mcp/plugin_packages.py`, replace `PACKAGE_ROOTS` and `METADATA_FILES` setup with:

```python
CLAUDE_PACKAGE_ROOT = Path("dist/integrations/anthropic/claude-plugin")
CODEX_PACKAGE_ROOT = Path("dist/plugins/cities2-mcp")
ANTIGRAVITY_PACKAGE_ROOT = Path("plugins/cities2-mcp")
CATALOG_CLAUDE_PACKAGE_ROOT = Path("integrations/anthropic/claude-plugin")
CATALOG_CODEX_PACKAGE_ROOT = Path("plugins/cities2-mcp")
DEFAULT_CATALOG_ROOT = Path("../Mayor-Modder-Cities2-Plugins")

PACKAGE_ROOTS = (
    CLAUDE_PACKAGE_ROOT,
    CODEX_PACKAGE_ROOT,
    ANTIGRAVITY_PACKAGE_ROOT,
)

CLAUDE_AND_CODEX_PACKAGE_ROOTS = (
    CLAUDE_PACKAGE_ROOT,
    CODEX_PACKAGE_ROOT,
)
```

Set `METADATA_FILES` to write Claude/Codex metadata under `dist/`, and keep only Antigravity metadata under the committed `plugins/cities2-mcp` package:

```python
METADATA_FILES: dict[Path, tuple[tuple[Path, Callable[[], str]], ...]] = {
    CLAUDE_PACKAGE_ROOT: (
        (CLAUDE_PACKAGE_ROOT / ".claude-plugin" / "plugin.json", plugin_metadata.claude_plugin_json),
        (CLAUDE_PACKAGE_ROOT / ".mcp.json", plugin_metadata.claude_mcp_json),
        (CLAUDE_PACKAGE_ROOT / "README.md", plugin_metadata.claude_readme_md),
        (Path("dist/.claude-plugin/marketplace.json"), plugin_metadata.claude_marketplace_json),
    ),
    CODEX_PACKAGE_ROOT: (
        (CODEX_PACKAGE_ROOT / ".codex-plugin" / "plugin.json", plugin_metadata.codex_plugin_json),
        (CODEX_PACKAGE_ROOT / ".mcp.json", plugin_metadata.codex_mcp_json),
        (CODEX_PACKAGE_ROOT / "README.md", plugin_metadata.codex_readme_md),
        (Path("dist/.agents/plugins/marketplace.json"), plugin_metadata.codex_marketplace_json),
    ),
    ANTIGRAVITY_PACKAGE_ROOT: (
        (ANTIGRAVITY_PACKAGE_ROOT / "plugin.json", plugin_metadata.antigravity_plugin_json),
        (ANTIGRAVITY_PACKAGE_ROOT / "mcp_config.json", plugin_metadata.antigravity_mcp_config_json),
    ),
}
```

- [ ] **Step 2: Add package-root validation**

Add this helper near `sync_packages()`:

```python
def _selected_package_roots(package_roots: Iterable[Path]) -> tuple[Path, ...]:
    selected = tuple(Path(path) for path in package_roots)
    unknown = [path for path in selected if path not in METADATA_FILES]
    if unknown:
        raise ValueError(f"Unknown plugin package root: {unknown[0]}")
    return selected
```

Use it in `sync_packages()` and `check_packages()`:

```python
for package_rel in _selected_package_roots(package_roots):
    ...
```

- [ ] **Step 3: Update check output text**

In `main()`, change the stale output lines to:

```python
print("Generated copies: dist/integrations/anthropic/claude-plugin/, dist/plugins/cities2-mcp/, and plugins/cities2-mcp/ for Antigravity")
print("Run: python -m cities2_mcp.plugin_packages sync")
```

- [ ] **Step 4: Run focused package sync tests**

Run:

```sh
python -m unittest tests.test_packaging.PluginPackagingTests.test_plugin_package_check_detects_stale_payload tests.test_packaging.PluginPackagingTests.test_check_detects_and_sync_restores_each_metadata_file tests.test_packaging.PluginPackagingTests.test_plugin_package_check_output_explains_generated_artifact_sync -v
```

Expected: PASS after tests are updated to the new root paths.

## Task 4: Add catalog sync and marketplace upsert

**Files:**
- Modify: `cities2_mcp/plugin_packages.py`
- Modify: `tests/test_packaging.py`

- [ ] **Step 1: Write catalog sync tests**

Add a test that creates a catalog fixture with an existing Chief of Staff entry:

```python
def test_sync_catalog_packages_exports_claude_and_codex_without_removing_other_plugins(self) -> None:
    from cities2_mcp import plugin_packages

    with tempfile.TemporaryDirectory(prefix="cities2-mcp-catalog-sync-") as tmp:
        root = Path(tmp) / "source"
        catalog = Path(tmp) / "Mayor-Modder-Cities2-Plugins"
        self._write_plugin_sync_fixture(root)
        (catalog / "plugins").mkdir(parents=True)
        (catalog / ".agents" / "plugins").mkdir(parents=True)
        (catalog / "README.md").write_text("# Mayor Modder Cities2 Plugins\n", encoding="utf-8")
        (catalog / ".agents" / "plugins" / "marketplace.json").write_text(
            json.dumps(
                {
                    "name": "mayor-modder-cities2-plugins",
                    "interface": {"displayName": "Mayor Modder Cities2 Plugins"},
                    "plugins": [
                        {
                            "name": "cities2-chief-of-staff",
                            "source": {"source": "local", "path": "./plugins/cities2-chief-of-staff"},
                            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                            "category": "Coding",
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        changed = plugin_packages.sync_catalog_packages(catalog, repo_root=root)

        self.assertTrue((catalog / "integrations" / "anthropic" / "claude-plugin" / ".claude-plugin" / "plugin.json").is_file())
        self.assertTrue((catalog / "plugins" / "cities2-mcp" / ".codex-plugin" / "plugin.json").is_file())
        codex_marketplace = json.loads((catalog / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual([plugin["name"] for plugin in codex_marketplace["plugins"]], ["cities2-chief-of-staff", "cities2-mcp"])
        claude_marketplace = json.loads((catalog / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual([plugin["name"] for plugin in claude_marketplace["plugins"]], ["cities2-mcp"])
        self.assertTrue(any(path.name == "plugin.json" for path in changed))
```

Add a missing-catalog test:

```python
def test_sync_catalog_packages_requires_catalog_checkout(self) -> None:
    from cities2_mcp import plugin_packages

    with tempfile.TemporaryDirectory(prefix="cities2-mcp-catalog-missing-") as tmp:
        root = Path(tmp) / "source"
        catalog = Path(tmp) / "missing"
        self._write_plugin_sync_fixture(root)

        with self.assertRaises(FileNotFoundError):
            plugin_packages.sync_catalog_packages(catalog, repo_root=root)
```

- [ ] **Step 2: Implement catalog sync**

In `cities2_mcp/plugin_packages.py`, add:

```python
CATALOG_PACKAGE_EXPORTS = (
    (CLAUDE_PACKAGE_ROOT, CATALOG_CLAUDE_PACKAGE_ROOT),
    (CODEX_PACKAGE_ROOT, CATALOG_CODEX_PACKAGE_ROOT),
)
```

Add:

```python
def sync_catalog_packages(
    catalog_root: Path | str = DEFAULT_CATALOG_ROOT,
    *,
    repo_root: Path | str = Path.cwd(),
) -> tuple[Path, ...]:
    root = Path(repo_root).resolve()
    catalog = Path(catalog_root).resolve()
    _validate_catalog_root(catalog)
    sync_packages(root, package_roots=CLAUDE_AND_CODEX_PACKAGE_ROOTS)

    changed: list[Path] = []
    for source_rel, target_rel in CATALOG_PACKAGE_EXPORTS:
        source = root / source_rel
        target = catalog / target_rel
        _ensure_inside(catalog, target)
        changed.extend(_changed_tree_paths(source, target))
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)

    changed.extend(_upsert_catalog_marketplaces(catalog))
    return tuple(sorted(set(changed)))
```

Add helpers:

```python
def _validate_catalog_root(catalog: Path) -> None:
    if not catalog.is_dir():
        raise FileNotFoundError(f"Catalog root not found: {catalog}")
    if not (catalog / "plugins").is_dir():
        raise FileNotFoundError(f"Catalog plugins directory not found: {catalog / 'plugins'}")


def _ensure_inside(root: Path, target: Path) -> None:
    if not target.resolve().is_relative_to(root):
        raise ValueError(f"Catalog target escapes catalog root: {target}")
```

Add marketplace upsert helpers:

```python
def _upsert_catalog_marketplaces(catalog: Path) -> tuple[Path, ...]:
    return (
        *_upsert_marketplace(
            catalog / ".claude-plugin" / "marketplace.json",
            {
                "name": plugin_metadata.CATALOG_NAME,
                "description": "Mayor Modder Cities2 Claude plugin marketplace.",
                "owner": plugin_metadata.AUTHOR,
                "plugins": [],
            },
            plugin_metadata.claude_marketplace_entry(),
        ),
        *_upsert_marketplace(
            catalog / ".agents" / "plugins" / "marketplace.json",
            {
                "name": plugin_metadata.CATALOG_NAME,
                "interface": {"displayName": plugin_metadata.CATALOG_DISPLAY_NAME},
                "plugins": [],
            },
            plugin_metadata.codex_marketplace_entry(),
        ),
    )


def _upsert_marketplace(path: Path, default_manifest: dict[str, object], entry: dict[str, object]) -> tuple[Path, ...]:
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default_manifest
    plugins = list(manifest.get("plugins", []))
    plugins = [plugin for plugin in plugins if plugin.get("name") != entry["name"]]
    plugins.append(entry)
    manifest["plugins"] = plugins
    content = plugin_metadata._dumps(manifest)
    current = path.read_text(encoding="utf-8") if path.is_file() else None
    if current == content:
        return ()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return (path,)
```

Add `import json` at the top of `plugin_packages.py`.

- [ ] **Step 3: Expose CLI command**

Change:

```python
parser.add_argument("command", choices=("sync", "check"))
```

to:

```python
parser.add_argument("command", choices=("sync", "check", "sync-catalog"))
parser.add_argument("--catalog-root", type=Path, default=DEFAULT_CATALOG_ROOT)
```

Add before the `check` branch:

```python
if args.command == "sync-catalog":
    changed = sync_catalog_packages(args.catalog_root, repo_root=args.repo_root)
    for path in changed:
        print(f"updated {path}")
    return 0
```

- [ ] **Step 4: Run catalog sync tests**

Run:

```sh
python -m unittest tests.test_packaging.PluginPackagingTests.test_sync_catalog_packages_exports_claude_and_codex_without_removing_other_plugins tests.test_packaging.PluginPackagingTests.test_sync_catalog_packages_requires_catalog_checkout -v
```

Expected: PASS.

## Task 5: Update launcher/package smoke tests to generate fixtures

**Files:**
- Modify: `tests/test_packaging.py`

- [ ] **Step 1: Add a helper that builds a full package fixture from the real repo**

Add this helper to `PluginPackagingTests`:

```python
def _generated_package_root(self, package_root: Path) -> Path:
    from cities2_mcp import plugin_packages

    tmp = tempfile.TemporaryDirectory(prefix="cities2-mcp-generated-package-")
    self.addCleanup(tmp.cleanup)
    root = Path(tmp.name)
    shutil.copytree(ROOT / "skills", root / "skills")
    shutil.copytree(ROOT / "cities2_mcp", root / "cities2_mcp", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))
    plugin_packages.sync_packages(root, package_roots=(package_root,))
    return root / package_root
```

- [ ] **Step 2: Update Claude smoke tests**

In `test_anthropic_distribution_artifacts_are_version_aligned`, `test_claude_plugin_vendored_launcher_reports_version`, and `test_claude_plugin_vendored_launcher_serves_mcp`, replace:

```python
plugin_root = ROOT / "integrations" / "anthropic" / "claude-plugin"
```

with:

```python
from cities2_mcp import plugin_packages

plugin_root = self._generated_package_root(plugin_packages.CLAUDE_PACKAGE_ROOT)
```

Read the marketplace from:

```python
marketplace = json.loads((plugin_root.parents[3] / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
```

If the parent expression is unclear in implementation, use:

```python
generated_root = plugin_root.parents[3]
marketplace = json.loads((generated_root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
```

- [ ] **Step 3: Update Codex smoke tests**

In Codex package tests, replace:

```python
plugin_root = ROOT / "plugins" / "cities2-mcp"
```

with:

```python
from cities2_mcp import plugin_packages

plugin_root = self._generated_package_root(plugin_packages.CODEX_PACKAGE_ROOT)
```

Read the generated Codex marketplace from:

```python
generated_root = plugin_root.parents[2]
marketplace = json.loads((generated_root / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
```

Do not change Antigravity tests that intentionally use `ROOT / "plugins" / "cities2-mcp"`.

- [ ] **Step 4: Run smoke tests**

Run:

```sh
python -m unittest tests.test_packaging.PluginPackagingTests.test_anthropic_distribution_artifacts_are_version_aligned tests.test_packaging.PluginPackagingTests.test_claude_plugin_vendored_launcher_reports_version tests.test_packaging.PluginPackagingTests.test_codex_distribution_artifacts_are_version_aligned tests.test_packaging.PluginPackagingTests.test_codex_plugin_vendored_launcher_reports_version -v
```

Expected: PASS.

## Task 6: Update install docs for shared catalog

**Files:**
- Modify: `INSTALL.md`
- Modify: `tests/test_portability.py`
- Modify: `cities2_mcp/plugin_metadata.py`

- [ ] **Step 1: Update portability expectations**

In `test_docs_include_current_claude_desktop_plugin_marketplace_path`, replace expected repo strings with:

```python
self.assertIn("mayor-modder/Mayor-Modder-Cities2-Plugins", text)
self.assertIn("/plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins", install_text)
self.assertNotIn("/plugin marketplace add mayor-modder/Cities2-MCP", install_text)
```

In `test_docs_include_codex_plugin_marketplace_path`, replace:

```python
self.assertIn("codex plugin marketplace add mayor-modder/Cities2-MCP", install_text)
```

with:

```python
self.assertIn("codex plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins", install_text)
self.assertNotIn("codex plugin marketplace add mayor-modder/Cities2-MCP", install_text)
```

Remove any test dependency on `plugins/cities2-mcp/README.md` for Codex-specific text because the Codex package README is generated under `dist/`.

- [ ] **Step 2: Update `INSTALL.md`**

Replace the Claude Code command:

```text
/plugin marketplace add mayor-modder/Cities2-MCP
```

with:

```text
/plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins
```

Replace the Codex CLI command:

```sh
codex plugin marketplace add mayor-modder/Cities2-MCP
```

with:

```sh
codex plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins
```

In the Codex app section, replace the source value:

```text
mayor-modder/Cities2-MCP
```

with:

```text
mayor-modder/Mayor-Modder-Cities2-Plugins
```

Leave the Google Antigravity section unchanged.

- [ ] **Step 3: Run portability tests**

Run:

```sh
python -m unittest tests.test_portability.PortabilityTests.test_docs_include_current_claude_desktop_plugin_marketplace_path tests.test_portability.PortabilityTests.test_docs_include_codex_plugin_marketplace_path tests.test_portability.PortabilityTests.test_docs_include_antigravity_install_paths tests.test_portability.PortabilityTests.test_claude_and_codex_package_snapshots_are_not_committed -v
```

Expected: PASS after old Claude/Codex package files are removed.

## Task 7: Remove committed Claude/Codex package snapshots

**Files:**
- Delete: `.claude-plugin/marketplace.json`
- Delete: `.agents/plugins/marketplace.json`
- Delete: `integrations/anthropic/claude-plugin/`
- Delete: `plugins/cities2-mcp/.codex-plugin/`
- Delete: `plugins/cities2-mcp/.mcp.json`
- Delete: `plugins/cities2-mcp/README.md`

- [ ] **Step 1: Remove only Claude/Codex package snapshot files**

Run:

```sh
git rm -r -- .claude-plugin .agents integrations/anthropic/claude-plugin plugins/cities2-mcp/.codex-plugin plugins/cities2-mcp/.mcp.json plugins/cities2-mcp/README.md
```

Expected: Git stages deletions for Claude/Codex package snapshots only. It must not remove `plugins/cities2-mcp/plugin.json`, `plugins/cities2-mcp/mcp_config.json`, `plugins/cities2-mcp/bin`, `plugins/cities2-mcp/skills`, or `plugins/cities2-mcp/vendor`.

- [ ] **Step 2: Verify Antigravity package files remain**

Run:

```sh
Test-Path plugins/cities2-mcp/plugin.json; Test-Path plugins/cities2-mcp/mcp_config.json; Test-Path plugins/cities2-mcp/bin/cities2-mcp-launcher.js
```

Expected: PowerShell prints `True` three times.

- [ ] **Step 3: Check deleted paths**

Run:

```sh
git status --short
```

Expected: deletions for the old Claude/Codex paths and modifications to code/docs/tests/spec/plan only.

## Task 8: Full verification

**Files:**
- No new file edits unless verification reveals a failure.

- [ ] **Step 1: Run packaging tests**

Run:

```sh
python -m unittest tests.test_packaging -v
```

Expected: PASS.

- [ ] **Step 2: Run portability tests**

Run:

```sh
python -m unittest tests.test_portability -v
```

Expected: PASS.

- [ ] **Step 3: Run package check**

Run:

```sh
python -m cities2_mcp.plugin_packages check
```

Expected: `Plugin package payloads are in sync.` and exit code 0.

- [ ] **Step 4: Run catalog sync against a temp fixture**

Run:

```sh
python -m unittest tests.test_packaging.PluginPackagingTests.test_sync_catalog_packages_exports_claude_and_codex_without_removing_other_plugins -v
```

Expected: PASS and the test confirms Chief of Staff marketplace entries are preserved.

- [ ] **Step 5: Inspect final diff**

Run:

```sh
git status --short --branch
git diff --stat
git diff --check
```

Expected: branch is `codex/catalog-export-flow`; `git diff --check` reports no whitespace errors.

## Self-review

- Spec coverage: Tasks cover dist generation, catalog sync, marketplace upsert, install docs, removal of committed Claude/Codex snapshots, and verification gates. Antigravity remains unchanged except for preserving its existing package path.
- Placeholder scan: No placeholder markers or vague implementation steps are intentionally left in this plan.
- Type consistency: Planned constants are `CLAUDE_PACKAGE_ROOT`, `CODEX_PACKAGE_ROOT`, `ANTIGRAVITY_PACKAGE_ROOT`, `DEFAULT_CATALOG_ROOT`, and `sync_catalog_packages(...)`; tests and CLI steps use those same names.
