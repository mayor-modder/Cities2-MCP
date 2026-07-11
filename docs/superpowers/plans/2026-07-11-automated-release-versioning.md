# Automated Release Versioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every merged Cities2-MCP update an automatic semantic version, publish it, and deliver the matching generated plugin payload to the Mayor Modder marketplace without routine maintainer intervention.

**Architecture:** `cities2_mcp/_version.py` becomes the one canonical version source, while Hatch, the MCP server, `server.json`, plugin metadata, and tests consume or validate that value. A tested Python release-preparation CLI calculates patch/minor/major bumps from the current base branch; GitHub workflows use a narrowly scoped GitHub App token to update same-repository PR branches, tag validated merges, run the existing OIDC publication path, and open an auto-merge catalog PR.

**Tech Stack:** Python 3.10+, `unittest`, Hatchling, GitHub Actions, GitHub CLI, GitHub App installation tokens, PyPI trusted publishing, MCP Registry OIDC, Codex plugin marketplace packaging.

## Global Constraints

- The first release produced by this work is exactly `0.2.0`.
- An unlabeled pull request defaults to a patch bump; `release:minor` and `release:major` are mutually exclusive overrides.
- `cities2_mcp.__version__` is the public canonical version and is backed by `cities2_mcp/_version.py`.
- Python 3.10 remains the minimum supported runtime.
- Plugin metadata is generated from `cities2_mcp/plugin_metadata.py`; never hand-edit generated manifests.
- Catalog packages are exported through `python -m cities2_mcp.plugin_packages sync-catalog` and never written directly to marketplace `main`.
- Pull requests must be current with `main` before merge; the existing repository ruleset already enforces strict required status checks.
- A merged, fully validated Cities2-MCP pull request is the human release approval; no implementation session may manually merge, tag, or publish without explicit human direction.
- Do not commit, push, alter repository rules, create labels, or configure secrets during execution until the maintainer explicitly authorizes that exact external action.
- Preserve existing line endings and paragraph-per-line Markdown style.

---

### Task 1: Establish one canonical Python version

**Files:**
- Create: `cities2_mcp/_version.py`
- Modify: `cities2_mcp/__init__.py:1-6`
- Modify: `cities2_mcp/mcp_server.py:13-38`
- Modify: `pyproject.toml:5-8`
- Test: `tests/test_packaging.py:64-91`

**Interfaces:**
- Produces: `cities2_mcp._version.__version__: str`
- Produces: `cities2_mcp.__version__: str`, re-exported from `_version.py`
- Consumes: Hatchling's regex version source at `cities2_mcp/_version.py`

- [ ] **Step 1: Write failing canonical-version tests**

Add these assertions to `PluginPackagingTests` and replace the current literal package-version assertion:

```python
def test_pyproject_reads_version_from_canonical_module(self) -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    project = pyproject["project"]
    self.assertEqual(project["dynamic"], ["version"])
    self.assertNotIn("version", project)
    self.assertEqual(pyproject["tool"]["hatch"]["version"]["path"], "cities2_mcp/_version.py")

def test_runtime_uses_one_version_assignment(self) -> None:
    import cities2_mcp

    canonical = (ROOT / "cities2_mcp" / "_version.py").read_text(encoding="utf-8")
    package_init = (ROOT / "cities2_mcp" / "__init__.py").read_text(encoding="utf-8")
    server = (ROOT / "cities2_mcp" / "mcp_server.py").read_text(encoding="utf-8")

    self.assertIn(f'__version__ = "{cities2_mcp.__version__}"', canonical)
    self.assertNotIn("__version__ =", package_init)
    self.assertNotIn("__version__ =", server)
    self.assertEqual(mcp_server.__version__, cities2_mcp.__version__)
```

- [ ] **Step 2: Run the focused tests and verify red state**

Run:

```powershell
python -m unittest tests.test_packaging.PluginPackagingTests.test_pyproject_reads_version_from_canonical_module tests.test_packaging.PluginPackagingTests.test_runtime_uses_one_version_assignment -v
```

Expected: FAIL because `[project].version` is still static, `_version.py` does not exist, and `mcp_server.py` declares another version.

- [ ] **Step 3: Add the canonical module and dynamic Hatch configuration**

Create `cities2_mcp/_version.py`:

```python
__version__ = "0.1.9"
```

Change `cities2_mcp/__init__.py` to import the value:

```python
from __future__ import annotations

from pathlib import Path

from ._version import __version__

MCP_NAME = "io.github.mayor-modder/cities2-mcp"
```

In `cities2_mcp/mcp_server.py`, add this import with the other package imports and remove the local assignment:

```python
from . import __version__
```

Change the project metadata in `pyproject.toml`:

```toml
[project]
name = "cities2-mcp"
dynamic = ["version"]
```

Add the Hatch version source before the build target sections:

```toml
[tool.hatch.version]
path = "cities2_mcp/_version.py"
```

- [ ] **Step 4: Run the focused tests and verify green state**

Run:

```powershell
python -m unittest tests.test_packaging.PluginPackagingTests.test_pyproject_reads_version_from_canonical_module tests.test_packaging.PluginPackagingTests.test_runtime_uses_one_version_assignment tests.test_packaging.PluginPackagingTests.test_server_version_flag_prints_public_version -v
```

Expected: 3 tests pass and `python -m cities2_mcp.mcp_server --version` still reports `cities2-mcp 0.1.9`.

- [ ] **Step 5: Review and commit the canonical-version unit**

After explicit maintainer authorization to commit:

```powershell
git add pyproject.toml cities2_mcp/_version.py cities2_mcp/__init__.py cities2_mcp/mcp_server.py tests/test_packaging.py
git commit -m "Centralize the package version"
```

### Task 2: Generate all release metadata from the canonical version

**Files:**
- Modify: `cities2_mcp/plugin_metadata.py:1-290`
- Modify: `cities2_mcp/plugin_packages.py:39-89,211-276`
- Modify: `server.json`
- Modify: `tests/test_packaging.py:64-211,740-805,829`

**Interfaces:**
- Consumes: `cities2_mcp.__version__: str`
- Produces: `plugin_metadata.server_json() -> str`
- Produces: `plugin_packages.ROOT_METADATA_FILES: tuple[tuple[Path, Callable[[], str]], ...]`
- Preserves: `sync_packages(...) -> tuple[Path, ...]` and `check_packages(...) -> tuple[Path, ...]`

- [ ] **Step 1: Write failing root-metadata and dynamic-assertion tests**

