from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Dict, List, Optional, Sequence

from .diagnostics import parse_build_output
from .project_scaffold import ProjectScaffolder

JSON = Dict[str, Any]


class BuildRunner:
    PROFILE_VALUES = {"debug", "release"}
    STEP_VALUES = {"ui", "dotnet", "package"}
    PROJECT_PROFILE_VALUES = {"cities2-csharp", "cities2-ui", "cities2-hybrid", "auto"}
    DEFAULT_PACKAGE_EXCLUDES = {
        ".git/**",
        ".venv/**",
        "__pycache__/**",
        "*.pyc",
        "bin/**",
        "node_modules/**",
        "obj/**",
        "packages/**",
    }
    PRUNE_PACKAGE_DIR_NAMES = {".git", ".venv", "__pycache__", "bin", "node_modules", "obj", "packages"}

    def __init__(self, scaffolder: ProjectScaffolder) -> None:
        self.scaffolder = scaffolder
        self.workspace = scaffolder.workspace

    @staticmethod
    def _tail(text: str, max_chars: int = 12000) -> str:
        if len(text) <= max_chars:
            return text
        return text[-max_chars:]

    @staticmethod
    def _common_windows_tool_dirs(env: Dict[str, str]) -> List[Path]:
        candidates: List[Path] = []
        folded_env = {key.casefold(): value for key, value in env.items()}
        for key in ("ProgramFiles", "ProgramFiles(x86)"):
            root = str(folded_env.get(key.casefold(), "")).strip()
            if not root:
                continue
            candidates.append(Path(root) / "nodejs")
            candidates.append(Path(root) / "dotnet")

        local_appdata = str(folded_env.get("localappdata", "")).strip()
        if local_appdata:
            candidates.append(Path(local_appdata) / "Programs" / "nodejs")
            candidates.append(Path(local_appdata) / "Microsoft" / "WinGet" / "Packages")

        seen: set[str] = set()
        unique: List[Path] = []
        for candidate in candidates:
            text = str(candidate)
            if text not in seen:
                seen.add(text)
                unique.append(candidate)
        return unique

    @classmethod
    def _subprocess_env(
        cls,
        *,
        env: Optional[Dict[str, str]] = None,
        platform: Optional[str] = None,
    ) -> Dict[str, str]:
        merged = dict(os.environ if env is None else env)
        platform_name = platform or sys.platform
        if not platform_name.startswith("win"):
            return merged

        path_parts = [part for part in str(merged.get("PATH", "")).split(os.pathsep) if part]
        normalized = {part.casefold() for part in path_parts}
        for candidate in cls._common_windows_tool_dirs(merged):
            if not candidate.is_dir():
                continue
            candidate_text = str(candidate)
            if candidate_text.casefold() in normalized:
                continue
            path_parts.append(candidate_text)
            normalized.add(candidate_text.casefold())
        merged["PATH"] = os.pathsep.join(path_parts)
        return merged

    @staticmethod
    def _resolve_windows_command(command: str, env: Dict[str, str]) -> str:
        path_value = env.get("PATH", "")
        path_parts = [part for part in str(path_value).split(os.pathsep) if part]
        extensions = [ext for ext in str(env.get("PATHEXT", ".COM;.EXE;.BAT;.CMD")).split(";") if ext]
        if Path(command).suffix:
            names = [command]
        else:
            names = []
            for ext in extensions:
                for suffix in (ext, ext.lower(), ext.upper()):
                    name = command + suffix
                    if name not in names:
                        names.append(name)
        for directory in path_parts:
            for name in names:
                candidate = Path(directory) / name
                if candidate.is_file():
                    return str(candidate)
        return ""

    @classmethod
    def _resolve_command_argv(
        cls,
        argv: Sequence[str],
        env: Dict[str, str],
        *,
        platform: Optional[str] = None,
    ) -> List[str]:
        if not argv:
            return []
        command = str(argv[0])
        if any(separator in command for separator in ("/", "\\")):
            return [command, *[str(arg) for arg in argv[1:]]]

        resolved = shutil.which(command, path=env.get("PATH"))
        if not resolved and (platform or sys.platform).startswith("win"):
            resolved = cls._resolve_windows_command(command, env)
        if resolved:
            return [resolved, *[str(arg) for arg in argv[1:]]]
        return [command, *[str(arg) for arg in argv[1:]]]

    def _run_command(self, argv: Sequence[str], cwd: Path, timeout_sec: int) -> JSON:
        started = time.monotonic()
        env = self._subprocess_env()
        resolved_argv = self._resolve_command_argv(argv, env)
        try:
            proc = subprocess.run(
                resolved_argv,
                cwd=str(cwd),
                env=env,
                capture_output=True,
                text=True,
                timeout=max(10, int(timeout_sec)),
            )
            output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
            return {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "command": list(argv),
                "duration_ms": int((time.monotonic() - started) * 1000),
                "output": output,
            }
        except FileNotFoundError:
            tool = argv[0] if argv else "command"
            msg = f"{tool} not found in PATH"
            return {
                "ok": False,
                "returncode": 127,
                "command": list(argv),
                "duration_ms": int((time.monotonic() - started) * 1000),
                "output": msg,
            }
        except subprocess.TimeoutExpired as exc:
            out = (exc.stdout or "") + ("\n" + exc.stderr if exc.stderr else "")
            return {
                "ok": False,
                "returncode": 124,
                "command": list(argv),
                "duration_ms": int((time.monotonic() - started) * 1000),
                "output": out + f"\nCommand timed out after {timeout_sec}s",
            }

    @staticmethod
    def _find_ui_dir(root: Path) -> Optional[Path]:
        if (root / "package.json").exists():
            return root
        if (root / "ui" / "package.json").exists():
            return root / "ui"
        return None

    def _default_steps_for_project(self, project_profile: str) -> List[str]:
        if project_profile == "cities2-csharp":
            return ["dotnet"]
        if project_profile == "cities2-ui":
            return ["ui"]
        if project_profile == "cities2-hybrid":
            return ["ui", "dotnet"]
        return []

    def _normalize_project_profile(self, project_dir: str, profile: str) -> str:
        profile = (profile or "auto").strip().lower()
        if profile not in self.PROJECT_PROFILE_VALUES:
            raise ValueError("project profile must be one of: auto, cities2-csharp, cities2-ui, cities2-hybrid")
        if profile == "auto":
            profile = self.scaffolder.detect_profile(project_dir)
        if profile not in {"cities2-csharp", "cities2-ui", "cities2-hybrid"}:
            raise ValueError("Unable to detect project profile from project contents")
        return profile

    def package_project(
        self,
        project_dir: str,
        output_dir: Optional[str],
        package_name: Optional[str],
        exclude_globs: Optional[List[str]],
    ) -> JSON:
        root = self.scaffolder.resolve_workspace_path(project_dir)
        out_dir = self.scaffolder.resolve_workspace_path(output_dir) if output_dir else (root / "packages")
        out_dir.mkdir(parents=True, exist_ok=True)

        name = self._safe_package_name(package_name or root.name)
        zip_path = (out_dir / f"{name}.zip").resolve()
        if not ProjectScaffolder.is_within_path(zip_path, out_dir):
            raise ValueError("package output path escapes output_dir")
        excludes = sorted(
            self.DEFAULT_PACKAGE_EXCLUDES
            | {
                ProjectScaffolder.validate_relative_glob(str(x), field_name="exclude_globs")
                for x in (exclude_globs or [])
                if str(x).strip()
            }
        )

        entries = 0
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for current_root, dirnames, filenames in os.walk(root):
                current = Path(current_root)
                rel_dir = current.relative_to(root).as_posix()
                if rel_dir == ".":
                    rel_dir = ""
                self._prune_unsafe_directories(root, current, dirnames)
                dirnames[:] = [
                    dirname
                    for dirname in dirnames
                    if dirname not in self.PRUNE_PACKAGE_DIR_NAMES
                ]
                for filename in sorted(filenames):
                    p = current / filename
                    if p.resolve() == zip_path:
                        continue
                    rel = p.relative_to(root)
                    rel_str = rel.as_posix()
                    if any(PurePosixPath(rel_str).match(g) for g in excludes):
                        continue
                    resolved_file = p.resolve()
                    if not ProjectScaffolder.is_within_path(resolved_file, root):
                        raise ValueError(f"package file resolves outside project root: {rel_str}")
                    if p.stat(follow_symlinks=False).st_nlink > 1:
                        raise ValueError(f"package file has multiple hard links: {rel_str}")
                    zf.write(p, arcname=rel_str)
                    entries += 1

        return {
            "ok": True,
            "project_dir": str(root),
            "package_path": str(zip_path),
            "size": zip_path.stat().st_size,
            "entries_count": entries,
            "excluded": excludes,
        }

    @staticmethod
    def _safe_package_name(value: str) -> str:
        name = str(value or "").strip()
        posix = PurePosixPath(name)
        windows = PureWindowsPath(name)
        if not name or name in {".", ".."}:
            raise ValueError("package_name must be a non-empty file name")
        if posix.is_absolute() or windows.is_absolute() or windows.drive:
            raise ValueError("package_name must not be an absolute path")
        if "/" in name or "\\" in name or ".." in posix.parts or ".." in windows.parts:
            raise ValueError("package_name must not contain path separators or parent traversal")
        return name

    @staticmethod
    def _prune_unsafe_directories(root: Path, current: Path, dirnames: List[str]) -> None:
        for dirname in list(dirnames):
            path = current / dirname
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                dirnames.remove(dirname)
                if not ProjectScaffolder.is_within_path(path.resolve(), root):
                    raise ValueError(f"package directory resolves outside project root: {rel}")
                continue
            if ProjectScaffolder.is_reparse_point(path):
                dirnames.remove(dirname)

    def build_project(
        self,
        project_dir: str,
        profile: str,
        steps: Optional[List[str]],
        clean: bool,
        package: bool,
        timeout_sec: int,
    ) -> JSON:
        root = self.scaffolder.resolve_workspace_path(project_dir)
        build_profile = (profile or "release").strip().lower()
        if build_profile not in self.PROFILE_VALUES:
            raise ValueError("profile must be one of: debug, release")

        project_profile = self._normalize_project_profile(str(root), "auto")

        selected_steps = [str(x).strip().lower() for x in (steps or self._default_steps_for_project(project_profile)) if str(x).strip()]
        if not selected_steps:
            selected_steps = self._default_steps_for_project(project_profile)
        for step in selected_steps:
            if step not in self.STEP_VALUES:
                raise ValueError("steps must only contain: ui, dotnet, package")

        if package and "package" not in selected_steps:
            selected_steps.append("package")

        results: List[JSON] = []

        for step in selected_steps:
            if step == "ui":
                ui_dir = self._find_ui_dir(root)
                if ui_dir is None:
                    results.append(
                        {
                            "name": "ui",
                            "ok": False,
                            "returncode": 2,
                            "command": [],
                            "duration_ms": 0,
                            "output_tail": "package.json not found in project root or ui/",
                            "diagnostics": [],
                        }
                    )
                    break

                install_cmd = ["npm", "ci"] if (ui_dir / "package-lock.json").exists() else ["npm", "install"]
                install_run = self._run_command(install_cmd, ui_dir, timeout_sec)
                install_diag = parse_build_output(install_run["output"], tool_hint="npm")
                results.append(
                    {
                        "name": "ui-install",
                        "ok": bool(install_run["ok"]),
                        "returncode": int(install_run["returncode"]),
                        "command": install_run["command"],
                        "duration_ms": int(install_run["duration_ms"]),
                        "output_tail": self._tail(str(install_run["output"])),
                        "diagnostics": install_diag,
                    }
                )
                if not install_run["ok"]:
                    break

                build_run = self._run_command(["npm", "run", "build"], ui_dir, timeout_sec)
                build_diag = parse_build_output(build_run["output"], tool_hint="npm")
                results.append(
                    {
                        "name": "ui-build",
                        "ok": bool(build_run["ok"]),
                        "returncode": int(build_run["returncode"]),
                        "command": build_run["command"],
                        "duration_ms": int(build_run["duration_ms"]),
                        "output_tail": self._tail(str(build_run["output"])),
                        "diagnostics": build_diag,
                    }
                )
                if not build_run["ok"]:
                    break

            elif step == "dotnet":
                if clean:
                    clean_run = self._run_command(["dotnet", "clean", "-c", build_profile.capitalize()], root, timeout_sec)
                    clean_diag = parse_build_output(clean_run["output"], tool_hint="dotnet")
                    results.append(
                        {
                            "name": "dotnet-clean",
                            "ok": bool(clean_run["ok"]),
                            "returncode": int(clean_run["returncode"]),
                            "command": clean_run["command"],
                            "duration_ms": int(clean_run["duration_ms"]),
                            "output_tail": self._tail(str(clean_run["output"])),
                            "diagnostics": clean_diag,
                        }
                    )
                    if not clean_run["ok"]:
                        break

                build_run = self._run_command(["dotnet", "build", "-c", build_profile.capitalize()], root, timeout_sec)
                build_diag = parse_build_output(build_run["output"], tool_hint="dotnet")
                results.append(
                    {
                        "name": "dotnet-build",
                        "ok": bool(build_run["ok"]),
                        "returncode": int(build_run["returncode"]),
                        "command": build_run["command"],
                        "duration_ms": int(build_run["duration_ms"]),
                        "output_tail": self._tail(str(build_run["output"])),
                        "diagnostics": build_diag,
                    }
                )
                if not build_run["ok"]:
                    break

            elif step == "package":
                package_payload = self.package_project(str(root), None, None, None)
                results.append(
                    {
                        "name": "package",
                        "ok": bool(package_payload["ok"]),
                        "returncode": 0 if package_payload["ok"] else 1,
                        "command": ["zip"],
                        "duration_ms": 0,
                        "output_tail": self._tail(str(package_payload)),
                        "diagnostics": [],
                        "package": package_payload,
                    }
                )

        ok = all(bool(step.get("ok")) for step in results) if results else False
        diagnostics: List[JSON] = []
        for step in results:
            diagnostics.extend(step.get("diagnostics", []))

        summary = {
            "errors": sum(1 for d in diagnostics if d.get("severity") == "error"),
            "warnings": sum(1 for d in diagnostics if d.get("severity") == "warning"),
            "steps_run": len(results),
            "project_profile": project_profile,
        }

        return {
            "ok": ok,
            "project_dir": str(root),
            "profile": build_profile,
            "steps": results,
            "summary": summary,
        }
