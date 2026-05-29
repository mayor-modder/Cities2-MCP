from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path
from typing import Iterable

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

MANAGED_DIRS = ("skills", "vendor")
MANAGED_FILES = (Path("bin") / "cities2-mcp-launcher.js",)

LAUNCHER_TEXT = """#!/usr/bin/env node

const { spawn, spawnSync } = require("node:child_process");
const path = require("node:path");

const pluginRoot = process.env.PLUGIN_ROOT || process.env.CLAUDE_PLUGIN_ROOT || path.resolve(__dirname, "..");
const serverScript = path.join(pluginRoot, "vendor", "run_server.py");

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

const python = findPython();
if (!python) {
  console.error("Cities2-MCP requires Python 3.10 or newer. Set CITIES2_MCP_PYTHON to a Python interpreter if it is not on PATH.");
  process.exit(127);
}

const child = spawn(python.command, [...python.args, serverScript, ...process.argv.slice(2)], {
  env: process.env,
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
    with tempfile.TemporaryDirectory(prefix="cities2-mcp-plugin-packages-") as tmp:
        tmp_root = Path(tmp)
        for package_rel in package_roots:
            expected_root = tmp_root / package_rel
            actual_root = root / package_rel
            _write_payload(root, expected_root)
            changed.extend(_changed_paths(expected_root, actual_root))
            _replace_payload(expected_root, actual_root)
    return tuple(sorted(set(changed)))


def check_packages(
    repo_root: Path | None = None,
    *,
    package_roots: Iterable[Path] = PACKAGE_ROOTS,
) -> tuple[Path, ...]:
    root = (repo_root or Path.cwd()).resolve()
    changed: list[Path] = []
    with tempfile.TemporaryDirectory(prefix="cities2-mcp-plugin-packages-") as tmp:
        tmp_root = Path(tmp)
        for package_rel in package_roots:
            expected_root = tmp_root / package_rel
            actual_root = root / package_rel
            _write_payload(root, expected_root)
            changed.extend(_changed_paths(expected_root, actual_root))
    return tuple(sorted(set(changed)))


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
    expected_files = {path.relative_to(expected_dir) for path in expected_dir.rglob("*") if path.is_file()}
    actual_files = {path.relative_to(actual_dir) for path in actual_dir.rglob("*") if path.is_file()} if actual_dir.exists() else set()

    changed: list[Path] = []
    for rel in expected_files:
        expected = expected_dir / rel
        actual = actual_dir / rel
        if rel not in actual_files or expected.read_bytes() != actual.read_bytes():
            changed.append(actual)
    for rel in actual_files - expected_files:
        changed.append(actual_dir / rel)
    return tuple(changed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m cities2_mcp.plugin_packages",
        description="Synchronize generated Cities2-MCP plugin package payloads.",
    )
    parser.add_argument("command", choices=("sync", "check"))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    if args.command == "sync":
        changed = sync_packages(args.repo_root)
        for path in changed:
            print(f"updated {path}")
        return 0

    stale = check_packages(args.repo_root)
    if stale:
        print("Stale plugin package payloads:")
        for path in stale:
            print(f"  {path}")
        return 1
    print("Plugin package payloads are in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