At module scope in `tests/test_packaging.py`, import the canonical expected version:

```python
import cities2_mcp

PACKAGE_VERSION = cities2_mcp.__version__
```

Replace public-release literals such as `"0.1.9"`, `"cities2-mcp 0.1.9"`, and path component `"0.1.9"` with `PACKAGE_VERSION`, `f"cities2-mcp {PACKAGE_VERSION}"`, and `PACKAGE_VERSION`. Keep historical documentation fixtures unchanged and use an intentionally unrelated fixture version such as `9.8.7` where a test needs a standalone fake package.

Add these tests:

```python
def test_server_json_builder_uses_canonical_version(self) -> None:
    from cities2_mcp import plugin_metadata

    generated = json.loads(plugin_metadata.server_json())
    self.assertEqual(generated["version"], PACKAGE_VERSION)
    self.assertEqual(generated["packages"][0]["version"], PACKAGE_VERSION)

def test_repo_metadata_check_detects_stale_server_json(self) -> None:
    from cities2_mcp import plugin_packages

    with tempfile.TemporaryDirectory(prefix="cities2-mcp-root-metadata-") as tmp:
        root = Path(tmp)
        shutil.copytree(ROOT / "skills", root / "skills")
        shutil.copytree(ROOT / "cities2_mcp", root / "cities2_mcp")
        shutil.copytree(ROOT / "plugins", root / "plugins")
        (root / "server.json").write_text("{}\n", encoding="utf-8")

        stale = plugin_packages.check_packages(root)

        self.assertIn(root / "server.json", stale)
```

- [ ] **Step 2: Run the focused tests and verify red state**

Run:

```powershell
python -m unittest tests.test_packaging.PluginPackagingTests.test_server_json_builder_uses_canonical_version tests.test_packaging.PluginPackagingTests.test_repo_metadata_check_detects_stale_server_json -v
```

Expected: FAIL because `server_json()` and root metadata checking do not exist.

- [ ] **Step 3: Add the generated `server.json` builder**

In `cities2_mcp/plugin_metadata.py`, add:

```python
SERVER_ENVIRONMENT_VARIABLES = [
    {
        "name": "CITIES2_MODS_DIR",
        "description": "Optional path to the Cities: Skylines II Mods directory.",
        "isRequired": False,
        "format": "string",
        "isSecret": False,
    },
    {
        "name": "CITIES2_GAME_DIR",
        "description": "Optional path to the Cities: Skylines II install directory when auto-detection cannot find the game.",
        "isRequired": False,
        "format": "string",
        "isSecret": False,
    },
    {
        "name": "CITIES2_LOCALE_COK",
        "description": "Optional path to Locale.cok when the in-game encyclopedia file should be selected directly.",
        "isRequired": False,
        "format": "string",
        "isSecret": False,
    },
]


def server_json() -> str:
    return _dumps(
        {
            "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
            "name": "io.github.mayor-modder/cities2-mcp",
            "title": DISPLAY_NAME,
            "description": "Cities: Skylines II knowledge and modding tools for AI agents.",
            "repository": {"url": REPO_URL, "source": "github"},
            "version": VERSION,
            "packages": [
                {
                    "registryType": "pypi",
                    "identifier": "cities2-mcp",
                    "version": VERSION,
                    "transport": {"type": "stdio"},
                    "environmentVariables": SERVER_ENVIRONMENT_VARIABLES,
                }
            ],
        }
    )
```

- [ ] **Step 4: Include root metadata in package sync and check**

In `cities2_mcp/plugin_packages.py`, define:

```python
ROOT_METADATA_FILES: tuple[tuple[Path, Callable[[], str]], ...] = (
    (Path("server.json"), plugin_metadata.server_json),
)
```

Add focused helpers:

```python
def _sync_root_metadata(repo_root: Path) -> list[Path]:
    changed: list[Path] = []
    for rel, builder in ROOT_METADATA_FILES:
        target = repo_root / rel
        content = builder()
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current != content:
            target.write_text(content, encoding="utf-8")
            changed.append(target)
    return changed


def _check_root_metadata(repo_root: Path) -> list[Path]:
    stale: list[Path] = []
    for rel, builder in ROOT_METADATA_FILES:
        target = repo_root / rel
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current != builder():
            stale.append(target)
    return stale
```

Call `_sync_root_metadata(root)` once from `sync_packages` and `_check_root_metadata(root)` once from `check_packages`, outside the per-package loops.

- [ ] **Step 5: Regenerate and run focused tests**

Run:

```powershell
python -m cities2_mcp.plugin_packages sync
python -m unittest tests.test_packaging.PluginPackagingTests.test_server_json_builder_uses_canonical_version tests.test_packaging.PluginPackagingTests.test_repo_metadata_check_detects_stale_server_json tests.test_packaging.PluginPackagingTests.test_generated_metadata_is_valid_and_canonical -v
python -m cities2_mcp.plugin_packages check
```

Expected: focused tests pass and package check prints `Plugin package payloads are in sync.`

- [ ] **Step 6: Verify that release literals are no longer independently maintained**

Run:

```powershell
git grep -n "0\.1\.9" -- pyproject.toml server.json cities2_mcp tests/test_packaging.py plugins/cities2-mcp
```

Expected: only `cities2_mcp/_version.py` and explicitly isolated fixture/history cases contain the literal; no runtime, generated metadata, or ordinary assertion carries an independent public version.

- [ ] **Step 7: Review and commit generated metadata centralization**

After explicit maintainer authorization to commit:

```powershell
git add cities2_mcp/plugin_metadata.py cities2_mcp/plugin_packages.py server.json tests/test_packaging.py plugins/cities2-mcp
git commit -m "Generate release metadata from the package version"
```

### Task 3: Add tested semantic-version preparation logic

**Files:**
- Create: `cities2_mcp/release_version.py`
- Create: `tests/test_release_version.py`

**Interfaces:**
- Produces: `SemVer.parse(value: str) -> SemVer`
- Produces: `SemVer.bump(level: ReleaseLevel) -> SemVer`
- Produces: `select_release_level(labels: Iterable[str]) -> ReleaseLevel`
- Produces: `version_from_ref(repo_root: Path, ref: str) -> SemVer`
- Produces: `prepare_release(repo_root: Path, base_version: SemVer, labels: Iterable[str]) -> SemVer`
- Produces CLI: `python -m cities2_mcp.release_version prepare (--base-version X.Y.Z | --base-ref REF) [--label NAME ...]`

