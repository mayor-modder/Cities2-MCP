from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from cities2_mcp.build_runner import BuildRunner
from cities2_mcp.project_scaffold import ProjectScaffolder

ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="cities2-mcp-scaffold-"))
        self.scaffolder = ProjectScaffolder(self.tmp, templates_dir=ROOT / "cities2_mcp" / "templates")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_scaffold_csharp_replaces_tokens(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Token Test",
            template="cities2-csharp",
            target_dir=None,
            metadata={"display_name": "Token Test"},
            options={"include_harmony": True},
        )
        self.assertTrue(result["ok"])
        project_dir = Path(result["project_dir"])
        mod_cs = (project_dir / "Mod.cs").read_text(encoding="utf-8")
        self.assertNotIn("{{", mod_cs)
        self.assertTrue((project_dir / "Setting.cs").exists())
        self.assertTrue((project_dir / "LocaleEN.cs").exists())

    def test_scaffold_csharp_template_keeps_langversion_after_toolchain_imports(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Build Ready",
            template="cities2-csharp",
            target_dir=None,
            metadata={},
            options={},
        )

        project_dir = Path(result["project_dir"])
        csproj = (project_dir / "build-ready.csproj").read_text(encoding="utf-8")

        self.assertIn('<Reference Include="Unity.Collections">', csproj)
        self.assertLess(csproj.index("Mod.targets"), csproj.rindex("<LangVersion>"))

    def test_default_game_version_comes_from_bundled_manifest(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Version Default",
            template="cities2-csharp",
            target_dir=None,
            metadata={},
            options={},
        )

        project_dir = Path(result["project_dir"])
        csproj = (project_dir / "version-default.csproj").read_text(encoding="utf-8")

        self.assertEqual(result["game_version"], "1.5.*")
        self.assertEqual(result["game_version_source"], "bundled_corpus_manifest")
        self.assertEqual(result["bundled_game_version"], "1.5.10f1")
        self.assertEqual(result["metadata"]["game_version"], "1.5.*")
        self.assertIn("<GameVersion>1.5.*</GameVersion>", csproj)

    def test_default_game_version_can_fall_back_to_patch_index(self) -> None:
        data_dir = self.tmp / "data-with-patch-index"
        index_dir = data_dir / "index"
        index_dir.mkdir(parents=True)
        (index_dir / "chunks.jsonl").write_text(
            json.dumps(
                {
                    "page_id": "patches",
                    "title": "Patches",
                    "section": "Introduction",
                    "text": "Version history\n\n1.6.2f1 2026-07-01 Patch\n\n1.5.9f1 2026-05-27 Patch",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        scaffolder = ProjectScaffolder(
            self.tmp / "patch-index-workspace",
            templates_dir=ROOT / "cities2_mcp" / "templates",
            data_dir=data_dir,
        )

        result = scaffolder.scaffold_project(
            name="Patch Index Version",
            template="cities2-csharp",
            target_dir=None,
            metadata={},
            options={},
        )

        self.assertEqual(result["game_version"], "1.6.*")
        self.assertEqual(result["game_version_source"], "bundled_corpus_patch_index")
        self.assertEqual(result["bundled_game_version"], "1.6.2f1")

    def test_default_game_version_prefers_manifest_metadata(self) -> None:
        data_dir = self.tmp / "data-with-version"
        data_dir.mkdir()
        (data_dir / "manifest.json").write_text(
            json.dumps({"current_game_version": "1.6.2f1"}),
            encoding="utf-8",
        )
        scaffolder = ProjectScaffolder(
            self.tmp / "manifest-workspace",
            templates_dir=ROOT / "cities2_mcp" / "templates",
            data_dir=data_dir,
        )

        result = scaffolder.scaffold_project(
            name="Manifest Version",
            template="cities2-csharp",
            target_dir=None,
            metadata={},
            options={},
        )

        self.assertEqual(result["game_version"], "1.6.*")
        self.assertEqual(result["game_version_source"], "bundled_corpus_manifest")
        self.assertEqual(result["bundled_game_version"], "1.6.2f1")

    def test_explicit_game_version_metadata_overrides_default(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Explicit Version",
            template="cities2-csharp",
            target_dir=None,
            metadata={"game_version": "1.6.*"},
            options={},
        )

        self.assertEqual(result["game_version"], "1.6.*")
        self.assertEqual(result["game_version_source"], "metadata")

    def test_default_game_version_falls_back_when_corpus_metadata_missing(self) -> None:
        empty_data_dir = self.tmp / "empty-data"
        empty_data_dir.mkdir()
        scaffolder = ProjectScaffolder(
            self.tmp / "fallback-workspace",
            templates_dir=ROOT / "cities2_mcp" / "templates",
            data_dir=empty_data_dir,
        )

        result = scaffolder.scaffold_project(
            name="Fallback Version",
            template="cities2-csharp",
            target_dir=None,
            metadata={},
            options={},
        )

        self.assertEqual(result["game_version"], "1.5.*")
        self.assertEqual(result["game_version_source"], "package_fallback")

    def test_scaffold_warns_when_installed_game_version_is_newer_than_bundle(self) -> None:
        data_dir = self.tmp / "data-with-current-version"
        data_dir.mkdir()
        (data_dir / "manifest.json").write_text(
            json.dumps({"current_game_version": "1.5.9f1"}),
            encoding="utf-8",
        )
        scaffolder = ProjectScaffolder(
            self.tmp / "newer-game-workspace",
            templates_dir=ROOT / "cities2_mcp" / "templates",
            data_dir=data_dir,
            installed_game_version="1.6.1f1",
            installed_game_version_source="test",
        )

        result = scaffolder.scaffold_project(
            name="Newer Game",
            template="cities2-csharp",
            target_dir=None,
            metadata={},
            options={},
        )

        self.assertEqual(result["installed_game_version"], "1.6.1f1")
        self.assertEqual(result["installed_game_version_source"], "test")
        self.assertEqual(result["bundled_game_version"], "1.5.9f1")
        self.assertIn("check for an updated Cities2-MCP release", "\n".join(result["warnings"]))

    def test_scaffold_warns_when_installed_steam_build_is_newer_than_bundle(self) -> None:
        data_dir = self.tmp / "data-with-steam-build"
        data_dir.mkdir()
        (data_dir / "manifest.json").write_text(
            json.dumps({"current_game_version": "1.5.9f1", "steam_build_id": "100"}),
            encoding="utf-8",
        )
        scaffolder = ProjectScaffolder(
            self.tmp / "newer-build-workspace",
            templates_dir=ROOT / "cities2_mcp" / "templates",
            data_dir=data_dir,
            installed_steam_build_id="101",
            installed_steam_build_id_source="steam",
        )

        result = scaffolder.scaffold_project(
            name="Newer Build",
            template="cities2-csharp",
            target_dir=None,
            metadata={},
            options={},
        )

        self.assertEqual(result["installed_steam_build_id"], "101")
        self.assertEqual(result["bundled_steam_build_id"], "100")
        self.assertIn("Steam build 101", "\n".join(result["warnings"]))

    def test_files_created_excludes_optionally_removed_files(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="No Settings",
            template="cities2-csharp",
            target_dir=None,
            metadata={},
            options={"include_settings": False, "include_localization": True},
        )

        project_dir = Path(result["project_dir"])
        created_rel = {str(Path(path).relative_to(project_dir)) for path in result["files_created"]}

        self.assertFalse((project_dir / "Setting.cs").exists())
        self.assertFalse((project_dir / "LocaleEN.cs").exists())
        self.assertNotIn("Setting.cs", created_rel)
        self.assertNotIn("LocaleEN.cs", created_rel)
        self.assertIn(
            "Localization files were not added because settings support is disabled.",
            result["warnings"],
        )

    def test_write_path_escape_is_rejected(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Path Test",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )
        with self.assertRaises(ValueError):
            self.scaffolder.write_project_file(
                project_dir=result["project_dir"],
                relative_path="../../outside.txt",
                content="x",
                mode="upsert",
            )

    def test_invalid_mode_rejected(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Mode Test",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )
        with self.assertRaises(ValueError):
            self.scaffolder.write_project_file(
                project_dir=result["project_dir"],
                relative_path="a.txt",
                content="x",
                mode="append",
            )

    def test_absolute_path_inside_additional_workspace_is_allowed(self) -> None:
        secondary = self.tmp / "secondary"
        secondary.mkdir()
        scaffolder = ProjectScaffolder(
            self.tmp,
            templates_dir=ROOT / "server" / "templates",
            additional_workspaces=[secondary],
        )

        resolved = scaffolder.resolve_workspace_path(str(secondary / "mod"))

        self.assertEqual(resolved, (secondary / "mod").resolve())

    def test_package_default_output_stays_inside_project(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Package Output",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )
        project_dir = Path(result["project_dir"])

        package = BuildRunner(self.scaffolder).package_project(
            project_dir=str(project_dir),
            output_dir=None,
            package_name=None,
            exclude_globs=None,
        )

        self.assertEqual(Path(package["package_path"]).parent, project_dir / "packages")
        self.assertFalse((self.tmp / "packages").exists())

    def test_package_project_excludes_generated_dependency_and_output_dirs(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Package Clean",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )
        project_dir = Path(result["project_dir"])
        (project_dir / "node_modules" / "left-pad").mkdir(parents=True)
        (project_dir / "node_modules" / "left-pad" / "index.js").write_text("module.exports = 1\n", encoding="utf-8")
        (project_dir / "packages").mkdir(exist_ok=True)
        (project_dir / "packages" / "old.zip").write_bytes(b"old")

        package = BuildRunner(self.scaffolder).package_project(
            project_dir=str(project_dir),
            output_dir=None,
            package_name=None,
            exclude_globs=None,
        )

        with zipfile.ZipFile(package["package_path"]) as zf:
            names = set(zf.namelist())

        self.assertIn("package.json", names)
        self.assertIn("src/index.tsx", names)
        self.assertNotIn("node_modules/left-pad/index.js", names)
        self.assertNotIn("packages/old.zip", names)
        self.assertNotIn("packages/package-clean.zip", names)

    def test_package_project_rejects_package_name_that_escapes_output_dir(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Package Escape",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )
        project_dir = Path(result["project_dir"])

        for package_name in ("../escape", "..\\escape", "nested/name", "nested\\name"):
            with self.subTest(package_name=package_name):
                with self.assertRaises(ValueError):
                    BuildRunner(self.scaffolder).package_project(
                        project_dir=str(project_dir),
                        output_dir=None,
                        package_name=package_name,
                        exclude_globs=None,
                    )

        self.assertFalse((project_dir.parent / "escape.zip").exists())

    def test_package_project_rejects_absolute_package_name(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Package Absolute",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )
        project_dir = Path(result["project_dir"])

        with self.assertRaises(ValueError):
            BuildRunner(self.scaffolder).package_project(
                project_dir=str(project_dir),
                output_dir=None,
                package_name=str(self.tmp / "escape"),
                exclude_globs=None,
            )

    def test_package_project_rejects_parent_or_absolute_exclude_globs(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Package Glob",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )
        project_dir = Path(result["project_dir"])

        for pattern in ("../*.txt", "..\\*.txt", str(self.tmp / "*.txt")):
            with self.subTest(pattern=pattern):
                with self.assertRaises(ValueError):
                    BuildRunner(self.scaffolder).package_project(
                        project_dir=str(project_dir),
                        output_dir=None,
                        package_name=None,
                        exclude_globs=[pattern],
                    )

    def test_package_project_zip_entries_are_project_relative(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Package Relative",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )
        project_dir = Path(result["project_dir"])

        package = BuildRunner(self.scaffolder).package_project(
            project_dir=str(project_dir),
            output_dir=None,
            package_name=None,
            exclude_globs=None,
        )

        with zipfile.ZipFile(package["package_path"]) as zf:
            for name in zf.namelist():
                parts = Path(name).parts
                self.assertFalse(Path(name).is_absolute(), name)
                self.assertNotIn("..", parts, name)
                self.assertFalse(Path(name).drive, name)

    def _symlink_or_skip(self, link: Path, target: Path, *, target_is_directory: bool = False) -> None:
        try:
            link.symlink_to(target, target_is_directory=target_is_directory)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlink creation is not available in this environment: {exc}")

    def _junction_or_skip(self, link: Path, target: Path) -> None:
        if os.name != "nt":
            self.skipTest("Windows junction coverage only applies on Windows")
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            self.skipTest(f"junction creation is not available in this environment: {result.stderr or result.stdout}")

    def test_package_project_rejects_outside_symlink_file(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Package Link File",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )
        project_dir = Path(result["project_dir"])
        outside = self.tmp / "outside-secret.txt"
        outside.write_text("outside secret", encoding="utf-8")
        self._symlink_or_skip(project_dir / "src" / "outside-secret.txt", outside)

        with self.assertRaises(ValueError):
            BuildRunner(self.scaffolder).package_project(
                project_dir=str(project_dir),
                output_dir=None,
                package_name=None,
                exclude_globs=None,
            )

    def test_package_project_rejects_outside_symlink_directory(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Package Link Dir",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )
        project_dir = Path(result["project_dir"])
        outside = self.tmp / "outside-dir"
        outside.mkdir()
        (outside / "secret.txt").write_text("outside secret", encoding="utf-8")
        self._symlink_or_skip(project_dir / "linked-outside", outside, target_is_directory=True)

        with self.assertRaises(ValueError):
            BuildRunner(self.scaffolder).package_project(
                project_dir=str(project_dir),
                output_dir=None,
                package_name=None,
                exclude_globs=None,
            )

    def test_package_project_prunes_outside_junction_before_descent(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Package Junction",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )
        project_dir = Path(result["project_dir"])
        outside = self.tmp / "outside-junction"
        outside.mkdir()
        (outside / "secret.txt").write_text("outside secret", encoding="utf-8")
        self._junction_or_skip(project_dir / "junction-outside", outside)

        package = BuildRunner(self.scaffolder).package_project(
            project_dir=str(project_dir),
            output_dir=None,
            package_name=None,
            exclude_globs=None,
        )

        with zipfile.ZipFile(package["package_path"]) as zf:
            names = set(zf.namelist())

        self.assertNotIn("junction-outside/secret.txt", names)

    def test_package_project_rejects_hardlinked_file(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Package Hardlink",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )
        project_dir = Path(result["project_dir"])
        outside = self.tmp / "outside-hardlink-secret.txt"
        outside.write_text("outside secret", encoding="utf-8")
        linked = project_dir / "src" / "outside-hardlink-secret.txt"
        try:
            os.link(outside, linked)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"hardlink creation is not available in this environment: {exc}")

        with self.assertRaises(ValueError):
            BuildRunner(self.scaffolder).package_project(
                project_dir=str(project_dir),
                output_dir=None,
                package_name=None,
                exclude_globs=None,
            )

    def test_list_project_tree_rejects_parent_glob_traversal(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Tree Traversal",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )

        with self.assertRaises(ValueError):
            self.scaffolder.list_project_tree(
                project_dir=result["project_dir"],
                glob="../*.txt",
            )

    def test_list_project_tree_rejects_absolute_glob(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Tree Absolute",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )

        with self.assertRaises(ValueError):
            self.scaffolder.list_project_tree(
                project_dir=result["project_dir"],
                glob=str(self.tmp / "*.txt"),
            )

    def test_list_project_tree_prunes_outside_junction_before_descent(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Tree Junction",
            template="cities2-ui",
            target_dir=None,
            metadata={},
            options={},
        )
        project_dir = Path(result["project_dir"])
        outside = self.tmp / "outside-tree-junction"
        outside.mkdir()
        (outside / "secret.txt").write_text("outside secret", encoding="utf-8")
        self._junction_or_skip(project_dir / "junction-outside", outside)

        original_is_file = Path.is_file

        def fail_if_junction_child(path: Path) -> bool:
            if "junction-outside" in path.parts:
                raise AssertionError(f"list_project_tree descended into junction child: {path}")
            return original_is_file(path)

        with mock.patch.object(Path, "is_file", fail_if_junction_child):
            payload = self.scaffolder.list_project_tree(project_dir=result["project_dir"])
        rels = {item["relative"].replace("\\", "/") for item in payload["files"]}

        self.assertNotIn("junction-outside/secret.txt", rels)

    def test_scaffold_escapes_metadata_in_code_and_xml_templates(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Metadata Escape",
            template="cities2-hybrid",
            target_dir=None,
            metadata={
                "display_name": 'Breaker" <tag> &',
                "short_description": "Short <description> & details",
            },
            options={},
        )
        project_dir = Path(result["project_dir"])

        locale_cs = (project_dir / "LocaleEN.cs").read_text(encoding="utf-8")
        index_ts = (project_dir / "ui" / "src" / "index.tsx").read_text(encoding="utf-8")
        csproj = (project_dir / "metadata-escape.csproj").read_text(encoding="utf-8")
        publish = (project_dir / "Properties" / "PublishConfiguration.xml").read_text(encoding="utf-8")

        self.assertIn('Breaker\\" <tag> &', locale_cs)
        self.assertIn('Breaker\\" <tag> &', index_ts)
        self.assertIn("<DisplayName>Breaker&quot; &lt;tag&gt; &amp;</DisplayName>", csproj)
        self.assertIn("<ShortDescription>Short &lt;description&gt; &amp; details</ShortDescription>", publish)

    def test_scaffold_rejects_invalid_identifier_metadata(self) -> None:
        with self.assertRaises(ValueError):
            self.scaffolder.scaffold_project(
                name="Metadata Inject",
                template="cities2-csharp",
                target_dir=None,
                metadata={"root_namespace": 'Bad.Namespace; System.IO.File.Delete("x")'},
                options={},
            )

    def test_scaffold_allows_dotted_root_namespace_metadata(self) -> None:
        result = self.scaffolder.scaffold_project(
            name="Dotted Namespace",
            template="cities2-csharp",
            target_dir=None,
            metadata={"root_namespace": "Company.ModName"},
            options={},
        )
        project_dir = Path(result["project_dir"])
        mod_cs = (project_dir / "Mod.cs").read_text(encoding="utf-8")

        self.assertIn("namespace Company.ModName;", mod_cs)

    def test_build_runner_adds_common_windows_tool_dirs_to_subprocess_path(self) -> None:
        program_files = self.tmp / "Program Files"
        node_dir = program_files / "nodejs"
        dotnet_dir = program_files / "dotnet"
        node_dir.mkdir(parents=True)
        dotnet_dir.mkdir()
        env = {
            "PATH": str(self.tmp / "existing"),
            "PROGRAMFILES": str(program_files),
            "PROGRAMFILES(X86)": "",
            "LOCALAPPDATA": "",
        }

        subprocess_env = BuildRunner._subprocess_env(env=env, platform="win32")
        path_parts = subprocess_env["PATH"].split(os.pathsep)

        self.assertIn(str(node_dir), path_parts)
        self.assertIn(str(dotnet_dir), path_parts)
        self.assertEqual(1, path_parts.count(str(node_dir)))

    def test_build_runner_resolves_tools_from_augmented_path(self) -> None:
        program_files = self.tmp / "Program Files"
        node_dir = program_files / "nodejs"
        node_dir.mkdir(parents=True)
        npm_cmd = node_dir / "npm.cmd"
        npm_cmd.write_text("@echo off\n", encoding="utf-8")
        env = {
            "PATH": "",
            "PATHEXT": ".COM;.EXE;.BAT;.CMD",
            "PROGRAMFILES": str(program_files),
            "PROGRAMFILES(X86)": "",
            "LOCALAPPDATA": "",
        }

        subprocess_env = BuildRunner._subprocess_env(env=env, platform="win32")
        resolved = BuildRunner._resolve_command_argv(["npm", "--version"], subprocess_env, platform="win32")

        self.assertEqual(str(npm_cmd).casefold(), resolved[0].casefold())
        self.assertEqual(["--version"], resolved[1:])


if __name__ == "__main__":
    unittest.main()
