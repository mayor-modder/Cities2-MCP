# Centralize plugin distribution artifacts — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate every hand-maintained plugin distribution metadata file (`plugin.json`, `.mcp.json`, `README.md`, `marketplace.json`, `mcp_config.json`) for the Claude, Codex, and Antigravity distributions from one canonical Python module, so `sync` regenerates them and `check` fails on drift.

**Architecture:** A new `cities2_mcp/plugin_metadata.py` holds shared identity constants, the verbatim platform-specific structures, and one pure builder function per artifact (JSON via `json.dumps`, READMEs via templates). `cities2_mcp/plugin_packages.py` gains a per-package-root metadata registry and a metadata pass in `sync_packages`/`check_packages` that compares/writes those files directly against the real tree using text (universal-newline) I/O.

**Tech stack:** Python 3.10+, stdlib only (`json`, `pathlib`), `unittest`.

**Spec:** [docs/superpowers/specs/2026-06-06-centralize-plugin-distribution-artifacts-design.md](../specs/2026-06-06-centralize-plugin-distribution-artifacts-design.md) (issue #33).

**Commit/push gating:** This repo's `AGENTS.md` requires explicit user agreement before committing or pushing. The commit steps below are part of the plan; when executing, confirm with the maintainer before running them (batching is fine). Net hand-written diff is ~480 lines (under the 800 hard limit) → single PR.

---

## File structure

- **Create** `cities2_mcp/plugin_metadata.py` — canonical metadata + per-platform builders. One responsibility: produce artifact content strings. No filesystem access.
- **Modify** `cities2_mcp/plugin_packages.py` — import `SKILL_NAMES` from `plugin_metadata`; add `METADATA_FILES` registry + metadata pass in `sync_packages`/`check_packages`.
- **Modify** `cities2_mcp/agent_assets.py` — import `SKILL_NAMES` from `plugin_metadata` instead of redefining it.
- **Modify** `tests/test_packaging.py` — add builder, repo-in-sync, drift tests.
- **Modify** `CONTRIBUTING.md` — Canonical vs generated subsection.
- **Regenerated (generated; excluded from size budget)** the 10 metadata files + re-vendored `vendor/cities2_mcp/` copies in both distro roots, committed after the first `sync`.

---

## Task 1: Builder unit tests (test-first)

**Files:**
- Test: `tests/test_packaging.py` (add two methods to `PackagingTests`)

- [ ] **Step 1: Write the failing tests**

Add these two methods inside the `PackagingTests` class in `tests/test_packaging.py` (e.g. after `test_plugin_package_sync_updates_stale_payload`):

```python
    def test_metadata_builders_are_deterministic(self) -> None:
        from cities2_mcp import plugin_metadata as meta

        builders = (
            meta.claude_plugin_json,
            meta.claude_mcp_json,
            meta.claude_readme_md,
            meta.claude_marketplace_json,
            meta.codex_plugin_json,
            meta.codex_mcp_json,
            meta.codex_readme_md,
            meta.codex_marketplace_json,
            meta.antigravity_plugin_json,
            meta.antigravity_mcp_config_json,
        )
        for builder in builders:
            self.assertEqual(builder(), builder(), builder.__name__)

    def test_generated_metadata_is_valid_and_canonical(self) -> None:
        import cities2_mcp
        from cities2_mcp import plugin_metadata as meta

        json_builders = {
            "claude_plugin_json": meta.claude_plugin_json,
            "claude_mcp_json": meta.claude_mcp_json,
            "claude_marketplace_json": meta.claude_marketplace_json,
            "codex_plugin_json": meta.codex_plugin_json,
            "codex_mcp_json": meta.codex_mcp_json,
            "codex_marketplace_json": meta.codex_marketplace_json,
            "antigravity_plugin_json": meta.antigravity_plugin_json,
            "antigravity_mcp_config_json": meta.antigravity_mcp_config_json,
        }
        parsed = {}
        for label, builder in json_builders.items():
            text = builder()
            self.assertTrue(text.endswith("\n"), label)
            parsed[label] = json.loads(text)  # raises on invalid JSON

        version = cities2_mcp.__version__
        self.assertEqual(parsed["claude_plugin_json"]["version"], version)
        self.assertEqual(parsed["codex_plugin_json"]["version"], version)
        self.assertEqual(parsed["antigravity_plugin_json"]["version"], version)
        self.assertEqual(parsed["claude_marketplace_json"]["plugins"][0]["version"], version)
        for label in (
            "claude_mcp_json",
            "codex_mcp_json",
            "antigravity_mcp_config_json",
            "codex_marketplace_json",
        ):
            self.assertNotIn("version", parsed[label])

        for label in (
            "claude_plugin_json",
            "codex_plugin_json",
            "antigravity_plugin_json",
            "claude_marketplace_json",
            "codex_marketplace_json",
        ):
            self.assertEqual(parsed[label]["name"], meta.NAME, label)

        self.assertEqual(parsed["claude_plugin_json"]["author"], meta.AUTHOR)
        self.assertEqual(parsed["codex_plugin_json"]["author"], meta.AUTHOR)
        self.assertEqual(parsed["claude_marketplace_json"]["owner"], meta.AUTHOR)
        self.assertEqual(parsed["claude_plugin_json"]["keywords"], meta.KEYWORDS)
        self.assertEqual(parsed["codex_plugin_json"]["keywords"], meta.KEYWORDS)
        self.assertEqual(parsed["claude_plugin_json"]["repository"], meta.REPO_URL)
        self.assertEqual(parsed["codex_plugin_json"]["repository"], meta.REPO_URL)
        self.assertEqual(
            parsed["codex_plugin_json"]["interface"]["privacyPolicyURL"], meta.PRIVACY_URL
        )

        for readme in (meta.claude_readme_md(), meta.codex_readme_md()):
            self.assertIn("Generated by cities2_mcp.plugin_packages", readme)
            for name in meta.SKILL_NAMES:
                self.assertIn(name, readme)
        self.assertIn(
            "claude plugin validate integrations/anthropic/claude-plugin --strict",
            meta.claude_readme_md(),
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -3 -m unittest tests.test_packaging.PackagingTests.test_metadata_builders_are_deterministic tests.test_packaging.PackagingTests.test_generated_metadata_is_valid_and_canonical -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'cities2_mcp.plugin_metadata'`.

---

## Task 2: Create the canonical module `cities2_mcp/plugin_metadata.py`

**Files:**
- Create: `cities2_mcp/plugin_metadata.py`

- [ ] **Step 1: Create the module**

Create `cities2_mcp/plugin_metadata.py` with this exact content:

```python
from __future__ import annotations

import json

from cities2_mcp import __version__ as VERSION

NAME = "cities2-mcp"
DISPLAY_NAME = "Cities2 MCP and Modding Toolkit"
AUTHOR = {"name": "mayor-modder", "url": "https://github.com/mayor-modder"}
REPO_URL = "https://github.com/mayor-modder/Cities2-MCP"
LICENSE = "MIT"
PRIVACY_URL = "https://github.com/mayor-modder/Cities2-MCP/blob/main/PRIVACY.md"
TERMS_URL = "https://github.com/mayor-modder/Cities2-MCP#license"
KEYWORDS = ["cities-skylines-ii", "mcp", "modding", "gameplay", "agent-skills"]

SKILL_NAMES = (
    "cities2-knowledge",
    "cities2-modding",
    "cities2-mod-review",
    "cities2-mod-debugging",
    "cities2-mod-release",
)

CLAUDE_DESCRIPTION = "Cities2 MCP and Modding Toolkit for Claude."
CODEX_DESCRIPTION = "Cities2 MCP and Modding Toolkit for Codex."
ANTIGRAVITY_DESCRIPTION = "Cities: Skylines II knowledge and modding tools for AI agents."
CLAUDE_MARKETPLACE_DESCRIPTION = "Claude plugin marketplace for Cities2 MCP and Modding Toolkit."

CLAUDE_USER_CONFIG = {
    "trusted_workspace": {
        "type": "directory",
        "title": "Trusted mod projects folder",
        "description": "Optional. Choose the parent folder that contains your mod projects to enable scaffold, edit, analyze, build, and package workflows for projects underneath it.",
        "required": False,
    },
    "mods_dir": {
        "type": "directory",
        "title": "Cities: Skylines II Mods folder",
        "description": "Optional. The plugin normally uses the standard local Mods folder; set this only if your Mods folder is somewhere else.",
        "required": False,
    },
    "game_dir": {
        "type": "directory",
        "title": "Cities: Skylines II install folder",
        "description": "Optional. The plugin normally discovers Steam installs automatically; set this only if encyclopedia search cannot find your game.",
        "required": False,
    },
    "locale_cok": {
        "type": "file",
        "title": "Locale.cok file",
        "description": "Optional. Direct path to Locale.cok; use only when automatic game discovery cannot find the in-game encyclopedia file.",
        "required": False,
    },
}

CODEX_INTERFACE = {
    "displayName": DISPLAY_NAME,
    "shortDescription": "Cities: Skylines II knowledge and modding tools",
    "longDescription": "Cities2 MCP and Modding Toolkit gives Codex local access to bundled Cities: Skylines II Wiki text, the user's installed in-game encyclopedia when available, and mod project workflow tools inside the current workspace.",
    "developerName": "mayor-modder",
    "category": "Coding",
    "capabilities": ["Read", "Write"],
    "websiteURL": REPO_URL,
    "privacyPolicyURL": PRIVACY_URL,
    "termsOfServiceURL": TERMS_URL,
    "defaultPrompt": [
        "What changed in the latest Cities: Skylines II patch?",
        "Scaffold a Cities: Skylines II UI mod.",
        "Build and package this Cities: Skylines II mod.",
    ],
    "brandColor": "#1F6F78",
    "screenshots": [],
}

# Verbatim copy of the single-line inline node bootstrap currently in
# plugins/cities2-mcp/mcp_config.json. The pieces below concatenate (no
# separators) into the exact original string. The test in Task 2/Step 3 asserts
# byte-equality with the current file, so any drift here fails fast.
ANTIGRAVITY_BOOTSTRAP_JS = (
    "const fs=require('node:fs');const os=require('node:os');const path=require('node:path');"
    "const home=process.env.USERPROFILE||process.env.HOME||os.homedir();"
    "const installed=[path.join(home,'.gemini','antigravity-cli','plugins','cities2-mcp'),"
    "path.join(home,'.gemini','config','plugins','cities2-mcp')];"
    "const workspaceRoots=process.env.CITIES2_MCP_ALLOW_WORKSPACE_PLUGIN_ROOTS==='1'?"
    "[path.join(process.cwd(),'.agents','plugins','cities2-mcp'),"
    "path.join(process.cwd(),'_agents','plugins','cities2-mcp')]:[];"
    "const candidates=[process.env.CITIES2_MCP_PLUGIN_ROOT,process.env.ANTIGRAVITY_PLUGIN_ROOT,"
    "...installed,...workspaceRoots].filter(Boolean);"
    "const root=candidates.find((candidate)=>fs.existsSync(path.join(candidate,'bin','cities2-mcp-launcher.js')));"
    "if(!root){console.error('Unable to locate the installed Cities2-MCP Antigravity plugin. "
    "Set CITIES2_MCP_PLUGIN_ROOT to the plugin directory. Checked: '+candidates.join('; '));process.exit(1);}"
    "const launcher=path.join(root,'bin','cities2-mcp-launcher.js');process.env.PLUGIN_ROOT=root;"
    "process.argv=[process.argv[0],launcher,...process.argv.slice(1)];require(launcher);"
)

_GENERATED_MARKER = (
    "<!-- Generated by cities2_mcp.plugin_packages; "
    "edit canonical sources in cities2_mcp/plugin_metadata.py, not this file. -->"
)


def _dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def claude_plugin_json() -> str:
    return _dumps(
        {
            "name": NAME,
            "displayName": DISPLAY_NAME,
            "version": VERSION,
            "description": CLAUDE_DESCRIPTION,
            "author": AUTHOR,
            "homepage": REPO_URL,
            "repository": REPO_URL,
            "license": LICENSE,
            "userConfig": CLAUDE_USER_CONFIG,
            "keywords": KEYWORDS,
        }
    )


def claude_mcp_json() -> str:
    return _dumps(
        {
            "mcpServers": {
                "cities2-mcp": {
                    "command": "node",
                    "args": [
                        "${CLAUDE_PLUGIN_ROOT}/bin/cities2-mcp-launcher.js",
                        "--workspace",
                        "${CLAUDE_PROJECT_DIR}",
                    ],
                    "env": {
                        "CITIES2_MCP_WORKSPACE": "${user_config.trusted_workspace}",
                        "CITIES2_MODS_DIR": "${user_config.mods_dir}",
                        "CITIES2_GAME_DIR": "${user_config.game_dir}",
                        "CITIES2_LOCALE_COK": "${user_config.locale_cok}",
                    },
                }
            }
        }
    )


def claude_marketplace_json() -> str:
    return _dumps(
        {
            "name": NAME,
            "description": CLAUDE_MARKETPLACE_DESCRIPTION,
            "owner": AUTHOR,
            "plugins": [
                {
                    "name": NAME,
                    "source": "./integrations/anthropic/claude-plugin",
                    "description": CLAUDE_DESCRIPTION,
                    "version": VERSION,
                    "author": AUTHOR,
                }
            ],
        }
    )


def claude_readme_md() -> str:
    skill_lines = "\n".join(f"- `/{name}`" for name in SKILL_NAMES)
    return f"""{_GENERATED_MARKER}

# Cities2 MCP and Modding Toolkit Claude plugin

This is the Claude plugin package for Cities2 MCP and Modding Toolkit. It bundles five user-facing agent skills and a plugin-local MCP server launcher.

The plugin gives Claude:

{skill_lines}
- the `cities2-mcp` MCP server, started automatically when the plugin is enabled

The plugin `.mcp.json` points at `bin/cities2-mcp-launcher.js`, which runs the vendored Python package from `vendor/cities2_mcp`. In Claude Code, it automatically sets the MCP workspace to the current project via `${{CLAUDE_PROJECT_DIR}}`.

Validate from the repository root:

```sh
claude plugin validate integrations/anthropic/claude-plugin --strict
```
"""


def codex_plugin_json() -> str:
    return _dumps(
        {
            "name": NAME,
            "version": VERSION,
            "description": CODEX_DESCRIPTION,
            "author": AUTHOR,
            "homepage": REPO_URL,
            "repository": REPO_URL,
            "license": LICENSE,
            "keywords": KEYWORDS,
            "skills": "./skills/",
            "mcpServers": "./.mcp.json",
            "interface": CODEX_INTERFACE,
        }
    )


def codex_mcp_json() -> str:
    return _dumps(
        {
            "mcpServers": {
                "cities2-mcp": {
                    "command": "node",
                    "args": ["./bin/cities2-mcp-launcher.js", "--workspace", "."],
                    "cwd": ".",
                }
            }
        }
    )


def codex_marketplace_json() -> str:
    return _dumps(
        {
            "name": NAME,
            "interface": {"displayName": DISPLAY_NAME},
            "plugins": [
                {
                    "name": NAME,
                    "source": {"source": "local", "path": "./plugins/cities2-mcp"},
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                    "category": "Coding",
                }
            ],
        }
    )


def codex_readme_md() -> str:
    head = ", ".join(f"`{name}`" for name in SKILL_NAMES[:-1])
    included = f"{head}, and `{SKILL_NAMES[-1]}`"
    return f"""{_GENERATED_MARKER}

# Cities2 MCP and Modding Toolkit Codex plugin

This is the Codex plugin package for Cities2 MCP and Modding Toolkit. It bundles five user-facing agent skills and a plugin-local MCP server launcher.

Included skills: {included}.

The plugin `.mcp.json` points at `bin/cities2-mcp-launcher.js`, which runs the vendored Python package from `vendor/cities2_mcp`. Codex currently launches the server from the installed plugin cache, so wiki and encyclopedia tools work immediately, while direct MCP workflow tools may be allowlist-blocked for the project you opened. The bundled `cities2-modding` skill includes an explicit template-copy fallback for that case.

Install from this repository marketplace:

```sh
codex plugin marketplace add mayor-modder/Cities2-MCP
```
"""


def antigravity_plugin_json() -> str:
    return _dumps(
        {
            "name": NAME,
            "description": ANTIGRAVITY_DESCRIPTION,
            "version": VERSION,
        }
    )


def antigravity_mcp_config_json() -> str:
    return _dumps(
        {
            "mcpServers": {
                "cities2-mcp": {
                    "command": "node",
                    "args": ["-e", ANTIGRAVITY_BOOTSTRAP_JS, "--", "--workspace", "."],
                    "cwd": ".",
                }
            }
        }
    )
```

- [ ] **Step 2: Run the Task 1 tests to verify they pass**

Run: `py -3 -m unittest tests.test_packaging.PackagingTests.test_metadata_builders_are_deterministic tests.test_packaging.PackagingTests.test_generated_metadata_is_valid_and_canonical -v`

Expected: PASS (2 tests).

- [ ] **Step 3: Guard — builders semantically match the current on-disk files (pre-sync fidelity check)**

This proves the builders reproduce the current artifacts (catching any value/key/bootstrap typo) BEFORE the first `sync` overwrites anything. The 6 round-trip-identical JSON files must match byte-for-byte; all 8 must match after JSON parsing (whitespace-insensitive).

Run:

```sh
py -3 -c "import json; from pathlib import Path; from cities2_mcp import plugin_metadata as m; exact={'plugins/cities2-mcp/.mcp.json':m.codex_mcp_json,'plugins/cities2-mcp/mcp_config.json':m.antigravity_mcp_config_json,'plugins/cities2-mcp/plugin.json':m.antigravity_plugin_json,'integrations/anthropic/claude-plugin/.mcp.json':m.claude_mcp_json,'.claude-plugin/marketplace.json':m.claude_marketplace_json,'.agents/plugins/marketplace.json':m.codex_marketplace_json}; semantic={'integrations/anthropic/claude-plugin/.claude-plugin/plugin.json':m.claude_plugin_json,'plugins/cities2-mcp/.codex-plugin/plugin.json':m.codex_plugin_json}; [exec(\"assert b()==Path(p).read_text(encoding='utf-8'), 'exact mismatch: '+p\") for p,b in exact.items()]; [exec(\"assert json.loads(b())==json.loads(Path(p).read_text(encoding='utf-8')), 'semantic mismatch: '+p\") for p,b in semantic.items()]; print('builders match current artifacts')"
```

Expected: prints `builders match current artifacts`. If any assertion fires, fix the corresponding builder/constant (most likely `ANTIGRAVITY_BOOTSTRAP_JS`) before continuing.

- [ ] **Step 4: Commit**

```sh
git add cities2_mcp/plugin_metadata.py tests/test_packaging.py
git commit -m "Add canonical plugin metadata module with per-platform builders (#33)"
```

---

## Task 3: Make `SKILL_NAMES` a single source

**Files:**
- Modify: `cities2_mcp/agent_assets.py:11-17`
- Modify: `cities2_mcp/plugin_packages.py:9-15`

- [ ] **Step 1: Replace the `agent_assets.py` definition with an import**

In `cities2_mcp/agent_assets.py`, replace the local tuple (lines 11–17):

```python
SKILL_NAMES = (
    "cities2-knowledge",
    "cities2-modding",
    "cities2-mod-review",
    "cities2-mod-debugging",
    "cities2-mod-release",
)
```

with:

```python
from .plugin_metadata import SKILL_NAMES
```

(Place the import with the other imports near the top — e.g. directly under `from . import package_root` on line 9 — and delete the old tuple. `LEGACY_ASSET_NAMES` on the next line stays.)

- [ ] **Step 2: Replace the `plugin_packages.py` definition with an import**

In `cities2_mcp/plugin_packages.py`, replace the local tuple (lines 9–15):

```python
SKILL_NAMES = (
    "cities2-knowledge",
    "cities2-modding",
    "cities2-mod-review",
    "cities2-mod-debugging",
    "cities2-mod-release",
)
```

with:

```python
from cities2_mcp import plugin_metadata
from cities2_mcp.plugin_metadata import SKILL_NAMES
```

(Keep these with the existing imports at the top of the file. `plugin_packages` already uses `SKILL_NAMES` in `_copy_skills`; the `plugin_metadata` module import is used by Task 4.)

- [ ] **Step 3: Run the existing packaging + asset tests to confirm no regression**

Run: `py -3 -m unittest tests.test_packaging -v`

Expected: PASS (all existing tests plus the two from Task 1).

- [ ] **Step 4: Commit**

```sh
git add cities2_mcp/agent_assets.py cities2_mcp/plugin_packages.py
git commit -m "Consolidate SKILL_NAMES into plugin_metadata single source (#33)"
```

---

## Task 4: Add the metadata registry and the sync/check metadata pass

**Files:**
- Modify: `cities2_mcp/plugin_packages.py`

- [ ] **Step 1: Add the `Callable` import**

In `cities2_mcp/plugin_packages.py`, change the typing import line:

```python
from typing import Iterable
```

to:

```python
from typing import Callable, Iterable
```

- [ ] **Step 2: Add the metadata registry**

Add this near the top of `cities2_mcp/plugin_packages.py`, after the `PACKAGE_ROOTS` definition (around line 20):

```python
METADATA_FILES: dict[Path, tuple[tuple[Path, Callable[[], str]], ...]] = {
    Path("integrations/anthropic/claude-plugin"): (
        (
            Path("integrations/anthropic/claude-plugin/.claude-plugin/plugin.json"),
            plugin_metadata.claude_plugin_json,
        ),
        (Path("integrations/anthropic/claude-plugin/.mcp.json"), plugin_metadata.claude_mcp_json),
        (Path("integrations/anthropic/claude-plugin/README.md"), plugin_metadata.claude_readme_md),
        (Path(".claude-plugin/marketplace.json"), plugin_metadata.claude_marketplace_json),
    ),
    Path("plugins/cities2-mcp"): (
        (Path("plugins/cities2-mcp/.codex-plugin/plugin.json"), plugin_metadata.codex_plugin_json),
        (Path("plugins/cities2-mcp/.mcp.json"), plugin_metadata.codex_mcp_json),
        (Path("plugins/cities2-mcp/README.md"), plugin_metadata.codex_readme_md),
        (Path(".agents/plugins/marketplace.json"), plugin_metadata.codex_marketplace_json),
        (Path("plugins/cities2-mcp/plugin.json"), plugin_metadata.antigravity_plugin_json),
        (Path("plugins/cities2-mcp/mcp_config.json"), plugin_metadata.antigravity_mcp_config_json),
    ),
}
```

- [ ] **Step 3: Add the metadata sync/check helpers**

Add these two functions to `cities2_mcp/plugin_packages.py` (e.g. directly after `_replace_payload`):

```python
def _sync_metadata(repo_root: Path, package_rel: Path) -> list[Path]:
    changed: list[Path] = []
    for rel, builder in METADATA_FILES.get(package_rel, ()):
        target = repo_root / rel
        content = builder()
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current != content:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            changed.append(target)
    return changed


def _check_metadata(repo_root: Path, package_rel: Path) -> list[Path]:
    stale: list[Path] = []
    for rel, builder in METADATA_FILES.get(package_rel, ()):
        target = repo_root / rel
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current != builder():
            stale.append(target)
    return stale
```

Note: text I/O (`read_text`/`write_text`), **not** `read_bytes`/`write_bytes`. On Windows the JSON files are checked out as CRLF (`.gitattributes` only forces LF for `*.md`); `read_text` decodes CRLF to `"\n"` to match the builder, and `write_text` re-emits the platform newline so `sync` does not fight git autocrlf.

- [ ] **Step 4: Wire the metadata pass into `sync_packages`**

In `sync_packages`, the per-root loop currently reads:

```python
        for package_rel in package_roots:
            expected_root = tmp_root / package_rel
            actual_root = root / package_rel
            _write_payload(root, expected_root)
            changed.extend(_changed_paths(expected_root, actual_root))
            _replace_payload(expected_root, actual_root)
```

Add the metadata sync as the last line of the loop body:

```python
        for package_rel in package_roots:
            expected_root = tmp_root / package_rel
            actual_root = root / package_rel
            _write_payload(root, expected_root)
            changed.extend(_changed_paths(expected_root, actual_root))
            _replace_payload(expected_root, actual_root)
            changed.extend(_sync_metadata(root, package_rel))
```

- [ ] **Step 5: Wire the metadata pass into `check_packages`**

In `check_packages`, the per-root loop currently reads:

```python
        for package_rel in package_roots:
            expected_root = tmp_root / package_rel
            actual_root = root / package_rel
            _write_payload(root, expected_root)
            changed.extend(_changed_paths(expected_root, actual_root))
```

Add the metadata check as the last line of the loop body:

```python
        for package_rel in package_roots:
            expected_root = tmp_root / package_rel
            actual_root = root / package_rel
            _write_payload(root, expected_root)
            changed.extend(_changed_paths(expected_root, actual_root))
            changed.extend(_check_metadata(root, package_rel))
```

- [ ] **Step 6: Verify check now reports the expected stale artifacts (vendored copies not yet synced)**

Run: `py -3 -m cities2_mcp.plugin_packages check`

Expected: exit code 1, listing stale paths — the vendored `vendor/cities2_mcp/plugin_metadata.py` (missing) and the changed `vendor/cities2_mcp/plugin_packages.py` / `agent_assets.py` in both distro roots, and the two whitespace-normalized JSON files + the two READMEs. (This confirms the metadata + payload passes both detect drift; Task 5 fixes it.)

- [ ] **Step 7: Commit**

```sh
git add cities2_mcp/plugin_packages.py
git commit -m "Generate and check plugin metadata artifacts in sync/check (#33)"
```

---

## Task 5: First sync, full verification, commit regenerated artifacts

**Files:**
- Regenerated: the 10 metadata files + re-vendored `vendor/cities2_mcp/` trees (generated)
- Test: `tests/test_packaging.py` (add `test_repo_metadata_in_sync`)

- [ ] **Step 1: Run the first sync**

Run: `py -3 -m cities2_mcp.plugin_packages sync`

Expected: prints `updated <path>` lines for the re-vendored module copies, the two reformatted JSON files (`integrations/anthropic/claude-plugin/.claude-plugin/plugin.json`, `plugins/cities2-mcp/.codex-plugin/plugin.json`), and the two READMEs.

- [ ] **Step 2: Review the generated diff**

Run: `git status --short` then `git diff -- integrations/anthropic/claude-plugin/.claude-plugin/plugin.json plugins/cities2-mcp/.codex-plugin/plugin.json plugins/cities2-mcp/README.md integrations/anthropic/claude-plugin/README.md`

Expected: the two `plugin.json` diffs are pure whitespace (indentation) changes; the READMEs gain the generated marker and the Codex README reflows to single-line paragraphs. Confirm no value changed.

- [ ] **Step 3: Confirm check is clean**

Run: `py -3 -m cities2_mcp.plugin_packages check`

Expected: `Plugin package payloads are in sync.` (exit 0).

- [ ] **Step 4: Add the repo-in-sync test**

Add to `PackagingTests` in `tests/test_packaging.py`:

```python
    def test_repo_metadata_in_sync(self) -> None:
        from cities2_mcp import plugin_packages

        self.assertEqual(plugin_packages.check_packages(ROOT), ())
```

- [ ] **Step 5: Run the full test suite**

Run: `py -3 -m unittest discover -s tests -v`

Expected: PASS. The existing `test_anthropic_distribution_artifacts_are_version_aligned`, `test_codex_distribution_artifacts_are_version_aligned`, `test_codex_plugin_package_is_antigravity_plugin`, and the `node ... --version` launcher/serve tests must all still pass (they are the safety net proving the regenerated artifacts — especially the Antigravity bootstrap — are byte-correct).

- [ ] **Step 6: Commit**

```sh
git add integrations/anthropic/claude-plugin plugins/cities2-mcp .claude-plugin/marketplace.json .agents/plugins/marketplace.json tests/test_packaging.py
git commit -m "Regenerate plugin distribution artifacts from canonical sources (#33)"
```

---

## Task 6: Per-file drift test

**Files:**
- Test: `tests/test_packaging.py`

- [ ] **Step 1: Write the drift test**

Add to `PackagingTests` in `tests/test_packaging.py`:

```python
    def test_check_detects_and_sync_restores_each_metadata_file(self) -> None:
        from cities2_mcp import plugin_packages

        flattened = [
            rel
            for entries in plugin_packages.METADATA_FILES.values()
            for rel, _builder in entries
        ]
        self.assertEqual(len(flattened), 10)  # guards the spec's "10 metadata files"
        self.assertEqual(len(set(flattened)), 10)  # no duplicate registrations

        for package_rel, entries in plugin_packages.METADATA_FILES.items():
            for rel, _builder in entries:
                with self.subTest(metadata=str(rel)):
                    with tempfile.TemporaryDirectory(prefix="cities2-mcp-meta-drift-") as tmp:
                        root = Path(tmp)
                        self._write_plugin_sync_fixture(root)
                        plugin_packages.sync_packages(root, package_roots=(package_rel,))

                        target = root / rel
                        self.assertTrue(target.is_file())
                        target.write_text("DRIFT\n", encoding="utf-8")

                        stale = plugin_packages.check_packages(root, package_roots=(package_rel,))
                        self.assertIn(target, stale)

                        restored = plugin_packages.sync_packages(root, package_roots=(package_rel,))
                        self.assertIn(target, restored)
                        self.assertEqual(
                            plugin_packages.check_packages(root, package_roots=(package_rel,)), ()
                        )
```

- [ ] **Step 2: Run the drift test**

Run: `py -3 -m unittest tests.test_packaging.PackagingTests.test_check_detects_and_sync_restores_each_metadata_file -v`

Expected: PASS (one subtest per metadata file across both groups).

- [ ] **Step 3: Commit**

```sh
git add tests/test_packaging.py
git commit -m "Add per-file drift test for generated plugin metadata (#33)"
```

---

## Task 7: Contributor docs — canonical vs generated

**Files:**
- Modify: `CONTRIBUTING.md`

- [ ] **Step 1: Add the subsection**

In `CONTRIBUTING.md`, in the "Agent skills and plugin packages" section, after the existing paragraph that begins "The root `skills/` directory is the source of truth..." (around line 55), insert:

```markdown

### Canonical vs generated files

Canonical sources — edit these:

- `cities2_mcp/plugin_metadata.py` — shared plugin metadata and per-platform artifact templates (name, descriptions, URLs, keywords, user config, marketplace and interface structures, and the README text).
- `cities2_mcp/__init__.py` — the canonical `__version__`, propagated into every distribution artifact.
- root `skills/` — the five bundled agent skills.
- root `cities2_mcp/` — the Python package vendored into each distribution.

Generated — do not hand-edit; run `sync` and commit the result:

- Claude: `integrations/anthropic/claude-plugin/.claude-plugin/plugin.json`, `integrations/anthropic/claude-plugin/.mcp.json`, `integrations/anthropic/claude-plugin/README.md`, and root `.claude-plugin/marketplace.json`.
- Codex: `plugins/cities2-mcp/.codex-plugin/plugin.json`, `plugins/cities2-mcp/.mcp.json`, `plugins/cities2-mcp/README.md`, and root `.agents/plugins/marketplace.json`.
- Antigravity: `plugins/cities2-mcp/plugin.json` and `plugins/cities2-mcp/mcp_config.json`.
- Per-distribution payloads under each root: `skills/`, `vendor/`, `bin/cities2-mcp-launcher.js`, and `vendor/run_server.py`.

Regenerate and verify:

```sh
py -3 -m cities2_mcp.plugin_packages sync
py -3 -m cities2_mcp.plugin_packages check
```
```

- [ ] **Step 2: Commit**

```sh
git add CONTRIBUTING.md
git commit -m "Document canonical vs generated plugin files (#33)"
```

---

## Task 8: Final verification

- [ ] **Step 1: Full test gate**

Run: `py -3 -m unittest discover -s tests -v`

Expected: PASS (entire suite).

- [ ] **Step 2: Plugin package gate**

Run: `py -3 -m cities2_mcp.plugin_packages check`

Expected: `Plugin package payloads are in sync.` (exit 0).

- [ ] **Step 3: Confirm working tree is clean and review the branch diff**

Run: `git status --short` (expect empty) and `git log --oneline origin/main..HEAD`

Expected: a clean tree and the task commits listed. Hand-written net diff should be ~480 lines (generated/vendored excluded), under the 800 hard limit → single PR.

- [ ] **Step 4: Open the PR**

Use `superpowers:finishing-a-development-branch` to push and open the PR against `main`. PR body must follow the repo's `.github/pull_request_template.md` (check both verification boxes) and append the agent co-author line per `AGENTS.md`. Do not merge — the maintainer's test/review gate is pending.

---

## Acceptance criteria coverage

- *sync regenerates all intended payloads + metadata* → Task 4 (registry + `_sync_metadata`), Task 5 (first sync).
- *check fails on drift for Claude/Codex/Antigravity artifacts* → Task 4 (`_check_metadata`), Task 6 (per-file drift test).
- *Platform-specific config preserved verbatim* → Task 2 (`CLAUDE_USER_CONFIG`, `CODEX_INTERFACE`, `ANTIGRAVITY_BOOTSTRAP_JS`, per-platform builders); existing launcher/serve tests confirm.
- *Tests cover stale generated metadata* → Tasks 1, 5, 6.
- *Contributor docs state canonical vs generated* → Task 7.
