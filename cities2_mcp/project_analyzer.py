from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from .project_scaffold import ProjectScaffolder

JSON = Dict[str, Any]


class ProjectAnalyzer:
    PROFILE_VALUES = {"auto", "cities2-csharp", "cities2-ui", "cities2-hybrid"}

    def __init__(self, scaffolder: ProjectScaffolder) -> None:
        self.scaffolder = scaffolder

    @staticmethod
    def _check(check_id: str, status: str, message: str, file: str, fix_hint: str) -> JSON:
        return {
            "id": check_id,
            "status": status,
            "message": message,
            "file": file,
            "fix_hint": fix_hint,
        }

    @staticmethod
    def _extract_xml_value(text: str, node: str) -> str:
        m = re.search(rf"<{re.escape(node)}>(.*?)</{re.escape(node)}>", text, re.IGNORECASE | re.DOTALL)
        if not m:
            return ""
        return m.group(1).strip()

    @staticmethod
    def _extract_dependencies(csproj_text: str) -> List[str]:
        deps = set(re.findall(r"<Dependency\s+Include=\"([^\"]+)\"", csproj_text, re.IGNORECASE))
        deps.update(re.findall(r"<PackageReference\s+Include=\"([^\"]+)\"", csproj_text, re.IGNORECASE))
        return sorted(deps)

    @staticmethod
    def _extract_references(csproj_text: str) -> List[str]:
        refs = set(re.findall(r"<Reference\s+Include=\"([^\"]+)\"", csproj_text, re.IGNORECASE))
        return sorted(refs)

    @staticmethod
    def _extract_conflicts(readme_text: str) -> List[str]:
        conflicts = []
        for line in readme_text.splitlines():
            if "incompatible" in line.lower() or "conflict" in line.lower():
                value = line.strip("- *\t")
                if value:
                    conflicts.append(value)
        return conflicts[:20]

    @staticmethod
    def _score(checks: List[JSON]) -> int:
        if not checks:
            return 0
        weights = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
        total = sum(weights.get(str(c.get("status", "")).lower(), 0.0) for c in checks)
        return int(round((total / len(checks)) * 100))

    @staticmethod
    def _uses_file_scoped_namespace(root: Path) -> bool:
        for cs_file in root.rglob("*.cs"):
            text = cs_file.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"(?m)^\s*namespace\s+[A-Za-z_][A-Za-z0-9_.]*\s*;", text):
                return True
        return False

    @staticmethod
    def _langversion_follows_toolchain_imports(csproj_text: str) -> bool:
        lang_positions = [match.start() for match in re.finditer(r"<LangVersion>", csproj_text, re.IGNORECASE)]
        import_positions = [
            match.start()
            for match in re.finditer(r"\\Mod\.(?:props|targets)", csproj_text, re.IGNORECASE)
            if "<Import" in csproj_text[max(0, match.start() - 160) : match.start()]
        ]
        if not lang_positions or not import_positions:
            return True
        return max(lang_positions) > max(import_positions)

    @staticmethod
    def _defined_type_names(root: Path) -> set[str]:
        names: set[str] = set()
        pattern = re.compile(r"\b(?:class|struct|interface|record(?:\s+class|\s+struct)?)\s+([A-Za-z_][A-Za-z0-9_]*)")
        for cs_file in root.rglob("*.cs"):
            text = cs_file.read_text(encoding="utf-8", errors="ignore")
            names.update(pattern.findall(text))
        return names

    @staticmethod
    def _referenced_update_system_names(root: Path) -> List[str]:
        pattern = re.compile(
            r"\b(?:UpdateAt|UpdateBefore|UpdateAfter|GetOrCreateSystemManaged|"
            r"GetExistingSystemManaged|GetOrCreateSystem|GetExistingSystem)\s*<\s*([^>,\s]+)"
        )
        names = set()
        for cs_file in root.rglob("*.cs"):
            text = cs_file.read_text(encoding="utf-8", errors="ignore")
            for match in pattern.findall(text):
                name = match.replace("global::", "").split(".")[-1].strip()
                if name:
                    names.add(name)
        return sorted(names)

    def analyze_project(self, project_dir: str, profile: str, strict: bool = True) -> JSON:
        profile = (profile or "auto").strip().lower()
        if profile not in self.PROFILE_VALUES:
            raise ValueError("profile must be one of: auto, cities2-csharp, cities2-ui, cities2-hybrid")

        root = self.scaffolder.resolve_workspace_path(project_dir)
        detected = self.scaffolder.detect_profile(str(root))
        project_profile = detected if profile == "auto" else profile
        if project_profile not in {"cities2-csharp", "cities2-ui", "cities2-hybrid"}:
            raise ValueError("Unable to detect project profile from project contents")

        checks: List[JSON] = []
        checks.append(
            self._check(
                "project_profile",
                "pass",
                f"Detected project profile: {project_profile}",
                str(root),
                "",
            )
        )

        mod_file = root / "Mod.cs"
        mod_text = mod_file.read_text(encoding="utf-8") if mod_file.exists() else ""
        readme_file = root / "README.md"
        readme_text = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

        csproj_text = ""
        csproj_path = self.scaffolder.find_primary_csproj(root)
        if csproj_path and csproj_path.exists():
            csproj_text = csproj_path.read_text(encoding="utf-8")

        if project_profile in {"cities2-csharp", "cities2-hybrid"}:
            required_nodes = ["DisplayName", "ShortDescription", "GameVersion"]
            missing = [n for n in required_nodes if not self._extract_xml_value(csproj_text, n)]
            if missing:
                status = "fail" if strict else "warn"
                checks.append(
                    self._check(
                        "metadata_complete",
                        status,
                        f"Missing csproj metadata nodes: {', '.join(missing)}",
                        str(csproj_path) if csproj_path else str(root),
                        "Add missing metadata nodes to the main .csproj file.",
                    )
                )
            else:
                checks.append(
                    self._check(
                        "metadata_complete",
                        "pass",
                        "Core csproj metadata nodes are present.",
                        str(csproj_path),
                        "",
                    )
                )

            if self._uses_file_scoped_namespace(root) and not self._langversion_follows_toolchain_imports(csproj_text):
                checks.append(
                    self._check(
                        "langversion_after_toolchain_imports",
                        "fail" if strict else "warn",
                        "Project uses file-scoped namespaces, but LangVersion may be overridden by the CS2 toolchain imports.",
                        str(csproj_path) if csproj_path else str(root),
                        "Set LangVersion after the Mod.props/Mod.targets imports or convert file-scoped namespaces to block namespaces.",
                    )
                )
            else:
                checks.append(
                    self._check(
                        "langversion_after_toolchain_imports",
                        "pass",
                        "LangVersion ordering is compatible with file-scoped namespaces.",
                        str(csproj_path) if csproj_path else str(root),
                        "",
                    )
                )

            references = self._extract_references(csproj_text)
            if "Unity.Entities" in references and "Unity.Collections" not in references:
                checks.append(
                    self._check(
                        "unity_collections_reference",
                        "fail" if strict else "warn",
                        "Unity.Entities is referenced without Unity.Collections.",
                        str(csproj_path) if csproj_path else str(root),
                        "Add a Unity.Collections reference with Private=false.",
                    )
                )
            else:
                checks.append(
                    self._check(
                        "unity_collections_reference",
                        "pass",
                        "Unity assembly references include required companion references.",
                        str(csproj_path) if csproj_path else str(root),
                        "",
                    )
                )

            defined_types = self._defined_type_names(root)
            referenced_systems = self._referenced_update_system_names(root)
            missing_systems = [name for name in referenced_systems if name not in defined_types]
            if missing_systems:
                checks.append(
                    self._check(
                        "unresolved_update_systems",
                        "fail" if strict else "warn",
                        f"UpdateSystem references missing system types: {', '.join(missing_systems)}",
                        str(mod_file),
                        "Define the referenced system types or remove the UpdateSystem scheduling calls.",
                    )
                )
            else:
                checks.append(
                    self._check(
                        "unresolved_update_systems",
                        "pass",
                        "UpdateSystem generic references resolve to project types or none are present.",
                        str(mod_file),
                        "",
                    )
                )

            publish_cfg = root / "Properties" / "PublishConfiguration.xml"
            if publish_cfg.exists():
                checks.append(self._check("publish_config", "pass", "PublishConfiguration.xml found.", str(publish_cfg), ""))
            else:
                checks.append(
                    self._check(
                        "publish_config",
                        "fail" if strict else "warn",
                        "PublishConfiguration.xml missing.",
                        str(root / "Properties"),
                        "Add Properties/PublishConfiguration.xml for release metadata.",
                    )
                )

            setting_file = root / "Setting.cs"
            has_setting_registration = "RegisterInOptionsUI" in mod_text
            has_setting_unregistration = "UnregisterInOptionsUI" in mod_text
            if setting_file.exists() and has_setting_registration and has_setting_unregistration:
                checks.append(
                    self._check(
                        "settings_lifecycle",
                        "pass",
                        "Settings register/unregister lifecycle detected.",
                        str(mod_file),
                        "",
                    )
                )
            else:
                checks.append(
                    self._check(
                        "settings_lifecycle",
                        "warn" if not strict else "fail",
                        "Settings lifecycle is incomplete or missing.",
                        str(mod_file),
                        "Implement RegisterInOptionsUI in OnLoad and UnregisterInOptionsUI in OnDispose.",
                    )
                )

            locale_file = root / "LocaleEN.cs"
            has_add_source = "AddSource(" in mod_text
            if locale_file.exists() and has_add_source:
                checks.append(
                    self._check(
                        "localization_lifecycle",
                        "pass",
                        "Localization source setup detected.",
                        str(locale_file),
                        "",
                    )
                )
            else:
                checks.append(
                    self._check(
                        "localization_lifecycle",
                        "warn",
                        "Localization source setup missing or incomplete.",
                        str(mod_file),
                        "Add a locale source class and register it via localizationManager.AddSource(...).",
                    )
                )

            has_patch = "PatchAll(" in mod_text
            has_unpatch = "UnpatchAll(" in mod_text
            if has_patch and has_unpatch:
                checks.append(
                    self._check(
                        "patch_unpatch_symmetry",
                        "pass",
                        "Patch/unpatch symmetry detected.",
                        str(mod_file),
                        "",
                    )
                )
            elif has_patch and not has_unpatch:
                checks.append(
                    self._check(
                        "patch_unpatch_symmetry",
                        "fail" if strict else "warn",
                        "Patch setup found but unpatch cleanup is missing.",
                        str(mod_file),
                        "Call UnpatchAll in OnDispose for your Harmony ID.",
                    )
                )
            else:
                checks.append(
                    self._check(
                        "patch_unpatch_symmetry",
                        "warn",
                        "No Harmony patch lifecycle detected.",
                        str(mod_file),
                        "If this mod patches game code, add Harmony patch/unpatch lifecycle.",
                    )
                )

        has_root_pkg = (root / "package.json").exists()
        package_path = root / "package.json" if has_root_pkg else (root / "ui" / "package.json")
        package_text = package_path.read_text(encoding="utf-8") if package_path.exists() else ""

        if project_profile in {"cities2-ui", "cities2-hybrid"}:
            if package_path.exists() and '"build"' in package_text:
                checks.append(
                    self._check(
                        "ui_pipeline",
                        "pass",
                        "UI build script detected.",
                        str(package_path),
                        "",
                    )
                )
            else:
                checks.append(
                    self._check(
                        "ui_pipeline",
                        "fail" if strict else "warn",
                        "UI package.json with build script is missing.",
                        str(package_path),
                        "Add package.json with a build script (npm run build).",
                    )
                )

        if project_profile == "cities2-hybrid":
            if "npm run build" in csproj_text and "BuildUI" in csproj_text:
                checks.append(
                    self._check(
                        "ui_target_in_csproj",
                        "pass",
                        "csproj UI build target detected.",
                        str(csproj_path),
                        "",
                    )
                )
            else:
                checks.append(
                    self._check(
                        "ui_target_in_csproj",
                        "warn" if not strict else "fail",
                        "Hybrid project missing csproj UI build target.",
                        str(csproj_path) if csproj_path else str(root),
                        "Add a BuildUI target to run npm build and copy artifacts.",
                    )
                )

        if readme_file.exists() and "compatibility" in readme_text.lower():
            checks.append(self._check("readme_compatibility", "pass", "README compatibility section found.", str(readme_file), ""))
        else:
            checks.append(
                self._check(
                    "readme_compatibility",
                    "warn",
                    "README compatibility section not found.",
                    str(readme_file),
                    "Document supported Cities2/game versions and known incompatibilities.",
                )
            )

        dependencies = self._extract_dependencies(csproj_text) if csproj_text else []
        game_version = self._extract_xml_value(csproj_text, "GameVersion") if csproj_text else ""
        conflicts = self._extract_conflicts(readme_text)

        return {
            "ok": True,
            "project_dir": str(root),
            "profile": project_profile,
            "strict": bool(strict),
            "score": self._score(checks),
            "checks": checks,
            "compatibility": {
                "game_version": game_version,
                "declared_dependencies": dependencies,
                "potential_conflicts": conflicts,
            },
        }
