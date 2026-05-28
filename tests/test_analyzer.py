from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from cities2_mcp.project_analyzer import ProjectAnalyzer
from cities2_mcp.project_scaffold import ProjectScaffolder

ROOT = Path(__file__).resolve().parents[1]


class AnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="cities2-mcp-analyze-"))
        self.scaffolder = ProjectScaffolder(self.tmp, templates_dir=ROOT / "cities2_mcp" / "templates")
        self.analyzer = ProjectAnalyzer(self.scaffolder)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_analyze_scaffold_passes_core_checks(self) -> None:
        scaffold = self.scaffolder.scaffold_project(
            name="Analyze Pass",
            template="cities2-csharp",
            target_dir=None,
            metadata={},
            options={},
        )
        result = self.analyzer.analyze_project(scaffold["project_dir"], profile="auto", strict=True)
        self.assertTrue(result["ok"])
        self.assertGreater(result["score"], 50)
        ids = {c["id"] for c in result["checks"]}
        self.assertIn("metadata_complete", ids)

    def test_analyze_broken_project_fails_publish_config(self) -> None:
        project = self.tmp / "mods" / "broken"
        project.mkdir(parents=True)
        (project / "broken.csproj").write_text("<Project Sdk=\"Microsoft.NET.Sdk\"></Project>\n", encoding="utf-8")
        (project / "Mod.cs").write_text("public class Mod {}\n", encoding="utf-8")
        result = self.analyzer.analyze_project(str(project), profile="cities2-csharp", strict=True)
        self.assertTrue(result["ok"])
        statuses = {c["id"]: c["status"] for c in result["checks"]}
        self.assertEqual(statuses.get("publish_config"), "fail")

    def test_analyze_project_flags_common_compile_blockers(self) -> None:
        scaffold = self.scaffolder.scaffold_project(
            name="Compile Blockers",
            template="cities2-csharp",
            target_dir=None,
            metadata={},
            options={},
        )
        project = Path(scaffold["project_dir"])
        csproj = project / "compile-blockers.csproj"
        csproj_text = csproj.read_text(encoding="utf-8")
        csproj_text = csproj_text.replace(
            "  <PropertyGroup>\n    <LangVersion>11.0</LangVersion>\n  </PropertyGroup>\n\n",
            "",
        )
        csproj_text = csproj_text.replace(
            "    <TargetFramework>net472</TargetFramework>\n",
            "    <TargetFramework>net472</TargetFramework>\n    <LangVersion>11.0</LangVersion>\n",
        )
        csproj.write_text(
            csproj_text.replace(
                '    <Reference Include="Unity.Collections">\n      <Private>false</Private>\n    </Reference>\n',
                "",
            ),
            encoding="utf-8",
        )
        mod_cs = project / "Mod.cs"
        mod_cs.write_text(
            mod_cs.read_text(encoding="utf-8").replace(
                "    public void OnDispose()",
                "        updateSystem.UpdateAt<MissingTrafficSystem>(SystemUpdatePhase.GameSimulation);\n    }\n\n    public void OnDispose()",
            ),
            encoding="utf-8",
        )

        result = self.analyzer.analyze_project(scaffold["project_dir"], profile="auto", strict=True)

        statuses = {c["id"]: c["status"] for c in result["checks"]}
        self.assertEqual(statuses.get("langversion_after_toolchain_imports"), "fail")
        self.assertEqual(statuses.get("unity_collections_reference"), "fail")
        self.assertEqual(statuses.get("unresolved_update_systems"), "fail")
        self.assertLess(result["score"], 80)

    def test_langversion_check_ignores_linked_toolchain_metadata(self) -> None:
        scaffold = self.scaffolder.scaffold_project(
            name="Linked Toolchain Metadata",
            template="cities2-csharp",
            target_dir=None,
            metadata={},
            options={},
        )

        result = self.analyzer.analyze_project(scaffold["project_dir"], profile="auto", strict=True)

        statuses = {c["id"]: c["status"] for c in result["checks"]}
        self.assertEqual(statuses.get("langversion_after_toolchain_imports"), "pass")

    def test_analyze_project_in_additional_workspace(self) -> None:
        secondary = self.tmp / "secondary"
        scaffolder = ProjectScaffolder(
            self.tmp,
            templates_dir=ROOT / "cities2_mcp" / "templates",
            additional_workspaces=[secondary],
        )
        analyzer = ProjectAnalyzer(scaffolder)
        scaffold = scaffolder.scaffold_project(
            name="Analyze Secondary",
            template="cities2-csharp",
            target_dir=str(secondary / "mods" / "analyze-secondary"),
            metadata={},
            options={},
        )

        result = analyzer.analyze_project(scaffold["project_dir"], profile="auto", strict=True)

        self.assertTrue(result["ok"])
        self.assertEqual(Path(result["project_dir"]).resolve(), Path(scaffold["project_dir"]).resolve())


if __name__ == "__main__":
    unittest.main()