- [ ] **Step 1: Write failing semantic-version tests**

Create `tests/test_release_version.py`:

```python
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cities2_mcp.release_version import SemVer, prepare_release, select_release_level


class ReleaseVersionTests(unittest.TestCase):
    def test_parse_and_render_stable_semver(self) -> None:
        self.assertEqual(str(SemVer.parse("0.2.19")), "0.2.19")

    def test_bump_levels_reset_lower_components(self) -> None:
        version = SemVer.parse("1.7.9")
        self.assertEqual(str(version.bump("patch")), "1.7.10")
        self.assertEqual(str(version.bump("minor")), "1.8.0")
        self.assertEqual(str(version.bump("major")), "2.0.0")

    def test_labels_default_to_patch(self) -> None:
        self.assertEqual(select_release_level([]), "patch")
        self.assertEqual(select_release_level(["documentation"]), "patch")
        self.assertEqual(select_release_level(["release:minor"]), "minor")
        self.assertEqual(select_release_level(["release:major"]), "major")

    def test_conflicting_release_labels_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            select_release_level(["release:minor", "release:major"])

    def test_prepare_is_idempotent_for_the_same_base(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cities2-release-version-") as tmp:
            root = Path(tmp)
            version_file = root / "cities2_mcp" / "_version.py"
            version_file.parent.mkdir(parents=True)
            version_file.write_text('__version__ = "0.2.4"\n', encoding="utf-8")

            with mock.patch("cities2_mcp.release_version._sync_and_check") as sync:
                first = prepare_release(root, SemVer.parse("0.2.4"), [])
                second = prepare_release(root, SemVer.parse("0.2.4"), [])

            self.assertEqual(first, SemVer.parse("0.2.5"))
            self.assertEqual(second, first)
            self.assertEqual(version_file.read_text(encoding="utf-8"), '__version__ = "0.2.5"\n')
            self.assertEqual(sync.call_count, 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new test module and verify red state**

Run:

```powershell
python -m unittest tests.test_release_version -v
```

Expected: import failure because `cities2_mcp.release_version` does not exist.

- [ ] **Step 3: Implement the semantic-version module and CLI**

Create `cities2_mcp/release_version.py`:

```python
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Sequence

ReleaseLevel = Literal["patch", "minor", "major"]
VERSION_RE = re.compile(r'\A__version__ = "(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"\n?\Z')
RELEASE_LABELS: dict[str, ReleaseLevel] = {
    "release:minor": "minor",
    "release:major": "major",
}


@dataclass(frozen=True, order=True)
class SemVer:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> "SemVer":
        match = re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value.strip())
        if match is None:
            raise ValueError(f"Invalid stable semantic version: {value!r}")
        return cls(*(int(part) for part in match.groups()))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def bump(self, level: ReleaseLevel) -> "SemVer":
        if level == "patch":
            return SemVer(self.major, self.minor, self.patch + 1)
        if level == "minor":
            return SemVer(self.major, self.minor + 1, 0)
        if level == "major":
            return SemVer(self.major + 1, 0, 0)
        raise ValueError(f"Unsupported release level: {level}")


def select_release_level(labels: Iterable[str]) -> ReleaseLevel:
    selected = {RELEASE_LABELS[label] for label in labels if label in RELEASE_LABELS}
    if len(selected) > 1:
        raise ValueError("release:minor and release:major are mutually exclusive")
    return next(iter(selected), "patch")


def _version_from_text(text: str) -> SemVer:
    match = VERSION_RE.fullmatch(text)
    if match is None:
        raise ValueError("Canonical version file has an unexpected format")
    return SemVer(*(int(part) for part in match.groups()))


