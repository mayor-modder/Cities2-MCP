from __future__ import annotations

import json
import os
import re
import stat
from html import escape
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Dict, List, Optional, Sequence

JSON = Dict[str, Any]
FALLBACK_GAME_VERSION_PATTERN = "1.5.*"
IDENTIFIER_SEGMENT_RE = r"[A-Za-z_][A-Za-z0-9_]*"
IDENTIFIER_RE = re.compile(f"^{IDENTIFIER_SEGMENT_RE}$")
NAMESPACE_RE = re.compile(f"^{IDENTIFIER_SEGMENT_RE}(?:\\.{IDENTIFIER_SEGMENT_RE})*$")
PROJECT_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ProjectScaffolder:
    TEMPLATE_VALUES = {"cities2-csharp", "cities2-ui", "cities2-hybrid"}
    MODE_VALUES = {"create", "replace", "upsert"}

    def __init__(
        self,
        workspace: Path,
        templates_dir: Optional[Path] = None,
        additional_workspaces: Optional[Sequence[Path]] = None,
        data_dir: Optional[Path] = None,
        installed_game_version: Optional[str] = None,
        installed_game_version_source: Optional[str] = None,
        installed_steam_build_id: Optional[str] = None,
        installed_steam_build_id_source: Optional[str] = None,
    ) -> None:
        self.workspace = workspace.resolve()
        self.allowed_workspaces = self._build_allowed_workspaces(additional_workspaces or [])
        self.projects_root = self.workspace / "mods"
        self.projects_root.mkdir(parents=True, exist_ok=True)
        package_dir = Path(__file__).resolve().parent
        self.templates_dir = (templates_dir or (package_dir / "templates")).resolve()
        self.data_dir = (data_dir or (package_dir / "data")).resolve()
        env_game_version = os.environ.get("CITIES2_GAME_VERSION", "").strip()
        env_steam_build_id = os.environ.get("CITIES2_STEAM_BUILD_ID", "").strip()
        self.installed_game_version = str(installed_game_version or env_game_version).strip()
        self.installed_game_version_source = str(
            installed_game_version_source or ("CITIES2_GAME_VERSION" if env_game_version else "")
        ).strip()
        self.installed_steam_build_id = self._normalize_steam_build_id(installed_steam_build_id or env_steam_build_id)
        self.installed_steam_build_id_source = str(
            installed_steam_build_id_source or ("CITIES2_STEAM_BUILD_ID" if env_steam_build_id else "")
        ).strip()

    def _build_allowed_workspaces(self, additional_workspaces: Sequence[Path]) -> List[Path]:
        workspaces: List[Path] = []
        for workspace in [self.workspace, *additional_workspaces]:
            resolved = Path(workspace).resolve()
            if resolved not in workspaces:
                workspaces.append(resolved)
        return workspaces

    def _is_within_allowed_workspace(self, path: Path) -> bool:
        return any(workspace == path or workspace in path.parents for workspace in self.allowed_workspaces)

    def resolve_workspace_path(self, rel_or_abs: str) -> Path:
        p = Path(rel_or_abs)
        if not p.is_absolute():
            p = self.workspace / p
        rp = p.resolve()
        if not self._is_within_allowed_workspace(rp):
            allowed = ", ".join(str(workspace) for workspace in self.allowed_workspaces)
            raise ValueError(f"Path must stay inside configured workspaces: {allowed}")
        return rp

    @staticmethod
    def is_within_path(path: Path, root: Path) -> bool:
        resolved_path = path.resolve()
        resolved_root = root.resolve()
        return resolved_path == resolved_root or resolved_root in resolved_path.parents

    @staticmethod
    def validate_relative_glob(pattern: str, *, field_name: str = "glob") -> str:
        value = str(pattern or "").strip() or "**/*"
        posix = PurePosixPath(value)
        windows = PureWindowsPath(value)
        if posix.is_absolute() or windows.is_absolute() or windows.drive:
            raise ValueError(f"{field_name} must be a relative pattern inside the project")
        if ".." in posix.parts or ".." in windows.parts:
            raise ValueError(f"{field_name} must not contain parent directory traversal")
        return value

    @staticmethod
    def is_reparse_point(path: Path) -> bool:
        is_junction = getattr(path, "is_junction", None)
        if callable(is_junction) and is_junction():
            return True
        try:
            attributes = getattr(path.lstat(), "st_file_attributes", 0)
        except OSError:
            return False
        return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))

    @staticmethod
    def _relative_glob_matches(relative: str, pattern: str) -> bool:
        rel_path = PurePosixPath(relative)
        if pattern == "**/*":
            return True
        if pattern.startswith("**/") and rel_path.match(pattern[3:]):
            return True
        return rel_path.match(pattern)

    @classmethod
    def _walk_project_files(cls, root: Path) -> List[Path]:
        files: List[Path] = []
        stack = [root]
        while stack:
            current = stack.pop()
            for child in sorted(current.iterdir()):
                if cls.is_reparse_point(child):
                    continue
                if child.is_dir():
                    stack.append(child)
                elif child.is_file():
                    files.append(child)
        return files

    @staticmethod
    def slug(name: str) -> str:
        s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower())
        return re.sub(r"-+", "-", s).strip("-") or "cities2-mod"

    @staticmethod
    def to_namespace(slug: str) -> str:
        parts = [p for p in re.split(r"[^a-zA-Z0-9]+", slug) if p]
        if not parts:
            return "Cities2Mod"
        return "".join(p[:1].upper() + p[1:] for p in parts)

    @staticmethod
    def _version_pattern(value: object) -> str:
        text = str(value or "")
        match = re.search(r"\b(\d+)\.(\d+)(?:\.(?:\d+|[xX])(?:f\d+)?)?\b", text)
        if not match:
            return ""
        return f"{match.group(1)}.{match.group(2)}.*"

    @staticmethod
    def _version_score(value: str) -> tuple[int, int, int, int]:
        match = re.search(r"\b(\d+)\.(\d+)(?:\.(\d+|[xX]))?(?:f(\d+))?\b", value)
        if not match:
            return (-1, -1, -1, -1)
        major = int(match.group(1))
        if major > 9:
            return (-1, -1, -1, -1)
        patch_text = match.group(3)
        patch = -1 if patch_text is None or patch_text.lower() == "x" else int(patch_text)
        fix = -1 if match.group(4) is None else int(match.group(4))
        return (major, int(match.group(2)), patch, fix)

    @classmethod
    def _best_version(cls, values: Sequence[object], *, require_game_patch_format: bool = False) -> str:
        pattern = (
            r"\b\d+\.\d+\.(?:\d+f\d+|[xX])\b"
            if require_game_patch_format
            else r"\b\d+\.\d+(?:\.(?:\d+|[xX]))?(?:f\d+)?\b"
        )
        versions: List[str] = []
        for value in values:
            versions.extend(re.findall(pattern, str(value or "")))
        if not versions:
            return ""
        best = max(versions, key=cls._version_score)
        if cls._version_score(best) == (-1, -1, -1, -1):
            return ""
        return best

    @classmethod
    def _best_version_pattern(cls, values: Sequence[object], *, require_game_patch_format: bool = False) -> str:
        best = cls._best_version(values, require_game_patch_format=require_game_patch_format)
        if not best:
            return ""
        return cls._version_pattern(best)

    @classmethod
    def _is_newer_version(cls, left: str, right: str) -> bool:
        left_score = cls._version_score(left)
        right_score = cls._version_score(right)
        if left_score == (-1, -1, -1, -1) or right_score == (-1, -1, -1, -1):
            return False
        return left_score > right_score

    @staticmethod
    def _manifest_version_candidates(value: object) -> List[object]:
        candidates: List[object] = []
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key).casefold()
                if ("game" in key_text or "patch" in key_text) and "version" in key_text:
                    candidates.append(item)
                if isinstance(item, (dict, list)):
                    candidates.extend(ProjectScaffolder._manifest_version_candidates(item))
        elif isinstance(value, list):
            for item in value:
                candidates.extend(ProjectScaffolder._manifest_version_candidates(item))
        return candidates

    @staticmethod
    def _normalize_steam_build_id(value: object) -> str:
        match = re.search(r"\b\d+\b", str(value or ""))
        return match.group(0) if match else ""

    @staticmethod
    def _manifest_steam_build_candidates(value: object) -> List[object]:
        candidates: List[object] = []
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key).casefold().replace("-", "_")
                if key_text in {"steam_build_id", "steam_buildid", "build_id", "buildid"}:
                    candidates.append(item)
                if isinstance(item, (dict, list)):
                    candidates.extend(ProjectScaffolder._manifest_steam_build_candidates(item))
        elif isinstance(value, list):
            for item in value:
                candidates.extend(ProjectScaffolder._manifest_steam_build_candidates(item))
        return candidates

    @staticmethod
    def _is_newer_steam_build(left: str, right: str) -> bool:
        try:
            return int(left) > int(right)
        except ValueError:
            return False

    def _read_manifest(self) -> JSON:
        manifest_path = self.data_dir / "manifest.json"
        if not manifest_path.exists():
            return {}
        try:
            value = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except Exception:
            return {}
        return value if isinstance(value, dict) else {}

    def _game_version_from_manifest(self) -> str:
        manifest = self._read_manifest()
        if not manifest:
            return ""
        return self._best_version_pattern(self._manifest_version_candidates(manifest))

    def _latest_game_version_from_manifest(self) -> str:
        manifest = self._read_manifest()
        if not manifest:
            return ""
        return self._best_version(self._manifest_version_candidates(manifest))

    def _steam_build_id_from_manifest(self) -> str:
        manifest = self._read_manifest()
        if not manifest:
            return ""
        for candidate in self._manifest_steam_build_candidates(manifest):
            build_id = self._normalize_steam_build_id(candidate)
            if build_id:
                return build_id
        return ""

    def _game_version_from_patch_index(self) -> str:
        return self._game_version_from_patch_index_value(pattern=True)

    def _latest_game_version_from_patch_index(self) -> str:
        return self._game_version_from_patch_index_value(pattern=False)

    def _game_version_from_patch_index_value(self, *, pattern: bool) -> str:
        chunks_path = self.data_dir / "index" / "chunks.jsonl"
        if not chunks_path.exists():
            return ""
        candidates: List[object] = []
        try:
            with chunks_path.open("r", encoding="utf-8-sig") as handle:
                for line in handle:
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    page_id = str(row.get("page_id", "")).casefold()
                    title = str(row.get("title", "")).casefold()
                    if page_id == "patches" or page_id.startswith("patch-") or title.startswith("patch"):
                        candidates.append(row.get("section", ""))
                        candidates.append(row.get("text", ""))
        except OSError:
            return ""
        if pattern:
            return self._best_version_pattern(candidates, require_game_patch_format=True)
        return self._best_version(candidates, require_game_patch_format=True)

    def default_game_version_info(self) -> JSON:
        manifest_version = self._game_version_from_manifest()
        if manifest_version:
            return {
                "game_version": manifest_version,
                "game_version_source": "bundled_corpus_manifest",
                "bundled_game_version": self._latest_game_version_from_manifest() or manifest_version,
                "bundled_steam_build_id": self._steam_build_id_from_manifest(),
            }
        patch_index_version = self._game_version_from_patch_index()
        if patch_index_version:
            return {
                "game_version": patch_index_version,
                "game_version_source": "bundled_corpus_patch_index",
                "bundled_game_version": self._latest_game_version_from_patch_index() or patch_index_version,
                "bundled_steam_build_id": self._steam_build_id_from_manifest(),
            }
        return {
            "game_version": FALLBACK_GAME_VERSION_PATTERN,
            "game_version_source": "package_fallback",
            "bundled_game_version": FALLBACK_GAME_VERSION_PATTERN,
            "bundled_steam_build_id": self._steam_build_id_from_manifest(),
        }

    def _installed_game_warning(self, game_version: str, default_game_version_info: JSON) -> str:
        bundled_game_version = str(default_game_version_info.get("bundled_game_version", "")).strip()
        bundled_steam_build_id = self._normalize_steam_build_id(default_game_version_info.get("bundled_steam_build_id", ""))

        installed_evidence = ""
        bundled_evidence = ""
        if self.installed_game_version and self._is_newer_version(self.installed_game_version, bundled_game_version):
            installed_source = f" from {self.installed_game_version_source}" if self.installed_game_version_source else ""
            installed_evidence = f"installed game version {self.installed_game_version}{installed_source}"
            bundled_evidence = f"bundled knowledge is current through {bundled_game_version}"
        elif (
            self.installed_steam_build_id
            and bundled_steam_build_id
            and self._is_newer_steam_build(self.installed_steam_build_id, bundled_steam_build_id)
        ):
            installed_source = f" from {self.installed_steam_build_id_source}" if self.installed_steam_build_id_source else ""
            installed_evidence = f"installed Steam build {self.installed_steam_build_id}{installed_source}"
            bundled_evidence = f"bundled Steam build is {bundled_steam_build_id}"

        if not installed_evidence:
            return ""
        return (
            f"Cities: Skylines II appears newer than this Cities2-MCP package ({installed_evidence}; "
            f"{bundled_evidence}). The project was still scaffolded with GameVersion {game_version}; "
            "check for an updated Cities2-MCP release or pass metadata.game_version explicitly if needed."
        )

    def _default_metadata(self, name: str, slug: str) -> JSON:
        game_version = self.default_game_version_info()["game_version"]
        return {
            "mod_id": "",
            "display_name": name,
            "short_description": f"{name} generated by Cities2-MCP modding tools.",
            "game_version": game_version,
            "github_url": "",
            "forum_url": "",
            "version": "0.1.0",
            "project_slug": slug,
            "root_namespace": ProjectScaffolder.to_namespace(slug),
        }

    @staticmethod
    def _merge_defaults(defaults: JSON, value: Optional[JSON]) -> JSON:
        out = dict(defaults)
        if value:
            for k, v in value.items():
                out[str(k)] = v
        return out

    @staticmethod
    def _validate_identifier(value: object, *, field_name: str) -> str:
        text = str(value or "").strip()
        if not IDENTIFIER_RE.fullmatch(text):
            raise ValueError(f"{field_name} must be a valid C# identifier")
        return text

    @staticmethod
    def _validate_namespace(value: object, *, field_name: str) -> str:
        text = str(value or "").strip()
        if not NAMESPACE_RE.fullmatch(text):
            raise ValueError(f"{field_name} must be a valid C# namespace")
        return text

    @staticmethod
    def _validate_project_slug(value: object) -> str:
        text = str(value or "").strip()
        if not PROJECT_SLUG_RE.fullmatch(text):
            raise ValueError("project_slug must be a lowercase path-safe slug")
        return text

    @staticmethod
    def _string_token(value: object) -> str:
        return json.dumps(str(value or ""), ensure_ascii=False)[1:-1]

    @staticmethod
    def _xml_token(value: object) -> str:
        return escape(str(value or ""), quote=True)

    @classmethod
    def _normalize_metadata(cls, metadata: JSON) -> JSON:
        normalized = dict(metadata)
        normalized["project_slug"] = cls._validate_project_slug(normalized.get("project_slug", ""))
        normalized["root_namespace"] = cls._validate_namespace(
            normalized.get("root_namespace", ""),
            field_name="root_namespace",
        )
        return normalized

    @staticmethod
    def _default_options(template: str) -> JSON:
        include_ui_pipeline = "auto"
        if template == "cities2-csharp":
            include_ui_pipeline = False
        elif template in {"cities2-ui", "cities2-hybrid"}:
            include_ui_pipeline = True
        return {
            "include_settings": True,
            "include_localization": True,
            "include_harmony": True,
            "include_ui_pipeline": include_ui_pipeline,
            "include_changelog": True,
        }

    @staticmethod
    def _bool_option(opts: JSON, key: str, default: bool) -> bool:
        value = opts.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off"}:
                return False
        return default

    @staticmethod
    def _xml_node(tag: str, value: str) -> str:
        if not value:
            return ""
        return f"    <{tag}>{escape(value)}</{tag}>\n"

    def _template_tokens(self, template: str, metadata: JSON, options: JSON) -> JSON:
        include_harmony = self._bool_option(options, "include_harmony", True)
        include_settings = self._bool_option(options, "include_settings", True)
        include_localization = self._bool_option(options, "include_localization", True)
        root_namespace = str(metadata.get("root_namespace", "Cities2Mod"))

        using_harmony = "using HarmonyLib;\n" if include_harmony else ""
        harmony_field = "    private Harmony? _harmony;\n" if include_harmony else ""
        setting_field = "    public static Setting? CurrentSetting;\n" if include_settings else ""

        onload_settings = ""
        ondispose_settings = ""
        onload_localization = ""
        if include_settings:
            onload_settings = (
                "        CurrentSetting = new Setting(this);\n"
                "        CurrentSetting.RegisterInOptionsUI();\n"
                f"        AssetDatabase.global.LoadSettings(nameof({root_namespace}), CurrentSetting, new Setting(this));\n\n"
            )
            ondispose_settings = (
                "        if (CurrentSetting != null)\n"
                "        {\n"
                "            CurrentSetting.UnregisterInOptionsUI();\n"
                "            CurrentSetting = null;\n"
                "        }\n"
            )
            if include_localization:
                onload_localization = (
                    '        GameManager.instance.localizationManager.AddSource("en-US", new LocaleEN(CurrentSetting));\n\n'
                )

        onload_harmony = ""
        ondispose_harmony = ""
        harmony_package_reference = ""
        if include_harmony:
            onload_harmony = (
                f'        _harmony = new Harmony("{root_namespace}.patches");\n'
                "        _harmony.PatchAll(typeof(Mod).Assembly);\n"
            )
            ondispose_harmony = f'        _harmony?.UnpatchAll("{root_namespace}.patches");\n        _harmony = null;\n'
            harmony_package_reference = (
                "  <ItemGroup>\n"
                '    <PackageReference Include="Lib.Harmony" Version="2.2.2" />\n'
                "  </ItemGroup>\n\n"
            )

        include_ui_pipeline_raw = options.get("include_ui_pipeline", "auto")
        include_ui_pipeline = include_ui_pipeline_raw
        if include_ui_pipeline_raw == "auto":
            include_ui_pipeline = template in {"cities2-ui", "cities2-hybrid"}
        if not isinstance(include_ui_pipeline, bool):
            include_ui_pipeline = template in {"cities2-ui", "cities2-hybrid"}

        ui_build_target = ""
        if include_ui_pipeline:
            ui_build_target = (
                "  <Target Name=\"BuildUI\" BeforeTargets=\"AfterBuild\">\n"
                '    <Exec Command="npm install" WorkingDirectory="$(ProjectDir)ui" />\n'
                '    <Exec Command="npm run build" WorkingDirectory="$(ProjectDir)ui" />\n'
                "  </Target>\n\n"
                "  <Target Name=\"CopyUIFiles\" AfterTargets=\"DeployWIP\">\n"
                "    <ItemGroup>\n"
                "      <UIFiles Include=\"ui\\dist\\**\\*.*\" />\n"
                "    </ItemGroup>\n"
                "    <Copy SourceFiles=\"@(UIFiles)\" DestinationFiles=\"@(UIFiles->'$(DeployDir)\\UI\\%(RecursiveDir)%(Filename)%(Extension)')\" />\n"
                "  </Target>\n"
            )

        return {
            "MOD_NAME": str(metadata.get("display_name", "")),
            "DISPLAY_NAME": str(metadata.get("display_name", "")),
            "DISPLAY_NAME_CS_STRING": self._string_token(metadata.get("display_name", "")),
            "DISPLAY_NAME_TS_STRING": self._string_token(metadata.get("display_name", "")),
            "DISPLAY_NAME_XML": self._xml_token(metadata.get("display_name", "")),
            "PROJECT_SLUG": str(metadata.get("project_slug", "")),
            "ROOT_NAMESPACE": str(metadata.get("root_namespace", "")),
            "SHORT_DESCRIPTION": str(metadata.get("short_description", "")),
            "SHORT_DESCRIPTION_XML": self._xml_token(metadata.get("short_description", "")),
            "GAME_VERSION": str(metadata.get("game_version", "")),
            "GAME_VERSION_XML": self._xml_token(metadata.get("game_version", "")),
            "VERSION": str(metadata.get("version", "0.1.0")),
            "VERSION_STRING": self._string_token(metadata.get("version", "0.1.0")),
            "VERSION_XML": self._xml_token(metadata.get("version", "0.1.0")),
            "USING_HARMONY": using_harmony,
            "HARMONY_FIELD": harmony_field,
            "SETTING_FIELD": setting_field,
            "ONLOAD_SETTINGS": onload_settings,
            "ONLOAD_LOCALIZATION": onload_localization,
            "ONLOAD_HARMONY": onload_harmony,
            "ONDISPOSE_SETTINGS": ondispose_settings,
            "ONDISPOSE_HARMONY": ondispose_harmony,
            "HARMONY_PACKAGE_REFERENCE": harmony_package_reference,
            "MOD_ID_NODE": self._xml_node("ModId", str(metadata.get("mod_id", ""))),
            "GITHUB_NODE": self._xml_node("GitHubLink", str(metadata.get("github_url", ""))),
            "FORUM_NODE": self._xml_node("ForumLink", str(metadata.get("forum_url", ""))),
            "UI_BUILD_TARGET": ui_build_target,
        }

    @staticmethod
    def _render_text(text: str, tokens: JSON) -> str:
        rendered = text
        for k, v in tokens.items():
            rendered = rendered.replace("{{" + str(k) + "}}", str(v))
        rendered = re.sub(r"\{\{[A-Z0-9_]+\}\}", "", rendered)
        return rendered

    @staticmethod
    def _is_text_file(path: Path) -> bool:
        if path.suffix.lower() in {
            ".cs",
            ".csproj",
            ".json",
            ".md",
            ".xml",
            ".txt",
            ".yml",
            ".yaml",
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".css",
            ".gitignore",
        }:
            return True
        return False

    def _copy_template_tree(self, template_dir: Path, target_dir: Path, tokens: JSON) -> List[str]:
        created: List[str] = []
        for src in sorted(template_dir.rglob("*")):
            rel = src.relative_to(template_dir)
            rel_str = str(rel).replace("__PROJECT_SLUG__", str(tokens["PROJECT_SLUG"]))
            dest = target_dir / rel_str
            resolved_dest = dest.resolve()
            if not self.is_within_path(resolved_dest, target_dir):
                raise ValueError("template path escapes target project directory")
            if src.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
                continue

            dest.parent.mkdir(parents=True, exist_ok=True)
            if self._is_text_file(src):
                content = src.read_text(encoding="utf-8")
                rendered = self._render_text(content, tokens)
                dest.write_text(rendered, encoding="utf-8")
            else:
                dest.write_bytes(src.read_bytes())
            created.append(str(dest))
        return created

    def scaffold_project(
        self,
        name: str,
        template: str,
        target_dir: Optional[str],
        metadata: Optional[JSON],
        options: Optional[JSON],
    ) -> JSON:
        if not str(name).strip():
            raise ValueError("name must be a non-empty string")
        if template not in self.TEMPLATE_VALUES:
            raise ValueError("template must be one of: cities2-csharp, cities2-ui, cities2-hybrid")

        slug = self.slug(name)
        root = self.resolve_workspace_path(target_dir) if target_dir else (self.projects_root / slug)
        template_dir = (self.templates_dir / template).resolve()
        if not template_dir.exists():
            raise FileNotFoundError(f"Missing template directory: {template_dir}")

        if root.exists() and any(root.iterdir()):
            raise ValueError(f"Target directory is not empty: {root}")
        root.mkdir(parents=True, exist_ok=True)

        metadata_game_version = str((metadata or {}).get("game_version", "")).strip()
        default_game_version_info = self.default_game_version_info()
        md = self._merge_defaults(self._default_metadata(name, slug), metadata)
        md = self._normalize_metadata(md)
        game_version_source = "metadata" if metadata_game_version else str(default_game_version_info["game_version_source"])
        opts = self._merge_defaults(self._default_options(template), options)
        tokens = self._template_tokens(template, md, opts)

        created = self._copy_template_tree(template_dir, root, tokens)
        warnings: List[str] = []
        installed_game_warning = self._installed_game_warning(str(md.get("game_version", "")), default_game_version_info)
        if installed_game_warning:
            warnings.append(installed_game_warning)

        include_changelog = self._bool_option(opts, "include_changelog", True)
        if not include_changelog:
            changelog = root / "CHANGELOG.md"
            if changelog.exists():
                changelog.unlink()

        include_settings = self._bool_option(opts, "include_settings", True)
        include_localization = self._bool_option(opts, "include_localization", True)
        if not include_settings:
            for p in [root / "Setting.cs", root / "LocaleEN.cs"]:
                if p.exists():
                    p.unlink()
            if include_localization:
                warnings.append("Localization files were not added because settings support is disabled.")
        elif not include_localization:
            locale_path = root / "LocaleEN.cs"
            if locale_path.exists():
                locale_path.unlink()

        include_ui_pipeline = opts.get("include_ui_pipeline", "auto")
        if template == "cities2-hybrid" and include_ui_pipeline is False:
            warnings.append("Hybrid template keeps UI folder; UI build target removed from csproj when include_ui_pipeline=false")

        created = [path for path in created if Path(path).exists()]

        recommended = []
        if template in {"cities2-ui", "cities2-hybrid"}:
            recommended.append("npm install")
            recommended.append("npm run build")
        if template in {"cities2-csharp", "cities2-hybrid"}:
            recommended.append("dotnet build -c Release")

        return {
            "ok": True,
            "name": name,
            "template": template,
            "project_slug": slug,
            "project_dir": str(root),
            "files_created": created,
            "warnings": warnings,
            "recommended_commands": recommended,
            "game_version": str(md.get("game_version", "")),
            "game_version_source": game_version_source,
            "bundled_game_version": str(default_game_version_info.get("bundled_game_version", "")),
            "bundled_steam_build_id": str(default_game_version_info.get("bundled_steam_build_id", "")),
            "installed_game_version": self.installed_game_version,
            "installed_game_version_source": self.installed_game_version_source,
            "installed_steam_build_id": self.installed_steam_build_id,
            "installed_steam_build_id_source": self.installed_steam_build_id_source,
            "metadata": md,
            "options": opts,
        }

    def write_project_file(self, project_dir: str, relative_path: str, content: str, mode: str = "upsert") -> JSON:
        if mode not in self.MODE_VALUES:
            raise ValueError("mode must be one of: create, replace, upsert")

        root = self.resolve_workspace_path(project_dir)
        target = (root / relative_path).resolve()
        if root not in target.parents and target != root:
            raise ValueError("relative_path escapes project dir")

        if mode == "create" and target.exists():
            return {"ok": False, "message": "File already exists", "path": str(target), "mode_applied": mode}
        if mode == "replace" and not target.exists():
            return {"ok": False, "message": "File not found", "path": str(target), "mode_applied": mode}

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {
            "ok": True,
            "path": str(target),
            "bytes": len(content.encode("utf-8")),
            "mode_applied": mode,
        }

    def list_project_tree(
        self,
        project_dir: str,
        glob: str = "**/*",
        include_hidden: bool = False,
        max_files: int = 2000,
    ) -> JSON:
        root = self.resolve_workspace_path(project_dir)
        max_files = max(1, min(10000, int(max_files)))

        files: List[JSON] = []
        safe_glob = self.validate_relative_glob(glob)
        for p in self._walk_project_files(root):
            resolved = p.resolve()
            if not self.is_within_path(resolved, root):
                continue
            rel = resolved.relative_to(root)
            rel_str = rel.as_posix()
            if not self._relative_glob_matches(rel_str, safe_glob):
                continue
            if not include_hidden and any(part.startswith(".") for part in rel.parts):
                continue
            files.append(
                {
                    "path": str(resolved),
                    "relative": str(rel),
                    "size": resolved.stat().st_size,
                }
            )
            if len(files) >= max_files:
                break

        return {
            "ok": True,
            "project_dir": str(root),
            "count": len(files),
            "truncated": len(files) >= max_files,
            "files": files,
        }

    def detect_profile(self, project_dir: str) -> str:
        root = self.resolve_workspace_path(project_dir)
        has_csproj = any(root.glob("*.csproj"))
        has_root_package = (root / "package.json").exists()
        has_ui_package = (root / "ui" / "package.json").exists()

        if has_csproj and has_ui_package:
            return "cities2-hybrid"
        if has_csproj:
            return "cities2-csharp"
        if has_root_package:
            return "cities2-ui"
        return "unknown"

    def find_primary_csproj(self, root: Path) -> Optional[Path]:
        csprojs = sorted(root.glob("*.csproj"))
        return csprojs[0] if csprojs else None


def json_dumps_pretty(payload: JSON) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
