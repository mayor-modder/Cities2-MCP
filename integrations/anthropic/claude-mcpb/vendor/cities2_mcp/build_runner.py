from __future__ import annotations

import fnmatch
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .diagnostics import parse_build_output
from .project_scaffold import ProjectScaffolder

JSON = Dict[str, Any]


class BuildRunner:
    PROFILE_VALUES = {"debug", "release"}
    STEP_VALUES = {"ui", "dotnet", "package"}
    PROJECT_PROFILE_VALUES = {"cities2-csharp", "cities2-ui", "cities2-hybrid", "auto"}

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
    def _resolve_command_argv(argv: Sequence[str], env: Dict[str, str]) -> List[str]:
        if not argv:
            return []
        command = str(argv[0])
        if any(separator in command for separator in ("/", "\\")):
            return [command, *[str(arg) for arg in argv[1:]]]

        resolved = shutil.which(command, path=env.get("PATH"))
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

        name = package_name or root.name
        zip_path = (out_dir / f"{name}.zip").resolve()
        excludes = [str(x) for x in (exclude_globs or []) if str(x).strip()]

        entries = 0
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for p in sorted(root.rglob("*")):
                if not p.is_file():
                    continue
                rel = p.relative_to(root)
                rel_str = rel.as_posix()
                if any(fnmatch.fnmatch(rel_str, g) for g in excludes):
                    continue
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

    @staticmethod
    def _platform_name(value: str) -> str:
        val = value.strip().lower()
        if val != "auto":
            return val
        if sys.platform == "darwin":
            return "mac"
        if sys.platform.startswith("win"):
            return "windows"
        return "linux"

    @staticmethod
    def _default_executable(platform_name: str) -> str:
        if platform_name == "mac":
            return "/Applications/Cities Skylines II.app/Contents/MacOS/Cities Skylines II"
        if platform_name == "windows":
            return r"C:\\Program Files (x86)\\Steam\\steamapps\\common\\Cities Skylines II\\Cities2.exe"
        return "Cities2"

    def launch_cities2(
        self,
        executable: Optional[str],
        flags: Optional[List[str]],
        platform: str,
        dry_run: bool,
    ) -> JSON:
        platform_name = self._platform_name(platform)
        if platform_name not in {"mac", "windows", "linux"}:
            raise ValueError("platform must be one of: auto, mac, windows, linux")

        resolved_executable = executable or self._default_executable(platform_name)
        cmd = [resolved_executable, *[str(f) for f in (flags or [])]]

        if dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "platform": platform_name,
                "resolved_executable": resolved_executable,
                "command": cmd,
                "message": "Dry run only; command not executed.",
            }

        if platform_name != "windows":
            exe_path = Path(resolved_executable).expanduser()
            if (os.path.sep in resolved_executable or resolved_executable.startswith(".")) and not exe_path.exists():
                return {
                    "ok": False,
                    "dry_run": False,
                    "platform": platform_name,
                    "resolved_executable": resolved_executable,
                    "command": cmd,
                    "message": f"Executable not found: {resolved_executable}",
                }

        proc = subprocess.Popen(cmd)
        return {
            "ok": True,
            "dry_run": False,
            "platform": platform_name,
            "resolved_executable": resolved_executable,
            "command": cmd,
            "pid": proc.pid,
            "message": "Launched process.",
        }