def version_from_ref(repo_root: Path, ref: str) -> SemVer:
    result = subprocess.run(
        ["git", "show", f"{ref}:cities2_mcp/_version.py"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )
    return _version_from_text(result.stdout)


def _sync_and_check(repo_root: Path) -> None:
    for command in (
        [sys.executable, "-m", "cities2_mcp.plugin_packages", "sync"],
        [sys.executable, "-m", "cities2_mcp.plugin_packages", "check"],
    ):
        result = subprocess.run(command, cwd=repo_root, text=True, capture_output=True)
        if result.returncode:
            detail = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
            raise RuntimeError(detail or f"Command failed: {' '.join(command)}")


def prepare_release(repo_root: Path, base_version: SemVer, labels: Iterable[str]) -> SemVer:
    target = base_version.bump(select_release_level(labels))
    version_file = repo_root / "cities2_mcp" / "_version.py"
    version_file.write_text(f'__version__ = "{target}"\n', encoding="utf-8", newline="\n")
    _sync_and_check(repo_root)
    return target


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m cities2_mcp.release_version")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    base = prepare.add_mutually_exclusive_group(required=True)
    base.add_argument("--base-version")
    base.add_argument("--base-ref")
    prepare.add_argument("--label", action="append", default=[])
    prepare.add_argument("--repo-root", type=Path, default=Path.cwd())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    base = SemVer.parse(args.base_version) if args.base_version else version_from_ref(repo_root, args.base_ref)
    target = prepare_release(repo_root, base, args.label)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run unit tests and verify green state**

Run:

```powershell
python -m unittest tests.test_release_version -v
```

Expected: all semantic-version tests pass.

- [ ] **Step 5: Add CLI and base-ref tests**

Extend `tests/test_release_version.py` with a temporary Git repository test that commits `_version.py`, then asserts `version_from_ref(root, "HEAD") == SemVer(0, 2, 4)`. Add a subprocess test for:

```powershell
python -m cities2_mcp.release_version --help
```

Expected: exit 0 and help text containing `prepare`, `--base-version`, `--base-ref`, and `--label`.

- [ ] **Step 6: Run release-version and packaging regression tests**

Run:

```powershell
python -m unittest tests.test_release_version tests.test_packaging -v
```

Expected: all tests pass.

- [ ] **Step 7: Review and commit the release-preparation unit**

After explicit maintainer authorization to commit:

```powershell
git add cities2_mcp/release_version.py tests/test_release_version.py
git commit -m "Add semantic release preparation"
```

### Task 4: Establish the `0.2.0` release payload

**Files:**
- Modify: `cities2_mcp/_version.py`
- Modify: `server.json`
- Modify: `plugins/cities2-mcp/**`
- Test: `tests/test_packaging.py`

**Interfaces:**
- Consumes: `release_version prepare --base-version 0.1.9 --label release:minor`
- Produces: canonical and generated version `0.2.0`
- Produces: bundled corpus manifest with 140 pages and 1,219 chunks in source and plugin payloads

- [ ] **Step 1: Add the explicit `0.2.0` release expectation**

Add a focused transition test in `tests/test_release_version.py`:

```python
def test_initial_minor_transition_is_0_2_0(self) -> None:
    base = SemVer.parse("0.1.9")
    self.assertEqual(base.bump(select_release_level(["release:minor"])), SemVer.parse("0.2.0"))
```

- [ ] **Step 2: Run the transition test**

Run:

```powershell
python -m unittest tests.test_release_version.ReleaseVersionTests.test_initial_minor_transition_is_0_2_0 -v
```

Expected: PASS because the tested bump logic already supports the intended transition.

- [ ] **Step 3: Prepare the actual release payload**

Run:

```powershell
python -m cities2_mcp.release_version prepare --base-version 0.1.9 --label release:minor
```

Expected: final stdout line `0.2.0`; `_version.py`, `server.json`, and generated plugin payloads all report `0.2.0`.

- [ ] **Step 4: Verify version and corpus alignment**

Run:

```powershell
python -c "import json, pathlib, cities2_mcp; roots=[pathlib.Path('cities2_mcp/data'), pathlib.Path('plugins/cities2-mcp/vendor/cities2_mcp/data')]; assert cities2_mcp.__version__ == '0.2.0'; [(lambda m: (m['page_count'] == 140 and m['chunk_count'] == 1219) or (_ for _ in ()).throw(AssertionError(m)))(json.loads((root/'manifest.json').read_text(encoding='utf-8'))) for root in roots]; print(cities2_mcp.__version__, 'corpus ok')"
python -m cities2_mcp.plugin_packages check
```

Expected: `0.2.0 corpus ok` and `Plugin package payloads are in sync.`

- [ ] **Step 5: Run the complete repository gate and build distributions**

Run:

```powershell
python -m unittest discover -s tests -v
python -m pip install build
python -m build
```

Expected: all tests pass and `dist/` contains `cities2_mcp-0.2.0-py3-none-any.whl` plus `cities2_mcp-0.2.0.tar.gz`.

- [ ] **Step 6: Inspect built artifacts**

Run:

```powershell
python -c "import json, zipfile; from pathlib import Path; wheel=next(Path('dist').glob('cities2_mcp-0.2.0-*.whl')); z=zipfile.ZipFile(wheel); names=set(z.namelist()); assert 'cities2_mcp/_version.py' in names; manifest=json.loads(z.read('cities2_mcp/data/manifest.json')); assert (manifest['page_count'], manifest['chunk_count']) == (140, 1219); assert any(name.endswith('cities2-knowledge/SKILL.md') for name in names); print(wheel.name, manifest['page_count'], manifest['chunk_count'])"
```

Expected: the wheel name followed by `140 1219`.

- [ ] **Step 7: Review and commit the `0.2.0` payload**

After explicit maintainer authorization to commit:

```powershell
git add cities2_mcp/_version.py server.json plugins/cities2-mcp tests/test_release_version.py
git commit -m "Prepare Cities2-MCP 0.2.0"
```

### Task 5: Automate version preparation on pull requests

**Files:**
- Create: `.github/workflows/prepare-release-version.yml`
- Create: `tests/test_release_workflows.py`
- Modify: `docs/maintainers/release-automation.md` (created in Task 8)

**Interfaces:**
- Consumes: GitHub PR labels and base ref through `GITHUB_EVENT_PATH` and `GITHUB_BASE_REF`
- Consumes variable: `RELEASE_APP_CLIENT_ID`
- Consumes secret: `RELEASE_APP_PRIVATE_KEY`
- Produces: app-authored `Prepare release vX.Y.Z` commit on a same-repository PR branch
- Produces check names: `prepare` and `unsupported-fork`

- [ ] **Step 1: Write failing workflow contract tests**

Create `tests/test_release_workflows.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseWorkflowTests(unittest.TestCase):
    def test_pr_workflow_uses_labels_base_ref_and_app_token(self) -> None:
        text = (ROOT / ".github" / "workflows" / "prepare-release-version.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request:", text)
        self.assertIn("release:minor", text)
        self.assertIn("release:major", text)
        self.assertIn("GITHUB_BASE_REF", text)
        self.assertIn("actions/create-github-app-token@v3", text)
        self.assertIn("RELEASE_APP_CLIENT_ID", text)
        self.assertIn("RELEASE_APP_PRIVATE_KEY", text)
        self.assertIn("cities2_mcp.release_version prepare", text)
        self.assertIn("git push", text)
        self.assertIn("unsupported-fork", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the workflow contract test and verify red state**

Run:

```powershell
python -m unittest tests.test_release_workflows.ReleaseWorkflowTests.test_pr_workflow_uses_labels_base_ref_and_app_token -v
```

Expected: ERROR because the workflow file does not exist.

- [ ] **Step 3: Create the PR preparation workflow**

Create `.github/workflows/prepare-release-version.yml`:

```yaml
name: Prepare release version

on:
  pull_request:
    types: [opened, synchronize, reopened, labeled, unlabeled]

permissions:
  contents: read

concurrency:
  group: prepare-release-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  prepare:
    if: github.event.pull_request.head.repo.full_name == github.repository
    runs-on: ubuntu-latest
    steps:
      - name: Create release automation token
        id: app-token
        uses: actions/create-github-app-token@v3
        with:
          client-id: ${{ vars.RELEASE_APP_CLIENT_ID }}
          private-key: ${{ secrets.RELEASE_APP_PRIVATE_KEY }}

      - name: Checkout pull request branch
        uses: actions/checkout@v5
        with:
          ref: ${{ github.event.pull_request.head.ref }}
          token: ${{ steps.app-token.outputs.token }}
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.14"

      - name: Prepare semantic version
        id: version
        shell: bash
        run: |
          git fetch origin "$GITHUB_BASE_REF"
          mapfile -t labels < <(jq -r '.pull_request.labels[].name' "$GITHUB_EVENT_PATH")
          args=()
          for label in "${labels[@]}"; do
            args+=(--label "$label")
          done
          version=$(python -m cities2_mcp.release_version prepare --base-ref "origin/$GITHUB_BASE_REF" "${args[@]}")
          echo "version=$version" >> "$GITHUB_OUTPUT"

      - name: Commit generated release metadata
        shell: bash
        run: |
          if git diff --quiet; then
            exit 0
          fi
          git config user.name "cities2-release[bot]"
          git config user.email "cities2-release[bot]@users.noreply.github.com"
          git add -A
          git commit -m "Prepare release v${{ steps.version.outputs.version }}"
          git push origin "HEAD:$GITHUB_HEAD_REF"

  unsupported-fork:
    if: github.event.pull_request.head.repo.full_name != github.repository
    runs-on: ubuntu-latest
    steps:
      - name: Explain fork limitation
        run: |
          echo "Automated release preparation requires a maintainer-owned branch."
          exit 1
```

- [ ] **Step 4: Run workflow contract and complete local regression tests**

Run:

```powershell
python -m unittest tests.test_release_workflows tests.test_release_version -v
python -m unittest discover -s tests -v
```

Expected: workflow contract and full suite pass.

- [ ] **Step 5: Validate the workflow syntax through GitHub's Actions analyzer**

After pushing a branch with explicit maintainer authorization, confirm the repository's existing required `Analyze (actions)` check passes for `.github/workflows/prepare-release-version.yml`.

- [ ] **Step 6: Review and commit the PR automation**

After explicit maintainer authorization to commit:

```powershell
git add .github/workflows/prepare-release-version.yml tests/test_release_workflows.py
git commit -m "Automate pull request version preparation"
```

### Task 6: Finalize validated merges with an idempotent tag

**Files:**
- Modify: `cities2_mcp/release_version.py`
- Modify: `tests/test_release_version.py`
- Create: `.github/workflows/finalize-release.yml`
- Modify: `tests/test_release_workflows.py`

**Interfaces:**
- Produces: `tag_action(version: SemVer, commit_sha: str, existing_sha: str | None) -> Literal["create", "exists"]`
- Consumes: `GITHUB_SHA` and canonical `cities2_mcp.__version__`
- Produces: `vX.Y.Z` tag through the GitHub App token

- [ ] **Step 1: Write failing tag-state tests**

Add to `tests/test_release_version.py`:

```python
def test_tag_action_is_idempotent_at_the_same_commit(self) -> None:
    from cities2_mcp.release_version import tag_action

    version = SemVer.parse("0.2.0")
    self.assertEqual(tag_action(version, "abc123", None), "create")
    self.assertEqual(tag_action(version, "abc123", "abc123"), "exists")
    with self.assertRaisesRegex(ValueError, "different commit"):
        tag_action(version, "abc123", "def456")
```

Add to `tests/test_release_workflows.py`:

```python
def test_finalize_workflow_validates_before_app_tag_push(self) -> None:
    text = (ROOT / ".github" / "workflows" / "finalize-release.yml").read_text(encoding="utf-8")
    self.assertIn('branches: ["main"]', text)
    self.assertIn("python -m unittest discover -s tests -v", text)
    self.assertIn("python -m cities2_mcp.plugin_packages check", text)
    self.assertIn("actions/create-github-app-token@v3", text)
    self.assertIn('tag="v$version"', text)
    self.assertIn("release_version tag-state", text)
    self.assertIn("https://pypi.org/pypi/cities2-mcp/$version/json", text)
    self.assertIn("git push origin", text)
```

- [ ] **Step 2: Run focused tests and verify red state**

Run:

```powershell
python -m unittest tests.test_release_version.ReleaseVersionTests.test_tag_action_is_idempotent_at_the_same_commit tests.test_release_workflows.ReleaseWorkflowTests.test_finalize_workflow_validates_before_app_tag_push -v
```

Expected: FAIL because `tag_action` and the workflow do not exist.

- [ ] **Step 3: Implement tag-state validation**

Add to `cities2_mcp/release_version.py`:

```python
TagAction = Literal["create", "exists"]


def tag_action(version: SemVer, commit_sha: str, existing_sha: str | None) -> TagAction:
    if not commit_sha:
        raise ValueError("Current commit SHA is required")
    if existing_sha is None:
        return "create"
    if existing_sha == commit_sha:
        return "exists"
    raise ValueError(f"Tag v{version} already points at a different commit: {existing_sha}")
```

Extend `_parser()` with:

```python
    tag_state = subparsers.add_parser("tag-state")
    tag_state.add_argument("--version", required=True)
    tag_state.add_argument("--commit-sha", required=True)
    tag_state.add_argument("--existing-sha", default="")
```

Handle the new command before the existing `prepare` branch in `main()`:

```python
    if args.command == "tag-state":
        action = tag_action(
            SemVer.parse(args.version),
            args.commit_sha,
            args.existing_sha or None,
        )
        print(action)
        return 0
```

- [ ] **Step 4: Create the merge finalization workflow**

Create `.github/workflows/finalize-release.yml`:

```yaml
name: Finalize release

on:
  push:
    branches: ["main"]

permissions:
  contents: read

concurrency:
  group: finalize-release
  cancel-in-progress: false

jobs:
  tag:
    runs-on: ubuntu-latest
    steps:
      - name: Create release automation token
        id: app-token
        uses: actions/create-github-app-token@v3
        with:
          client-id: ${{ vars.RELEASE_APP_CLIENT_ID }}
          private-key: ${{ secrets.RELEASE_APP_PRIVATE_KEY }}

      - name: Checkout merged release
        uses: actions/checkout@v5
        with:
          token: ${{ steps.app-token.outputs.token }}
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.14"

      - name: Verify repository state
        run: |
          python -m unittest discover -s tests -v
          python -m cities2_mcp.plugin_packages check

      - name: Create release tag
        shell: bash
        run: |
          version=$(python -c 'import cities2_mcp; print(cities2_mcp.__version__)')
          tag="v$version"
          git fetch --tags origin
          existing=""
          if git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
            existing=$(git rev-list -n 1 "$tag")
          fi
          action=$(python -m cities2_mcp.release_version tag-state --version "$version" --commit-sha "$GITHUB_SHA" --existing-sha "$existing")
          if [[ "$action" == "exists" ]]; then
            exit 0
          fi
          pypi_status=$(curl --retry 3 --silent --show-error --output /dev/null --write-out '%{http_code}' "https://pypi.org/pypi/cities2-mcp/$version/json")
          case "$pypi_status" in
            200)
              echo "cities2-mcp $version already exists on PyPI without a matching tag at this commit" >&2
              exit 1
              ;;
            404)
              ;;
            *)
              echo "Unable to verify cities2-mcp $version on PyPI (HTTP $pypi_status)" >&2
              exit 1
              ;;
          esac
          git config user.name "cities2-release[bot]"
          git config user.email "cities2-release[bot]@users.noreply.github.com"
          git tag -a "$tag" -m "Release $tag" "$GITHUB_SHA"
          git push origin "$tag"
