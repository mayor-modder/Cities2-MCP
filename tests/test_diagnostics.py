from __future__ import annotations

import unittest

from cities2_mcp.diagnostics import parse_build_output


class DiagnosticsTests(unittest.TestCase):
    def test_parse_dotnet_style(self) -> None:
        output = "src/Mod.cs(12,8): error CS1002: ; expected"
        diags = parse_build_output(output)
        self.assertEqual(len(diags), 1)
        d = diags[0]
        self.assertEqual(d["file"], "src/Mod.cs")
        self.assertEqual(d["line"], 12)
        self.assertEqual(d["column"], 8)
        self.assertEqual(d["severity"], "error")
        self.assertEqual(d["code"], "CS1002")

    def test_parse_typescript_colon_style(self) -> None:
        output = "ui/src/index.ts:3:11: error TS2304 Cannot find name 'foo'"
        diags = parse_build_output(output)
        self.assertEqual(len(diags), 1)
        self.assertEqual(diags[0]["tool"], "typescript")

    def test_parse_esbuild_and_npm(self) -> None:
        output = "\n".join(
            [
                "✘ [ERROR] Could not resolve './missing'",
                "  src/index.ts:2:9:",
                "npm ERR! code ELIFECYCLE",
            ]
        )
        diags = parse_build_output(output)
        self.assertGreaterEqual(len(diags), 2)
        tools = {d["tool"] for d in diags}
        self.assertIn("esbuild", tools)
        self.assertIn("npm", tools)


    def test_parse_missing_dotnet_runtime_from_msbuild_postprocessor(self) -> None:
        output = (
            r"C:\Users\Example\AppData\LocalLow\Colossal Order\Cities Skylines II\.cache\Modding\Mod.targets(103,5): "
            r"error : You must install or update .NET to run this application. "
            r"[C:\Users\Example\Documents\Cities2-MCP\TestMayor\testmayor.csproj]"
        )

        diags = parse_build_output(output, tool_hint="dotnet")

        self.assertEqual(len(diags), 1)
        self.assertEqual(diags[0]["code"], "DOTNET_RUNTIME")
        self.assertEqual(diags[0]["tool"], "dotnet")
        self.assertIn("install or update .NET", diags[0]["message"])


if __name__ == "__main__":
    unittest.main()
