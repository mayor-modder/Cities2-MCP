#!/usr/bin/env python3
"""Direct CLI for Cities2-MCP."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server" / "mcp_server.py"
WORKSPACE = ROOT
PYTHON = sys.executable


def framed(msg: Dict[str, Any]) -> bytes:
    body = json.dumps(msg).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


def read_msg(stream) -> Dict[str, Any]:
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
        raise RuntimeError("No Content-Length header in response")
    payload = stream.read(content_length)
    return json.loads(payload.decode("utf-8"))


def rpc(proc, req_id: int, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    assert proc.stdin and proc.stdout
    proc.stdin.write(framed({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}))
    proc.stdin.flush()
    return read_msg(proc.stdout)


def notify(proc, method: str, params: Dict[str, Any]) -> None:
    assert proc.stdin
    proc.stdin.write(framed({"jsonrpc": "2.0", "method": method, "params": params}))
    proc.stdin.flush()


def parse_content_text(resp: Dict[str, Any]) -> Any:
    content = resp.get("result", {}).get("content", [])
    if not content:
        return resp
    text = content[0].get("text", "")
    try:
        return json.loads(text)
    except Exception:
        return text


def tool_call_from_args(args: argparse.Namespace) -> Dict[str, Any]:
    if args.cmd == "call-tool":
        tool_args = json.loads(args.args)
        if not isinstance(tool_args, dict):
            raise ValueError("--args must parse to a JSON object")
        return {"name": args.name, "arguments": tool_args}

    if args.cmd == "scaffold":
        metadata = json.loads(args.metadata) if args.metadata else {}
        options = json.loads(args.options) if args.options else {}
        if not isinstance(metadata, dict) or not isinstance(options, dict):
            raise ValueError("--metadata and --options must be JSON objects")
        payload: Dict[str, Any] = {
            "name": args.name,
            "template": args.template,
            "metadata": metadata,
            "options": options,
        }
        if args.target_dir:
            payload["target_dir"] = args.target_dir
        return {"name": "scaffold_project", "arguments": payload}

    if args.cmd == "build":
        payload: Dict[str, Any] = {
            "project_dir": args.project_dir,
            "profile": args.profile,
            "clean": args.clean,
            "package": args.package,
            "timeout_sec": args.timeout_sec,
        }
        if args.steps:
            payload["steps"] = [s.strip() for s in args.steps.split(",") if s.strip()]
        return {"name": "build_project", "arguments": payload}

    if args.cmd == "analyze":
        return {
            "name": "analyze_project",
            "arguments": {
                "project_dir": args.project_dir,
                "profile": args.profile,
                "strict": args.strict,
            },
        }

    raise ValueError(f"Unsupported command: {args.cmd}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Call Cities2-MCP directly")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list-tools", help="List MCP tool names")

    call_p = sub.add_parser("call-tool", help="Call any MCP tool by name")
    call_p.add_argument("name", help="Tool name")
    call_p.add_argument("--args", default="{}", help="JSON object with tool arguments")

    scaffold_p = sub.add_parser("scaffold", help="Scaffold project using scaffold_project")
    scaffold_p.add_argument("name", help="Project name")
    scaffold_p.add_argument("template", choices=["cities2-csharp", "cities2-ui", "cities2-hybrid"])
    scaffold_p.add_argument("--target-dir")
    scaffold_p.add_argument("--metadata", default="{}", help="JSON object")
    scaffold_p.add_argument("--options", default="{}", help="JSON object")

    build_p = sub.add_parser("build", help="Run build_project")
    build_p.add_argument("project_dir")
    build_p.add_argument("--profile", choices=["debug", "release"], default="release")
    build_p.add_argument("--steps", help="Comma-separated ui,dotnet,package")
    build_p.add_argument("--clean", action="store_true")
    build_p.add_argument("--package", action="store_true")
    build_p.add_argument("--timeout-sec", type=int, default=300)

    analyze_p = sub.add_parser("analyze", help="Run analyze_project")
    analyze_p.add_argument("project_dir")
    analyze_p.add_argument("--profile", choices=["auto", "cities2-csharp", "cities2-ui", "cities2-hybrid"], default="auto")
    analyze_p.add_argument("--strict", action="store_true")

    args = parser.parse_args()

    proc = subprocess.Popen(
        [
            PYTHON,
            str(SERVER),
            "--data-dir",
            str(ROOT / "data"),
            "--workspace",
            str(WORKSPACE),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        _ = rpc(proc, 1, "initialize", {"protocolVersion": "2025-06-18"})
        notify(proc, "notifications/initialized", {})

        if args.cmd == "list-tools":
            resp = rpc(proc, 2, "tools/list", {})
            names = [t.get("name") for t in resp.get("result", {}).get("tools", [])]
            print(json.dumps({"count": len(names), "tools": names}, indent=2))
            return 0

        tool_call = tool_call_from_args(args)
        resp = rpc(proc, 2, "tools/call", tool_call)
        payload = parse_content_text(resp)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