```

- [ ] **Step 5: Run focused and full regression tests**

Run:

```powershell
python -m unittest tests.test_release_version tests.test_release_workflows -v
python -m unittest discover -s tests -v
python -m cities2_mcp.plugin_packages check
```

Expected: all tests pass and plugin payloads remain synchronized.

- [ ] **Step 6: Review and commit merge finalization**

After explicit maintainer authorization to commit:

```powershell
git add cities2_mcp/release_version.py tests/test_release_version.py .github/workflows/finalize-release.yml tests/test_release_workflows.py
git commit -m "Finalize merged releases automatically"
```

### Task 7: Deliver published releases to the plugin marketplace

**Files:**
- Modify: `.github/workflows/release.yml:1-68`
- Modify: `tests/test_release_workflows.py`

**Interfaces:**
- Consumes: successful `publish` job and tag `vX.Y.Z`
- Consumes variable: `RELEASE_APP_CLIENT_ID`
- Consumes secret: `RELEASE_APP_PRIVATE_KEY`
- Consumes: `plugin_packages sync-catalog`
- Produces branch: `automation/cities2-mcp-X.Y.Z` in `mayor-modder/Mayor-Modder-Cities2-Plugins`
- Produces: one squash-auto-merge catalog PR with a release-automation co-author footer

- [ ] **Step 1: Write the failing catalog-delivery workflow test**

Add to `tests/test_release_workflows.py`:

```python
def test_release_workflow_syncs_catalog_after_publish(self) -> None:
    text = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    self.assertIn("catalog:", text)
    self.assertIn("needs: publish", text)
    self.assertIn("mayor-modder/Mayor-Modder-Cities2-Plugins", text)
    self.assertIn("cities2_mcp.plugin_packages sync-catalog", text)
    self.assertIn("automation/cities2-mcp-", text)
    self.assertIn("git merge --no-edit origin/main", text)
    self.assertIn("gh pr create", text)
    self.assertIn("gh pr merge --auto --squash", text)
    self.assertIn("*Co-authored by Cities2-MCP release automation.*", text)
