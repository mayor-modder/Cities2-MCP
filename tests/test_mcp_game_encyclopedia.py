from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FakeAvailableEncyclopedia:
    available = True

    def search(self, query: str, *, limit: int = 5):
        return []


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class McpGameEncyclopediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module("mcp_server_game_encyclopedia_tests", ROOT / "server" / "mcp_server.py")

    def test_tools_list_includes_game_encyclopedia_tools(self) -> None:
        response = self.module.handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            corpus=None,
            wm=None,
            encyclopedia=None,
            corpus_error="docs missing",
            workflow_error=None,
            docs_paths={},
        )

        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertEqual(len(names), len(response["result"]["tools"]))
        self.assertIn("search_encyclopedia", names)
        self.assertIn("get_encyclopedia_entry", names)
        self.assertIn("source_status", names)

    def test_source_status_reports_unavailable_encyclopedia(self) -> None:
        response = self.module.handle_tools_call(
            2,
            {"name": "source_status", "arguments": {}},
            corpus=None,
            wm=None,
            encyclopedia=None,
            corpus_error="docs missing",
            workflow_error=None,
            docs_paths={},
        )
        payload = json.loads(response["result"]["content"][0]["text"])

        self.assertFalse(payload["game_encyclopedia"]["available"])
        self.assertIn("Game Encyclopedia not found", payload["game_encyclopedia"]["warning"])

    def test_search_encyclopedia_unavailable_returns_tool_error_payload(self) -> None:
        response = self.module.handle_tools_call(
            3,
            {"name": "search_encyclopedia", "arguments": {"query": "roads"}},
            corpus=None,
            wm=None,
            encyclopedia=None,
            corpus_error=None,
            workflow_error=None,
            docs_paths={},
        )
        payload = json.loads(response["result"]["content"][0]["text"])

        self.assertFalse(payload["ok"])
        self.assertIn("Game Encyclopedia not found", payload["message"])

    def test_search_encyclopedia_malformed_limit_returns_tool_error_payload(self) -> None:
        response = self.module.handle_tools_call(
            4,
            {"name": "search_encyclopedia", "arguments": {"query": "roads", "limit": "many"}},
            corpus=None,
            wm=None,
            encyclopedia=FakeAvailableEncyclopedia(),
            corpus_error=None,
            workflow_error=None,
            docs_paths={},
        )
        payload = json.loads(response["result"]["content"][0]["text"])

        self.assertFalse(payload["ok"])
        self.assertIn("error", payload)
