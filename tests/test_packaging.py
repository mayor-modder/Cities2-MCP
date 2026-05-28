from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    @staticmethod
    def _stop_proc(proc: subprocess.Popen[bytes]) -> None:
        proc.terminate()
        proc.wait(timeout=3)
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is not None:
                stream.close()

    def test_pyproject_declares_public_package_and_entrypoint(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        project = pyproject["project"]
        self.assertEqual(project["name"], "cities2-mcp")
        self.assertEqual(project["version"], "0.1.6")
        self.assertEqual(project["scripts"]["cities2-mcp"], "cities2_mcp.mcp_server:main")

    def test_package_module_reports_version_and_bundled_data_dir(self) -> None:
        package = importlib.import_module("cities2_mcp")

        self.assertEqual(package.__version__, "0.1.6")
        data_dir = package.bundled_data_dir()
        self.assertTrue((data_dir / "index" / "chunks.jsonl").exists())
        self.assertTrue((data_dir / "index" / "pages.jsonl").exists())

    def test_server_version_flag_prints_public_version(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "cities2_mcp.mcp_server", "--version"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertEqual(result.stdout.strip(), "cities2-mcp 0.1.6")

    def test_default_start_without_workspace_keeps_knowledge_tools_available(self) -> None:
        from tests.smoke_mcp import call, rpc, rpc_ndjson

        proc = subprocess.Popen(
            [sys.executable, "-m", "cities2_mcp.mcp_server"],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert proc.stdin and proc.stdout and proc.stderr

        try:
            init = rpc_ndjson(proc, 1, "initialize", {"protocolVersion": "2025-06-18"})
            tools = rpc(proc, 2, "tools/list", {})
            search = call(proc, 3, "search", {"query": "modding toolchain requirements", "limit": 1})
            scaffold = call(proc, 4, "scaffold_project", {"name": "No Workspace", "template": "cities2-csharp"})

            self.assertEqual(init["result"]["serverInfo"]["version"], "0.1.6")
            self.assertEqual(len(tools["result"]["tools"]), 14)
            self.assertTrue(search["ok"])
            self.assertFalse(scaffold["ok"])
            self.assertIn("--workspace", scaffold["error"])
        finally:
            self._stop_proc(proc)

    def test_default_start_with_workspace_enables_workflow_tools(self) -> None:
        from tests.smoke_mcp import call, rpc_ndjson

        with tempfile.TemporaryDirectory(prefix="cities2-mcp-package-") as tmp:
            workspace = Path(tmp)
            proc = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "cities2_mcp.mcp_server",
                    "--workspace",
                    str(workspace),
                    "--mods-dir",
                    str(workspace / "local-mods"),
                ],
                cwd=ROOT,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert proc.stdin and proc.stdout and proc.stderr

            try:
                rpc_ndjson(proc, 1, "initialize", {"protocolVersion": "2025-06-18"})
                scaffold = call(proc, 2, "scaffold_project", {"name": "Packaged", "template": "cities2-csharp"})

                self.assertTrue(scaffold["ok"])
                self.assertTrue(Path(scaffold["project_dir"]).is_dir())
            finally:
                self._stop_proc(proc)

    def test_server_json_registers_pypi_package(self) -> None:
        server_json = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))

        self.assertEqual(server_json["name"], "io.github.mayor-modder/cities2-mcp")
        self.assertEqual(server_json["version"], "0.1.6")
        package = server_json["packages"][0]
        self.assertEqual(package["registryType"], "pypi")
        self.assertEqual(package["identifier"], "cities2-mcp")
        self.assertEqual(package["version"], "0.1.6")
        self.assertEqual(package["transport"]["type"], "stdio")