```

- [ ] **Step 2: Run the catalog workflow test and verify red state**

Run:

```powershell
python -m unittest tests.test_release_workflows.ReleaseWorkflowTests.test_release_workflow_syncs_catalog_after_publish -v
```

Expected: FAIL because `release.yml` has no catalog job.

- [ ] **Step 3: Add the catalog job to `release.yml`**

Append this job after `publish`:

```yaml
  catalog:
    needs: publish
    runs-on: ubuntu-latest
    steps:
      - name: Create cross-repository token
        id: app-token
        uses: actions/create-github-app-token@v3
        with:
          client-id: ${{ vars.RELEASE_APP_CLIENT_ID }}
          private-key: ${{ secrets.RELEASE_APP_PRIVATE_KEY }}
          owner: mayor-modder
          repositories: |
            Cities2-MCP
            Mayor-Modder-Cities2-Plugins

      - name: Checkout Cities2-MCP release
        uses: actions/checkout@v5
        with:
          path: source
          ref: ${{ github.ref }}

      - name: Checkout marketplace
        uses: actions/checkout@v5
        with:
          repository: mayor-modder/Mayor-Modder-Cities2-Plugins
          path: catalog
          token: ${{ steps.app-token.outputs.token }}
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.14"

      - name: Prepare catalog branch
        id: branch
        shell: bash
        working-directory: catalog
        run: |
          version="${GITHUB_REF_NAME#v}"
          branch="automation/cities2-mcp-$version"
          git fetch origin main
          if git ls-remote --exit-code --heads origin "$branch" >/dev/null 2>&1; then
            git fetch origin "$branch"
            git checkout -B "$branch" "origin/$branch"
            git merge --no-edit origin/main
          else
            git checkout -b "$branch"
          fi
          echo "name=$branch" >> "$GITHUB_OUTPUT"

      - name: Generate marketplace payload
        working-directory: source
        run: python -m cities2_mcp.plugin_packages sync-catalog --catalog-root ../catalog

      - name: Commit and push marketplace update
        shell: bash
        working-directory: catalog
        run: |
          git config user.name "cities2-release[bot]"
          git config user.email "cities2-release[bot]@users.noreply.github.com"
          git add -A
          if ! git diff --cached --quiet; then
            git commit -m "Update Cities2-MCP to ${GITHUB_REF_NAME#v}"
            git push -u origin "${{ steps.branch.outputs.name }}"
          fi

      - name: Open or update catalog pull request
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
        shell: bash
        working-directory: catalog
        run: |
          branch="${{ steps.branch.outputs.name }}"
          version="${GITHUB_REF_NAME#v}"
          pr=$(gh pr list --head "$branch" --state open --json url --jq '.[0].url')
          if [[ -z "$pr" ]]; then
            if git diff --quiet origin/main...HEAD; then
              exit 0
            fi
            printf '%s\n' \
              '## Summary' \
              '' \
              "Update the generated Cities2-MCP plugin packages and marketplace metadata to $version." \
              '' \
              '## Validation' \
              '' \
              '- source release publication completed' \
              '- catalog payload generated by `cities2_mcp.plugin_packages sync-catalog`' \
              '' \
              '*Co-authored by Cities2-MCP release automation.*' \
              > "$RUNNER_TEMP/catalog-pr.md"
            pr=$(gh pr create --base main --head "$branch" --title "Update Cities2-MCP to $version" --body-file "$RUNNER_TEMP/catalog-pr.md")
          fi
          gh pr merge --auto --squash "$pr"
```

- [ ] **Step 4: Add a generated-catalog consistency check before commit**

Immediately after `Generate marketplace payload`, add this workflow step:

```yaml
      - name: Verify generated marketplace release
        shell: bash
        run: |
          python - <<'PY'
          import json
          from pathlib import Path
          import sys

          sys.path.insert(0, "source")
          import cities2_mcp

          plugin = json.loads(Path("catalog/plugins/cities2-mcp/.codex-plugin/plugin.json").read_text(encoding="utf-8"))
          manifest = json.loads(Path("catalog/plugins/cities2-mcp/vendor/cities2_mcp/data/manifest.json").read_text(encoding="utf-8"))
          source_manifest = json.loads(Path("source/cities2_mcp/data/manifest.json").read_text(encoding="utf-8"))
          assert plugin["version"] == cities2_mcp.__version__
          assert manifest == source_manifest
          PY
