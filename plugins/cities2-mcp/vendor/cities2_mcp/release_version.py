from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Sequence

ReleaseLevel = Literal["patch", "minor", "major"]
TagAction = Literal["create", "exists"]
VERSION_RE = re.compile(r'\A__version__ = "(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"\n?\Z')
LEGACY_VERSION_RE = re.compile(r'(?m)^__version__ = "(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"$')
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


def tag_action(version: SemVer, commit_sha: str, existing_sha: str | None) -> TagAction:
    if not commit_sha:
        raise ValueError("Current commit SHA is required")
    if existing_sha is None:
        return "create"
    if existing_sha == commit_sha:
        return "exists"
    raise ValueError(f"Tag v{version} already points at a different commit: {existing_sha}")


def _version_from_text(text: str) -> SemVer:
    match = VERSION_RE.fullmatch(text)
    if match is None:
        raise ValueError("Canonical version file has an unexpected format")
    return SemVer(*(int(part) for part in match.groups()))


def _legacy_version_from_text(text: str) -> SemVer:
    match = LEGACY_VERSION_RE.search(text)
    if match is None:
        raise ValueError("Legacy package version has an unexpected format")
    return SemVer(*(int(part) for part in match.groups()))


def version_from_ref(repo_root: Path, ref: str) -> SemVer:
    canonical = subprocess.run(
        ["git", "show", f"{ref}:cities2_mcp/_version.py"],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if canonical.returncode == 0:
        return _version_from_text(canonical.stdout)

    legacy = subprocess.run(
        ["git", "show", f"{ref}:cities2_mcp/__init__.py"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )
    return _legacy_version_from_text(legacy.stdout)



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
    tag_state = subparsers.add_parser("tag-state")
    tag_state.add_argument("--version", required=True)
    tag_state.add_argument("--commit-sha", required=True)
    tag_state.add_argument("--existing-sha", default="")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "tag-state":
        action = tag_action(
            SemVer.parse(args.version),
            args.commit_sha,
            args.existing_sha or None,
        )
        print(action)
        return 0
    repo_root = args.repo_root.resolve()
    base = SemVer.parse(args.base_version) if args.base_version else version_from_ref(repo_root, args.base_ref)
    target = prepare_release(repo_root, base, args.label)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
