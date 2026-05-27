from __future__ import annotations

import unittest

from cities2_mcp.mcp_server import domain_tools_catalog, handle_domain_tools


EXPECTED_DOMAIN_TOOLS = {
    "scaffold_project",
    "write_project_file",
    "list_project_tree",
    "build_project",
    "analyze_project",
    "package_project",
    "launch_cities2",
}


class ExtensionTests(unittest.TestCase):
    def test_domain_tools_catalog_complete(self) -> None:
        names = {tool["name"] for tool in domain_tools_catalog()}
        self.assertEqual(names, EXPECTED_DOMAIN_TOOLS)

    def test_handle_domain_tools_unknown_returns_none(self) -> None:
        result = handle_domain_tools(req_id=1, params={"name": "nonexistent", "arguments": {}}, wm=None)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