```

- [ ] **Step 5: Run workflow and repository tests**

Run:

```powershell
python -m unittest tests.test_release_workflows -v
python -m unittest discover -s tests -v
python -m cities2_mcp.plugin_packages check
```

Expected: all tests pass.

- [ ] **Step 6: Review and commit catalog delivery**

After explicit maintainer authorization to commit:

```powershell
git add .github/workflows/release.yml tests/test_release_workflows.py
git commit -m "Deliver releases to the plugin marketplace"
```

### Task 8: Document and configure the one-time GitHub automation

**Files:**
- Create: `docs/maintainers/release-automation.md`
- Modify: `tests/test_release_workflows.py`
- External state: GitHub App installation, repository variable/secret, labels, required check, marketplace auto-merge setting

**Interfaces:**
- Produces labels: `release:minor`, `release:major`
- Produces variable: `RELEASE_APP_CLIENT_ID`
- Produces secret: `RELEASE_APP_PRIVATE_KEY`
- Produces required check: `Prepare release version / prepare`
- Produces marketplace setting: `allow_auto_merge: true`

- [ ] **Step 1: Write a failing maintainer-documentation test**

Add to `tests/test_release_workflows.py`:

```python
def test_maintainer_docs_cover_one_time_release_setup(self) -> None:
    text = (ROOT / "docs" / "maintainers" / "release-automation.md").read_text(encoding="utf-8")
    for required in (
        "release:minor",
        "release:major",
        "RELEASE_APP_CLIENT_ID",
        "RELEASE_APP_PRIVATE_KEY",
        "Cities2-MCP",
        "Mayor-Modder-Cities2-Plugins",
        "Prepare release version / prepare",
        "allow_auto_merge",
        "contents: write",
        "pull requests: write",
    ):
        self.assertIn(required, text)
```

- [ ] **Step 2: Run the documentation test and verify red state**

Run:

```powershell
python -m unittest tests.test_release_workflows.ReleaseWorkflowTests.test_maintainer_docs_cover_one_time_release_setup -v
```

Expected: ERROR because the maintainer document does not exist.

- [ ] **Step 3: Write the one-time setup guide**

Create `docs/maintainers/release-automation.md` with these exact requirements:

```markdown
# Release automation

Cities2-MCP defaults every same-repository pull request to a patch release. Apply `release:minor` or `release:major` before merge only when that larger semantic bump is intentional; the labels are mutually exclusive.

## GitHub App

Install one private GitHub App on `mayor-modder/Cities2-MCP` and `mayor-modder/Mayor-Modder-Cities2-Plugins`. Grant repository `contents: write`, `pull requests: write`, and metadata read access. Do not grant organization administration or unrelated repository access.

Store its client ID as a Cities2-MCP Actions variable named `RELEASE_APP_CLIENT_ID`. Store its private key as an Actions secret named `RELEASE_APP_PRIVATE_KEY`.

## Labels and branch rule

Create `release:minor` and `release:major` in Cities2-MCP. Add `Prepare release version / prepare` to the required status checks for `main`, retaining strict up-to-date branch enforcement and the existing test and CodeQL checks.

Enable repository auto-merge in `mayor-modder/Mayor-Modder-Cities2-Plugins` (`allow_auto_merge: true`) so the validated generated catalog pull request can complete without a second maintainer action.

## Release path

The PR workflow writes the generated version commit. After a validated merge, finalization creates `vX.Y.Z`; the existing release workflow publishes PyPI, MCP Registry, and GitHub Release artifacts, then opens and auto-merges a generated marketplace pull request.

If source publication succeeds but catalog delivery fails, treat the marketplace as incomplete and rerun the failed catalog job after correcting the named authentication or validation error.
```

- [ ] **Step 4: Run documentation and full tests**

Run:

```powershell
python -m unittest tests.test_release_workflows -v
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 5: Configure GitHub labels after explicit external-write approval**

Run only after the maintainer explicitly authorizes repository metadata changes:

```powershell
gh label create "release:minor" --repo mayor-modder/Cities2-MCP --color "1D76DB" --description "Release automation increments the minor version" --force
gh label create "release:major" --repo mayor-modder/Cities2-MCP --color "B60205" --description "Release automation increments the major version" --force
```

Expected: both labels exist and `gh label list --repo mayor-modder/Cities2-MCP --search "release:"` shows them.

- [ ] **Step 6: Pause for maintainer-owned GitHub App secret setup**

The maintainer creates/installs the private GitHub App, adds `RELEASE_APP_CLIENT_ID` as a repository variable, and adds `RELEASE_APP_PRIVATE_KEY` as a repository secret. Do not request, print, copy, or store the private key in the repository or task transcript.

- [ ] **Step 7: Add the required PR preparation check after its first successful run**

After explicit approval to modify repository rules, update ruleset `17004760` so `Prepare release version / prepare` joins the existing required checks while preserving strict status checks, pull-request-only changes, deletion protection, and non-fast-forward protection. Fetch the ruleset before and after the update and compare every unrelated field.

- [ ] **Step 8: Enable marketplace auto-merge after explicit repository-setting approval**

Run only after the maintainer explicitly authorizes the marketplace setting change:

```powershell
gh api --method PATCH repos/mayor-modder/Mayor-Modder-Cities2-Plugins -F allow_auto_merge=true
gh api repos/mayor-modder/Mayor-Modder-Cities2-Plugins --jq '.allow_auto_merge'
```

Expected: the second command prints `true`.

- [ ] **Step 9: Review and commit maintainer documentation**

After explicit maintainer authorization to commit:

```powershell
git add docs/maintainers/release-automation.md tests/test_release_workflows.py
git commit -m "Document release automation setup"
```

### Task 9: Run end-to-end package, catalog, and Codex smoke validation

**Files:**
- Create after observed testing: `evals/reports/2026-07-11-cities2-mcp-0.2.0-release-smoke.md`
- Verify: built distributions under ignored `dist/`
- Verify: temporary generated catalog checkout outside the repository
- Verify: installed Codex plugin cache for `0.2.0`

**Interfaces:**
- Consumes: all implementation tasks and documented one-time GitHub configuration
- Produces: reproducible evidence for source package, marketplace payload, MCP startup, and all five skills
- Does not produce: a tag, merge, PyPI upload, MCP Registry publication, or marketplace merge during pre-merge validation

- [ ] **Step 1: Run mandatory repository gates from a clean worktree**

Run:

