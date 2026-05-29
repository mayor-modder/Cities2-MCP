# Antigravity Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Antigravity as a third installable plugin distribution while reducing drift across Claude, Codex, and Antigravity packages.

**Architecture:** Keep root `skills/` and `cities2_mcp/` as canonical sources. Add `cities2_mcp.plugin_packages` with `sync` and `check` commands that own repeated package payloads: `skills/`, `bin/cities2-mcp-launcher.js`, `vendor/run_server.py`, and `vendor/cities2_mcp/`. Keep platform manifests and README files platform-native.

**Tech Stack:** Python 3.10+, stdlib `pathlib`, `shutil`, `filecmp`, `tempfile`, `argparse`, Node launcher already used by Claude/Codex plugin packages, `unittest`.

---

### Task 1: Fix Existing Skill Packaging Drift

**Files:**
- Modify: `cities2_mcp/agent_assets.py`
- Modify: `skills/cities2-mod-review/SKILL.md`
- Modify: `skills/cities2-mod-debugging/SKILL.md`
- Modify: `skills/cities2-mod-release/SKILL.md`
- Test: `tests/test_packaging.py`
- Test: `tests/test_portability.py`

- [ ] **Step 1: Confirm current RED tests**

Run: `python -m unittest tests.test_packaging.PackagingTests.test_agent_asset_installer_copies_codex_and_claude_assets tests.test_portability.PortabilityTests.test_agent_skills_are_packaged_and_documented -v`

Expected: FAIL because `install-agent-assets` installs only two skills and the new quality skills do not all say `Use automatically`.

- [ ] **Step 2: Make all shared skills installable**

Change `SKILL_NAMES` in `cities2_mcp/agent_assets.py` to:

```python
SKILL_NAMES = (
    "cities2-knowledge",
    "cities2-modding",
    "cities2-mod-review",
    "cities2-mod-debugging",
    "cities2-mod-release",
)
```

- [ ] **Step 3: Make quality skill descriptions satisfy trigger contract**

Ensure each quality skill frontmatter description begins with `Use automatically when ...`.

- [ ] **Step 4: Verify green**

Run: `python -m unittest tests.test_packaging.PackagingTests.test_agent_asset_installer_copies_codex_and_claude_assets tests.test_portability.PortabilityTests.test_agent_skills_are_packaged_and_documented -v`

Expected: PASS.

### Task 2: Add Package Sync/Check Helper

**Files:**
- Create: `cities2_mcp/plugin_packages.py`
- Test: `tests/test_packaging.py`

- [ ] **Step 1: Write failing sync/check tests**

Add tests that import `cities2_mcp.plugin_packages`, assert `check_packages(ROOT)` returns no drift for current packages after sync, and assert a temporary stale package reports changed paths.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_packaging.PackagingTests.test_plugin_package_check_detects_stale_payload -v`

Expected: FAIL because `cities2_mcp.plugin_packages` does not exist.

- [ ] **Step 3: Implement helper**

Create `cities2_mcp/plugin_packages.py` with:

```python
from __future__ import annotations

import argparse
import filecmp
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

SKILL_NAMES = (
    "cities2-knowledge",
    "cities2-modding",
    "cities2-mod-review",
    "cities2-mod-debugging",
    "cities2-mod-release",
)

PACKAGE_ROOTS = (
    Path("integrations/anthropic/claude-plugin"),
    Path("plugins/cities2-mcp"),
    Path("integrations/google/antigravity-plugin"),
)
```

Implement `sync_packages(repo_root: Path) -> tuple[Path, ...]`, `check_packages(repo_root: Path) -> tuple[Path, ...]`, and `main(argv: list[str] | None = None) -> int`. Copy canonical `skills/`, `cities2_mcp/`, and launcher content into each package. `check` must not mutate the working tree.

- [ ] **Step 4: Verify helper tests**

Run: `python -m unittest tests.test_packaging.PackagingTests.test_plugin_package_check_detects_stale_payload tests.test_packaging.PackagingTests.test_plugin_package_sync_updates_stale_payload -v`

Expected: PASS.

### Task 3: Add Antigravity Package

**Files:**
- Create: `integrations/google/README.md`
- Create: `integrations/google/antigravity-plugin/plugin.json`
- Create: `integrations/google/antigravity-plugin/mcp_config.json`
- Create: `integrations/google/antigravity-plugin/README.md`
- Generated: `integrations/google/antigravity-plugin/bin/cities2-mcp-launcher.js`
- Generated: `integrations/google/antigravity-plugin/skills/**`
- Generated: `integrations/google/antigravity-plugin/vendor/**`
- Test: `tests/test_packaging.py`

- [ ] **Step 1: Write failing Antigravity tests**

Add tests for manifest shape, launcher version output, MCP smoke behavior, and absence of Gemini CLI extension packaging.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_packaging.PackagingTests.test_antigravity_distribution_artifacts_are_version_aligned -v`

Expected: FAIL because `integrations/google/antigravity-plugin/plugin.json` does not exist.

- [ ] **Step 3: Add Antigravity manifests and docs**

Add `plugin.json`:

```json
{
  "name": "cities2-mcp"
}
```

Add `mcp_config.json`:

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

- [ ] **Step 4: Run sync**

Run: `python -m cities2_mcp.plugin_packages sync`

Expected: Antigravity package receives generated `bin/`, `skills/`, and `vendor/` payloads; Claude and Codex repeated payloads match canonical sources.

- [ ] **Step 5: Verify green**

Run: `python -m unittest tests.test_packaging.PackagingTests.test_antigravity_distribution_artifacts_are_version_aligned tests.test_packaging.PackagingTests.test_antigravity_plugin_vendored_launcher_reports_version tests.test_packaging.PackagingTests.test_antigravity_plugin_vendored_launcher_serves_mcp -v`

Expected: PASS.

### Task 4: Update Public Documentation

**Files:**
- Modify: `README.md`
- Modify: `INSTALL.md`
- Modify: `integrations/openai/README.md` only if needed by existing tests
- Test: `tests/test_portability.py`

- [ ] **Step 1: Write failing docs tests**

Add tests that root docs include Antigravity install paths and that public docs do not present Gemini CLI as a supported package.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_portability.PortabilityTests.test_docs_include_antigravity_plugin_path -v`

Expected: FAIL because Antigravity docs are not yet linked from root docs.

- [ ] **Step 3: Update docs**

Add Antigravity to the quick install matrix, add install instructions for workspace and global plugin paths, and describe `python -m cities2_mcp.plugin_packages sync` / `check` as maintainer-only package refresh commands.

- [ ] **Step 4: Verify docs tests**

Run: `python -m unittest tests.test_portability.PortabilityTests.test_docs_include_antigravity_plugin_path tests.test_portability.PortabilityTests.test_public_docs_do_not_advertise_gemini_cli_package -v`

Expected: PASS.

### Task 5: Full Verification

**Files:**
- No new files.

- [ ] **Step 1: Run package check**

Run: `python -m cities2_mcp.plugin_packages check`

Expected: PASS with no stale package payloads.

- [ ] **Step 2: Run full unit suite**

Run: `python -m unittest discover -s tests -v`

Expected: PASS.

- [ ] **Step 3: Run lint**

Run: `python -m ruff check .`

Expected: PASS.
