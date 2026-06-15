from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Iterable

from cities2_mcp import plugin_metadata
from cities2_mcp.plugin_metadata import SKILL_NAMES


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

CHECK_PACKAGE_ROOTS = (ANTIGRAVITY_PACKAGE_ROOT,)

CLAUDE_AND_CODEX_PACKAGE_ROOTS = (
    CLAUDE_PACKAGE_ROOT,
    CODEX_PACKAGE_ROOT,
)

CATALOG_PACKAGE_EXPORTS = (
    (CLAUDE_PACKAGE_ROOT, CATALOG_CLAUDE_PACKAGE_ROOT),
    (CODEX_PACKAGE_ROOT, CATALOG_CODEX_PACKAGE_ROOT),
)

METADATA_FILES: dict[Path, tuple[tuple[Path, Callable[[], str]], ...]] = {
    CLAUDE_PACKAGE_ROOT: (
        (
            CLAUDE_PACKAGE_ROOT / ".claude-plugin" / "plugin.json",
            plugin_metadata.claude_plugin_json,
        ),
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

CATALOG_MARKETPLACE_FILES: tuple[
    tuple[Path, Callable[[], str], Callable[[], dict[str, object]]],
    ...
] = (
    (
        Path(".claude-plugin") / "marketplace.json",
        plugin_metadata.claude_marketplace_json,
        plugin_metadata.claude_marketplace_entry,
    ),
    (
        Path(".agents") / "plugins" / "marketplace.json",
        plugin_metadata.codex_marketplace_json,
        plugin_metadata.codex_marketplace_entry,
    ),
)

MANAGED_DIRS = ("skills", "vendor")
MANAGED_FILES = (Path("bin") / "cities2-mcp-launcher.js",)

LAUNCHER_TEXT = """#!/usr/bin/env node

const fs = require("node:fs");
const { spawn, spawnSync } = require("node:child_process");
const path = require("node:path");

const selfRoot = path.resolve(__dirname, "..");

function candidates() {
  const configured = process.env.CITIES2_MCP_PYTHON;
  const values = [];
  if (configured) {
    values.push({ command: configured, args: [] });
  }
  if (process.platform === "win32") {
    values.push({ command: "py", args: ["-3"] });
  }
  values.push({ command: "python3", args: [] });
  values.push({ command: "python", args: [] });
  return values;
}

function findPython() {
  for (const candidate of candidates()) {
    const result = spawnSync(candidate.command, [...candidate.args, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"], {
      stdio: "ignore",
      windowsHide: true,
    });
    if (result.status === 0) {
      return candidate;
    }
  }
  return null;
}

function uniquePaths(values) {
  const seen = new Set();
  const paths = [];
  for (const value of values) {
    if (!value) {
      continue;
    }
    const resolved = path.resolve(value);
    const key = process.platform === "win32" ? resolved.toLowerCase() : resolved;
    if (!seen.has(key)) {
      seen.add(key);
      paths.push(resolved);
    }
  }
  return paths;
}

function invocationForRoot(pluginRoot) {
  const vendoredScript = path.join(pluginRoot, "vendor", "run_server.py");
  if (fs.existsSync(vendoredScript)) {
    return { args: [vendoredScript], env: process.env };
  }

  const vendoredPackageServer = path.join(pluginRoot, "vendor", "cities2_mcp", "mcp_server.py");
  if (fs.existsSync(vendoredPackageServer)) {
    const env = { ...process.env };
    env.PYTHONPATH = [path.join(pluginRoot, "vendor"), env.PYTHONPATH].filter(Boolean).join(path.delimiter);
    return { args: ["-m", "cities2_mcp.mcp_server"], env };
  }

  const sourceServer = path.join(pluginRoot, "cities2_mcp", "mcp_server.py");
  if (fs.existsSync(sourceServer)) {
    const env = { ...process.env };
    env.PYTHONPATH = [pluginRoot, env.PYTHONPATH].filter(Boolean).join(path.delimiter);
    return { args: ["-m", "cities2_mcp.mcp_server"], env };
  }

  return null;
}

function serverInvocation() {
  const checkedRoots = uniquePaths([selfRoot, process.env.PLUGIN_ROOT, process.env.CLAUDE_PLUGIN_ROOT]);
  for (const root of checkedRoots) {
    const invocation = invocationForRoot(root);
    if (invocation) {
      return invocation;
    }
  }

  console.error(`Unable to locate Cities2-MCP server files. Checked: ${checkedRoots.join("; ")}.`);
  process.exit(1);
}

const python = findPython();
if (!python) {
  console.error("Cities2-MCP requires Python 3.10 or newer. Set CITIES2_MCP_PYTHON to a Python interpreter if it is not on PATH.");
  process.exit(127);
}

const invocation = serverInvocation();
const child = spawn(python.command, [...python.args, ...invocation.args, ...process.argv.slice(2)], {
  env: invocation.env,
  stdio: ["inherit", "inherit", "inherit"],
  windowsHide: true,
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});

child.on("error", (error) => {
  console.error(`Unable to start Cities2-MCP: ${error.message}`);
  process.exit(1);
});
"""

RUN_SERVER_TEXT = """from __future__ import annotations

import sys
from pathlib import Path

VENDOR_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(VENDOR_ROOT))

from cities2_mcp.mcp_server import main  # noqa: E402


if __name__ == "__main__":
    main()
"""


def sync_packages(
    repo_root: Path | None = None,
    *,
    package_roots: Iterable[Path] = PACKAGE_ROOTS,
) -> tuple[Path, ...]:
    root = (repo_root or Path.cwd()).resolve()
    changed: list[Path] = []
    selected_roots = _selected_package_roots(package_roots)
    with tempfile.TemporaryDirectory(prefix="cities2-mcp-plugin-packages-") as tmp:
        tmp_root = Path(tmp)
        for package_rel in selected_roots:
            expected_root = tmp_root / package_rel
            actual_root = root / package_rel
            _write_payload(root, expected_root)
            changed.extend(_changed_paths(expected_root, actual_root))
            _replace_payload(expected_root, actual_root)
            changed.extend(_sync_metadata(root, package_rel))
    return tuple(sorted(set(changed)))


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


def check_packages(
    repo_root: Path | None = None,
    *,
    package_roots: Iterable[Path] = CHECK_PACKAGE_ROOTS,
) -> tuple[Path, ...]:
    root = (repo_root or Path.cwd()).resolve()
    changed: list[Path] = []
    selected_roots = _selected_package_roots(package_roots)
    with tempfile.TemporaryDirectory(prefix="cities2-mcp-plugin-packages-") as tmp:
        tmp_root = Path(tmp)
        for package_rel in selected_roots:
            expected_root = tmp_root / package_rel
            actual_root = root / package_rel
            _write_payload(root, expected_root)
            changed.extend(_changed_paths(expected_root, actual_root))
            changed.extend(_check_metadata(root, package_rel))
    return tuple(sorted(set(changed)))


def _validate_catalog_root(catalog: Path) -> None:
    if not catalog.is_dir():
        raise FileNotFoundError(f"Catalog root not found: {catalog}")
    if not (catalog / "plugins").is_dir():
        raise FileNotFoundError(f"Catalog plugins directory not found: {catalog / 'plugins'}")


def _ensure_inside(root: Path, target: Path) -> None:
    if not target.resolve().is_relative_to(root):
        raise ValueError(f"Catalog target escapes catalog root: {target}")


def _selected_package_roots(package_roots: Iterable[Path]) -> tuple[Path, ...]:
    selected = tuple(Path(package_root) for package_root in package_roots)
    unknown = tuple(package_root for package_root in selected if package_root not in METADATA_FILES)
    if unknown:
        unknown_text = ", ".join(str(package_root) for package_root in unknown)
        known_text = ", ".join(str(package_root) for package_root in METADATA_FILES)
        raise ValueError(f"Unknown package root(s): {unknown_text}. Expected one of: {known_text}")
    return selected


def _write_payload(repo_root: Path, package_root: Path) -> None:
    _copy_skills(repo_root / "skills", package_root / "skills")
    launcher_path = package_root / "bin" / "cities2-mcp-launcher.js"
    launcher_path.parent.mkdir(parents=True, exist_ok=True)
    launcher_path.write_text(LAUNCHER_TEXT, encoding="utf-8")

    vendor_root = package_root / "vendor"
    vendor_root.mkdir(parents=True, exist_ok=True)
    (vendor_root / "run_server.py").write_text(RUN_SERVER_TEXT, encoding="utf-8")
    shutil.copytree(
        repo_root / "cities2_mcp",
        vendor_root / "cities2_mcp",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
        dirs_exist_ok=True,
    )


def _copy_skills(source_root: Path, target_root: Path) -> None:
    target_root.mkdir(parents=True, exist_ok=True)
    for skill_name in SKILL_NAMES:
        source = source_root / skill_name
        if not source.is_dir():
            raise FileNotFoundError(f"Canonical skill not found: {source}")
        shutil.copytree(source, target_root / skill_name, dirs_exist_ok=True)


def _replace_payload(expected_root: Path, actual_root: Path) -> None:
    actual_root.mkdir(parents=True, exist_ok=True)
    for dirname in MANAGED_DIRS:
        target = actual_root / dirname
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(expected_root / dirname, target)
    for rel in MANAGED_FILES:
        target = actual_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(expected_root / rel, target)


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


def _changed_paths(expected_root: Path, actual_root: Path) -> tuple[Path, ...]:
    changed: list[Path] = []
    for dirname in MANAGED_DIRS:
        changed.extend(_changed_tree_paths(expected_root / dirname, actual_root / dirname))
    for rel in MANAGED_FILES:
        expected = expected_root / rel
        actual = actual_root / rel
        if not actual.is_file() or expected.read_bytes() != actual.read_bytes():
            changed.append(actual)
    return tuple(changed)


def _changed_tree_paths(expected_dir: Path, actual_dir: Path) -> tuple[Path, ...]:
    expected_files = {
        path.relative_to(expected_dir)
        for path in expected_dir.rglob("*")
        if path.is_file() and not _is_ignored_payload_path(path)
    }
    actual_files = (
        {
            path.relative_to(actual_dir)
            for path in actual_dir.rglob("*")
            if path.is_file() and not _is_ignored_payload_path(path)
        }
        if actual_dir.exists()
        else set()
    )

    changed: list[Path] = []
    for rel in expected_files:
        expected = expected_dir / rel
        actual = actual_dir / rel
        if rel not in actual_files or expected.read_bytes() != actual.read_bytes():
            changed.append(actual)
    for rel in actual_files - expected_files:
        changed.append(actual_dir / rel)
    return tuple(changed)


def _is_ignored_payload_path(path: Path) -> bool:
    return "__pycache__" in path.parts or path.suffix == ".pyc"


def _upsert_catalog_marketplaces(catalog: Path) -> list[Path]:
    changed: list[Path] = []
    for rel, default_builder, entry_builder in CATALOG_MARKETPLACE_FILES:
        target = catalog / rel
        _ensure_inside(catalog, target)
        content = _catalog_marketplace_content(target, default_builder, entry_builder)
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current != content:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            changed.append(target)
    return changed


def _catalog_marketplace_content(
    target: Path,
    default_builder: Callable[[], str],
    entry_builder: Callable[[], dict[str, object]],
) -> str:
    if target.is_file():
        manifest = json.loads(target.read_text(encoding="utf-8"))
    else:
        manifest = json.loads(default_builder())

    fresh = entry_builder()
    fresh_name = fresh["name"]
    existing_plugins = manifest.get("plugins", [])
    plugins = existing_plugins if isinstance(existing_plugins, list) else []
    manifest["plugins"] = [
        plugin
        for plugin in plugins
        if not (isinstance(plugin, dict) and plugin.get("name") == fresh_name)
    ]
    manifest["plugins"].append(fresh)
    return _json_dumps(manifest)


def _json_dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m cities2_mcp.plugin_packages",
        description="Synchronize generated Cities2-MCP plugin package payloads.",
    )
    parser.add_argument("command", choices=("sync", "check", "sync-catalog"))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog-root", type=Path, default=DEFAULT_CATALOG_ROOT)
    args = parser.parse_args(argv)

    if args.command == "sync":
        changed = sync_packages(args.repo_root)
        for path in changed:
            print(f"updated {path}")
        return 0

    if args.command == "sync-catalog":
        changed = sync_catalog_packages(args.catalog_root, repo_root=args.repo_root)
        for path in changed:
            print(f"updated {path}")
        return 0

    stale = check_packages(args.repo_root)
    if stale:
        print("Stale plugin package payloads: generated artifacts differ from canonical sources.")
        print("Canonical sources: skills/, cities2_mcp/, and cities2_mcp.plugin_metadata")
        print("Generated copies: dist/integrations/anthropic/claude-plugin/, dist/plugins/cities2-mcp/, and plugins/cities2-mcp/ for Antigravity")
        print("Run: python -m cities2_mcp.plugin_packages sync")
        for path in stale:
            print(f"  {path}")
        return 1
    print("Plugin package payloads are in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