```powershell
git status --short --branch
python -m unittest discover -s tests -v
python -m cities2_mcp.plugin_packages check
python -m build
```

Expected: clean tracked state before generated `dist/`, all tests pass, plugin payloads are synchronized, and both `0.2.0` distributions build.

- [ ] **Step 2: Generate the marketplace payload in a disposable checkout**

Run:

```powershell
$catalog = Join-Path $env:TEMP 'cities2-mcp-0.2.0-catalog-smoke'
git clone https://github.com/mayor-modder/Mayor-Modder-Cities2-Plugins.git $catalog
python -m cities2_mcp.plugin_packages sync-catalog --catalog-root $catalog
```

Expected: only Cities2-MCP catalog package files and the two marketplace entries change; Cities2 Chief of Staff files and entries remain intact.

- [ ] **Step 3: Verify generated catalog identity and corpus**

Run:

```powershell
python -c "import json, pathlib, sys; root=pathlib.Path(sys.argv[1]); plugin=json.loads((root/'plugins/cities2-mcp/.codex-plugin/plugin.json').read_text(encoding='utf-8')); manifest=json.loads((root/'plugins/cities2-mcp/vendor/cities2_mcp/data/manifest.json').read_text(encoding='utf-8')); assert plugin['version']=='0.2.0'; assert (manifest['page_count'],manifest['chunk_count'])==(140,1219); print(plugin['version'],manifest['page_count'],manifest['chunk_count'])" $catalog
```

Expected: `0.2.0 140 1219`.

- [ ] **Step 4: Add or upgrade the disposable marketplace in Codex**

After explicit maintainer approval to make a temporary local Codex marketplace change, replace the configured marketplace with the disposable checkout:

```powershell
codex plugin marketplace remove mayor-modder-cities2-plugins
codex plugin marketplace add $catalog
```

Use the Codex app's plugin view to install or upgrade `cities2-mcp`, then start a fresh task so the MCP server launches from the new cache. Do not delete or overwrite the existing `0.1.9` cache by hand.

- [ ] **Step 5: Verify installed source status and the refreshed corpus**

In the fresh Codex task, invoke `cities2-mcp:cities2-knowledge`, call `source_status()`, search compact terms `patch 1.6 X patch notes fixes changes`, and fetch `cities2-docs:patch-1-6-x`.

Expected: the configured wiki paths contain `cities2-mcp\0.2.0\vendor\cities2_mcp\data`, exact page retrieval succeeds, and results no longer fall back solely to `Patch 1.5.X`.

- [ ] **Step 6: Exercise all five installed skills**

Use the prompts and evidence expectations in `evals/reports/2026-05-31-codex-plugin-skill-evaluation.md`:

```text
$cities2-mcp:cities2-knowledge How do subway lines work best in Cities: Skylines II?
$cities2-mcp:cities2-modding Scaffold a small Cities: Skylines II UI mod in this project folder, then build it.
$cities2-mcp:cities2-mod-review Review this generated project for maintainability, user value, packaging hygiene, and readiness gaps.
$cities2-mcp:cities2-mod-debugging The UI does not appear in game. Diagnose what evidence is needed before changing code.
$cities2-mcp:cities2-mod-release Is this generated project ready for public release if it has not been packaged and playtested in game?
```

Expected: MCP starts; knowledge uses local sources; modding uses workflow tools or the documented Codex fallback; review grounds findings in files; debugging asks for runtime evidence before edits; release keeps readiness blocked without package/playtest evidence.

- [ ] **Step 7: Restore the normal GitHub marketplace source**

After the smoke task has captured its evidence, run:

```powershell
codex plugin marketplace remove mayor-modder-cities2-plugins
codex plugin marketplace add mayor-modder/Mayor-Modder-Cities2-Plugins
```

Expected: the configured marketplace again tracks the public GitHub repository. Leave the `0.2.0` cache intact as smoke evidence; do not claim the public marketplace serves `0.2.0` until its generated PR merges.

- [ ] **Step 8: Record observed smoke evidence**

Create `evals/reports/2026-07-11-cities2-mcp-0.2.0-release-smoke.md` only after the runs. Record client/version, source paths, exact commands or prompts, pass/fail results, corpus page proof, limitations, and whether any step remains pending. Do not claim publication, merge, or release completion during this pre-merge smoke.

- [ ] **Step 9: Run final diff and line-ending checks**

Run:

```powershell
git diff --check
git status --short --branch
git ls-files --eol -- pyproject.toml server.json cities2_mcp plugins/cities2-mcp .github/workflows tests docs evals/reports
```

Expected: no whitespace errors; all touched files preserve indexed line endings; only intended source, generated package, workflow, test, design, plan, documentation, and observed smoke-report files are changed.

- [ ] **Step 10: Commit the observed smoke report and any final verification-only edits**

After explicit maintainer authorization to commit:

```powershell
git add evals/reports/2026-07-11-cities2-mcp-0.2.0-release-smoke.md
git commit -m "Record Cities2-MCP 0.2.0 release smoke"
```

### Task 10: Prepare the reviewed pull request without releasing

**Files:**
- Review all files changed by Tasks 1-9
- External state: branch, draft PR, labels, checks

**Interfaces:**
- Produces: draft PR targeting `main`
- Applies: `release:minor`
- Preserves: no merge/tag/publication until explicit human direction and all documented gates pass

- [ ] **Step 1: Re-run final verification immediately before publication of the branch**

Run:

```powershell
python -m unittest discover -s tests -v
python -m cities2_mcp.plugin_packages check
python -m build
git diff --check
git status --short --branch
```

Expected: all commands pass and branch state contains only the intended implementation commits.

- [ ] **Step 2: Push only after explicit maintainer authorization**

Run:

```powershell
git push -u origin codex/automated-release-versioning
```

- [ ] **Step 3: Open a draft PR with release scope and validation evidence**

The PR body must summarize canonical versioning, PR label behavior, automatic tag/publication flow, marketplace delivery, one-time GitHub App setup, tests, client smoke evidence, and the pending human merge gate. End with:

```markdown
*Co-authored by Codex.*
```

- [ ] **Step 4: Apply the initial minor label**

Run after the label exists:

```powershell
gh pr edit --add-label "release:minor"
```

Expected: the preparation workflow computes `0.2.0` idempotently and does not create a second version diff.

- [ ] **Step 5: Hold the release gate**

Do not merge the PR, create `v0.2.0`, publish PyPI/MCP artifacts, or merge the catalog PR. Report required-check state and wait for explicit human direction to merge after review.
