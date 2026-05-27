from __future__ import annotations

import json
import unittest
from pathlib import Path

from cities2_mcp import mcp_server

ROOT = Path(__file__).resolve().parents[1]


class FakeAvailableEncyclopedia:
    available = True
    entries = [{"entry_id": "roads/basic", "title": "Basic Roads"}]

    def search(self, query: str, *, limit: int = 5):
        return []

    def get_entry(self, entry_id: str):
        if entry_id == "roads/basic":
            return {"entry_id": entry_id, "title": "Basic Roads", "text": "Road text"}
        return None

    def status(self):
        return {"source": "game_encyclopedia", "available": True, "entry_count": 0}


class FakeUnavailableEncyclopedia:
    available = False
    entries = []

    def status(self):
        return {
            "source": "game_encyclopedia",
            "available": False,
            "cache_status": "missing",
            "warning": "Game Encyclopedia not found",
        }


class McpGameEncyclopediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = mcp_server

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

    def test_prompts_list_includes_cities2_slash_command_workflows(self) -> None:
        response = self.module.handle_request(
            {"jsonrpc": "2.0", "id": 9, "method": "prompts/list", "params": {}},
            corpus=None,
            wm=None,
            encyclopedia=None,
            corpus_error=None,
            workflow_error=None,
            docs_paths={},
        )

        prompts = {prompt["name"]: prompt for prompt in response["result"]["prompts"]}
        self.assertIn("cities2", prompts)
        self.assertIn("cities2-wiki", prompts)
        self.assertIn("cities2-encyclopedia", prompts)
        self.assertIn("cities2-modding", prompts)
        self.assertTrue(prompts["cities2"]["arguments"][0]["required"])

    def test_prompts_get_returns_portable_source_workflow_prompt(self) -> None:
        response = self.module.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "prompts/get",
                "params": {
                    "name": "cities2-encyclopedia",
                    "arguments": {"question": "Why are my citizens not using buses?"},
                },
            },
            corpus=None,
            wm=None,
            encyclopedia=None,
            corpus_error=None,
            workflow_error=None,
            docs_paths={},
        )

        text = response["result"]["messages"][0]["content"]["text"]
        self.assertIn("/cities2-encyclopedia", text)
        self.assertIn("Why are my citizens not using buses?", text)
        self.assertIn("source_status()", text)
        self.assertIn("search_encyclopedia", text)
        self.assertIn("CITIES2_GAME_DIR", text)
        self.assertNotIn("get_page", text)

    def test_prompts_get_rejects_unknown_prompt(self) -> None:
        response = self.module.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "prompts/get",
                "params": {"name": "cities2-forgotten-city", "arguments": {}},
            },
            corpus=None,
            wm=None,
            encyclopedia=None,
            corpus_error=None,
            workflow_error=None,
            docs_paths={},
        )

        self.assertEqual(-32602, response["error"]["code"])
        self.assertIn("Unknown prompt", response["error"]["message"])

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

    def test_resources_list_includes_encyclopedia_entries_when_available(self) -> None:
        encyclopedia = type(
            "FakeEncyclopedia",
            (),
            {
                "available": True,
                "entries": [{"entry_id": "roads", "title": "Roads"}],
                "get_entry": lambda self, entry_id: {"entry_id": entry_id, "title": "Roads", "text": "Road text"},
                "status": lambda self: {"source": "game_encyclopedia", "available": True, "entry_count": 1},
            },
        )()

        response = self.module.handle_request(
            {"jsonrpc": "2.0", "id": 4, "method": "resources/list", "params": {}},
            corpus=None,
            wm=None,
            encyclopedia=encyclopedia,
            corpus_error=None,
            workflow_error=None,
            docs_paths={},
        )

        uris = {item["uri"] for item in response["result"]["resources"]}
        self.assertIn("cities2encyclopedia://entry/roads", uris)

    def test_resources_list_uri_encodes_encyclopedia_entry_ids(self) -> None:
        response = self.module.handle_request(
            {"jsonrpc": "2.0", "id": 6, "method": "resources/list", "params": {}},
            corpus=None,
            wm=None,
            encyclopedia=FakeAvailableEncyclopedia(),
            corpus_error=None,
            workflow_error=None,
            docs_paths={},
        )

        uris = {item["uri"] for item in response["result"]["resources"]}
        self.assertIn("cities2encyclopedia://entry/roads%2Fbasic", uris)

    def test_resources_read_returns_encyclopedia_entry_json(self) -> None:
        response = self.module.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "resources/read",
                "params": {"uri": "cities2encyclopedia://entry/roads%2Fbasic"},
            },
            corpus=None,
            wm=None,
            encyclopedia=FakeAvailableEncyclopedia(),
            corpus_error=None,
            workflow_error=None,
            docs_paths={},
        )

        content = response["result"]["contents"][0]
        payload = json.loads(content["text"])
        self.assertEqual("application/json", content["mimeType"])
        self.assertEqual("cities2encyclopedia://entry/roads%2Fbasic", content["uri"])
        self.assertEqual("roads/basic", payload["entry_id"])
        self.assertEqual("Road text", payload["text"])

    def test_resources_read_unavailable_encyclopedia_returns_warning_error(self) -> None:
        response = self.module.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "resources/read",
                "params": {"uri": "cities2encyclopedia://entry/roads"},
            },
            corpus=None,
            wm=None,
            encyclopedia=FakeUnavailableEncyclopedia(),
            corpus_error=None,
            workflow_error=None,
            docs_paths={},
        )

        self.assertEqual(-32001, response["error"]["code"])
        self.assertIn("Game Encyclopedia not found", response["error"]["message"])

    def test_main_debug_logs_unavailable_encyclopedia_status(self) -> None:
        loaded_encyclopedia = FakeUnavailableEncyclopedia()
        logs = []
        messages = iter([None])

        original_argv = self.module.sys.argv
        original_corpus = self.module.Corpus
        original_wm = self.module.WorkflowManager
        original_load = self.module.GameEncyclopediaSource.load
        original_read = self.module.read_message
        original_debug_enabled = self.module.debug_enabled
        original_debug_log = self.module.debug_log

        try:
            self.module.sys.argv = ["mcp_server.py"]
            self.module.Corpus = lambda paths: None
            self.module.WorkflowManager = lambda workspaces, mods_dir: None
            self.module.GameEncyclopediaSource.load = lambda config: loaded_encyclopedia
            self.module.read_message = lambda: next(messages)
            self.module.debug_enabled = lambda: True
            self.module.debug_log = logs.append

            self.module.main()
        finally:
            self.module.sys.argv = original_argv
            self.module.Corpus = original_corpus
            self.module.WorkflowManager = original_wm
            self.module.GameEncyclopediaSource.load = original_load
            self.module.read_message = original_read
            self.module.debug_enabled = original_debug_enabled
            self.module.debug_log = original_debug_log

        encyclopedia_logs = [line for line in logs if "Game encyclopedia status:" in line]
        self.assertEqual(1, len(encyclopedia_logs))
        self.assertIn("missing", encyclopedia_logs[0])
        self.assertIn("Game Encyclopedia not found", encyclopedia_logs[0])

    def test_main_passes_loaded_encyclopedia_to_request_handler(self) -> None:
        loaded_encyclopedia = FakeAvailableEncyclopedia()
        seen_encyclopedias = []
        sent_messages = []
        messages = iter(
            [
                {
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {"name": "source_status", "arguments": {}},
                },
                None,
            ]
        )

        original_argv = self.module.sys.argv
        original_corpus = self.module.Corpus
        original_wm = self.module.WorkflowManager
        original_load = self.module.GameEncyclopediaSource.load
        original_read = self.module.read_message
        original_send = self.module.send_message
        original_handle_request = self.module.handle_request

        def tracking_handle_request(message, corpus, wm, **kwargs):
            seen_encyclopedias.append(kwargs.get("encyclopedia"))
            return original_handle_request(message, corpus, wm, **kwargs)

        try:
            self.module.sys.argv = ["mcp_server.py"]
            self.module.Corpus = lambda paths: None
            self.module.WorkflowManager = lambda workspaces, mods_dir: None
            self.module.GameEncyclopediaSource.load = lambda config: loaded_encyclopedia
            self.module.read_message = lambda: next(messages)
            self.module.send_message = sent_messages.append
            self.module.handle_request = tracking_handle_request

            self.module.main()
        finally:
            self.module.sys.argv = original_argv
            self.module.Corpus = original_corpus
            self.module.WorkflowManager = original_wm
            self.module.GameEncyclopediaSource.load = original_load
            self.module.read_message = original_read
            self.module.send_message = original_send
            self.module.handle_request = original_handle_request

        self.assertEqual([loaded_encyclopedia], seen_encyclopedias)
        payload = json.loads(sent_messages[0]["result"]["content"][0]["text"])
        self.assertTrue(payload["game_encyclopedia"]["available"])
