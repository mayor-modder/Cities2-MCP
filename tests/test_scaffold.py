from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from project_scaffold import ProjectScaffolder  # noqa: E402


class ScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="cities2-mcp-scaffold-"))
        self.scaffolder = ProjectScaffolder(self.tmp, templates_dir=ROOT / "server" / "templates")

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


if __name__ == "__main__":
    unittest.main()
