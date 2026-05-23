#!/usr/bin/env python3
"""Protocol-level smoke test for the local MCP server."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server" / "mcp_server.py"
DATA_DIR = ROOT / "data"
PYTHON = sys.executable


def framed(msg: dict) -> bytes:
    body = json.dumps(msg).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


def read_msg(stream) -> dict:
    first = stream.readline()
    if not first:
        raise RuntimeError("EOF while reading response")

    stripped = first.lstrip()
    if stripped.startswith(b"{") or stripped.startswith(b"["):
        return json.loads(first.decode("utf-8"))

    content_length = None
    line = first
    while True:
        if line in (b"\r\n", b"\n"):
            break
        s = line.decode("utf-8").strip()
        if s.lower().startswith("content-length:"):
            content_length = int(s.split(":", 1)[1].strip())
        line = stream.readline()
        if not line:
            raise RuntimeError("EOF while reading headers")
    if content_length is None:
        raise RuntimeError("No Content-Length header")
    payload = stream.read(content_length)
    return json.loads(payload.decode("utf-8"))


def call(proc, i: int, name: str, arguments: dict) -> dict:
    proc.stdin.write(
        framed(
            {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
    )
    proc.stdin.flush()
    resp = read_msg(proc.stdout)
    return json.loads(resp["result"]["content"][0]["text"])


def rpc(proc, i: int, method: str, params: dict) -> dict:
    proc.stdin.write(
        framed(
            {
                "jsonrpc": "2.0",
                "id": i,
                "method": method,
                "params": params,
            }
        )
    )
    proc.stdin.flush()
    return read_msg(proc.stdout)


def rpc_ndjson(proc, i: int, method: str, params: dict) -> dict:
    proc.stdin.write(
        (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": i,
                    "method": method,
                    "params": params,
                }
            )
            + "\n"
        ).encode("utf-8")
    )
    proc.stdin.flush()
    return read_msg(proc.stdout)


def main() -> None:
    ws = Path(tempfile.mkdtemp(prefix="cities2-mcp-smoke-"))

    proc = subprocess.Popen(
        [
            PYTHON,
            str(SERVER),
            "--data-dir",
            str(DATA_DIR),
            "--workspace",
            str(ws),
            "--mods-dir",
            str(ws / "local-mods"),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdin and proc.stdout and proc.stderr

    try:
        init = rpc_ndjson(proc, 1, "initialize", {"protocolVersion": "2025-06-18"})
        tools = rpc(proc, 2, "tools/list", {})
        resources = rpc(proc, 15, "resources/list", {})
        templates = rpc(proc, 16, "resources/templates/list", {})
        expected_tools = {
            "search_encyclopedia",
            "get_encyclopedia_entry",
            "source_status",
        }
        tool_names = {tool["name"] for tool in tools["result"]["tools"]}
        assert expected_tools.issubset(tool_names)
        first_page_uri = next(
            item["uri"] for item in resources["result"]["resources"] if item["uri"].startswith("wikimcp://page/")
        )
        page_read = rpc(proc, 17, "resources/read", {"uri": first_page_uri})

        s1 = call(proc, 3, "search", {"query": "modding toolchain requirements", "limit": 2})
        p1 = call(proc, 4, "get_page", {"page_id": "modding-toolchain"})
        r1 = call(proc, 5, "query_reference", {"query": "localization", "limit": 2})
        t1 = call(proc, 6, "get_snippets", {"query": "settings file", "limit": 1})

        c1 = call(proc, 7, "scaffold_project", {"name": "Smoke CSharp", "template": "cities2-csharp"})
        c2 = call(proc, 8, "scaffold_project", {"name": "Smoke UI", "template": "cities2-ui"})
        c3 = call(proc, 9, "scaffold_project", {"name": "Smoke Hybrid", "template": "cities2-hybrid"})

        proj = c1["project_dir"]
        w1 = call(
            proc,
            10,
            "write_project_file",
            {
                "project_dir": proj,
                "relative_path": "src/Generated.txt",
                "content": "hello\n",
                "mode": "upsert",
            },
        )
        l1 = call(proc, 11, "list_project_tree", {"project_dir": proj})
        b1 = call(proc, 12, "build_project", {"project_dir": proj, "steps": ["package"], "profile": "release"})
        a1 = call(proc, 13, "analyze_project", {"project_dir": proj, "profile": "auto", "strict": True})
        z1 = call(proc, 14, "package_project", {"project_dir": proj, "exclude_globs": ["obj/*", "bin/*"]})
        g1 = call(proc, 18, "launch_cities2", {"platform": "auto", "flags": ["--developerMode"], "dry_run": True})
        status = call(proc, 19, "source_status", {})
        assert "game_encyclopedia" in status

        print("initialize protocol:", init["result"]["protocolVersion"])
        print("tools count:", len(tools["result"]["tools"]))
        print("resources count:", len(resources["result"]["resources"]))
        print("resource templates count:", len(templates["result"]["resourceTemplates"]))
        print("read resource uri:", page_read["result"]["contents"][0]["uri"])
        print("search count:", s1["count"])
        print("get_page title:", p1["title"])
        print("reference count:", r1["count"])
        print("snippet ok:", t1.get("ok"))
        print("scaffold csharp:", c1["project_dir"])
        print("scaffold ui:", c2["project_dir"])
        print("scaffold hybrid:", c3["project_dir"])
        print("write file ok:", w1["ok"])
        print("tree count:", l1["count"])
        print("build ok:", b1["ok"])
        print("analyze score:", a1["score"])
        print("package path exists:", Path(z1["package_path"]).exists())
        print("launch dry_run:", g1["dry_run"])
        print("game encyclopedia available:", status["game_encyclopedia"]["available"])
    finally:
        proc.terminate()
        proc.wait(timeout=3)
        shutil.rmtree(ws, ignore_errors=True)


if __name__ == "__main__":
    main()
