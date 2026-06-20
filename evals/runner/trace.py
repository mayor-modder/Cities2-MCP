from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _iter_json_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _nested_event(event: dict[str, Any]) -> dict[str, Any]:
    msg = event.get("msg")
    if isinstance(msg, dict):
        return msg

    item = event.get("item")
    if isinstance(item, dict):
        return item

    return event


def _is_incomplete_item_event(event: dict[str, Any]) -> bool:
    return event.get("type") == "item.started"


def _tool_call(event: dict[str, Any]) -> dict[str, Any] | None:
    if _is_incomplete_item_event(event):
        return None

    candidate = _nested_event(event)
    raw_type = candidate.get("type")
    if raw_type == "command_execution":
        command = candidate.get("command")
        if not isinstance(command, str):
            return None
        return {
            "name": "shell_command",
            "arguments": {"command": command},
            "raw_type": raw_type,
        }

    if raw_type not in {"tool_call", "function_call", "mcp_tool_call"}:
        return None

    name = candidate.get("name")
    if not isinstance(name, str):
        name = candidate.get("tool")
    if not isinstance(name, str):
        name = candidate.get("tool_name")
    if not isinstance(name, str):
        return None

    return {
        "name": name,
        "arguments": _arguments(candidate.get("arguments")),
        "raw_type": raw_type,
    }


def _arguments(raw_arguments: Any) -> dict[str, Any]:
    if isinstance(raw_arguments, dict):
        return raw_arguments

    if isinstance(raw_arguments, str):
        try:
            parsed = json.loads(raw_arguments)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed

    return {}


def _message_text(event: dict[str, Any]) -> str | None:
    candidate = _nested_event(event)
    role = candidate.get("role")
    if role == "user":
        return None

    event_type = candidate.get("type")
    if event_type not in {"agent_message", "assistant_message"} and not (
        event_type == "message" and role == "assistant"
    ):
        return None

    for field in ("message", "text", "content"):
        text = candidate.get(field)
        if isinstance(text, str):
            return text
    return None


def normalize_codex_events(
    raw_events: Path, tool_calls: Path, transcript: Path
) -> None:
    calls: list[dict[str, Any]] = []
    messages: list[str] = []

    for event in _iter_json_lines(raw_events):
        call = _tool_call(event)
        if call is not None:
            calls.append(call)

        message = _message_text(event)
        if message is not None:
            messages.append(message)

    tool_calls.write_text(
        "".join(json.dumps(call, sort_keys=True) + "\n" for call in calls),
        encoding="utf-8",
    )
    transcript.write_text("\n\n".join(messages), encoding="utf-8")


def _claude_content_blocks(event: dict[str, Any]) -> list[dict[str, Any]]:
    message = event.get("message")
    if isinstance(message, dict):
        content = message.get("content")
    else:
        content = event.get("content")
    if not isinstance(content, list):
        return []
    return [block for block in content if isinstance(block, dict)]


def _claude_tool_call(block: dict[str, Any]) -> dict[str, Any] | None:
    if block.get("type") not in {"tool_use", "server_tool_use"}:
        return None
    name = block.get("name")
    if not isinstance(name, str):
        name = block.get("tool_name")
    if not isinstance(name, str):
        return None
    arguments = block.get("input")
    if not isinstance(arguments, dict):
        arguments = _arguments(block.get("arguments"))
    if name == "Bash":
        name = "shell_command"
    return {
        "name": name,
        "arguments": arguments if isinstance(arguments, dict) else {},
        "raw_type": f"claude_{block.get('type')}",
    }


def _claude_text(block: dict[str, Any]) -> str | None:
    if block.get("type") != "text":
        return None
    text = block.get("text")
    return text if isinstance(text, str) else None


def normalize_claude_events(
    raw_events: Path, tool_calls: Path, transcript: Path
) -> None:
    calls: list[dict[str, Any]] = []
    messages: list[str] = []
    result_messages: list[str] = []

    for event in _iter_json_lines(raw_events):
        if event.get("type") == "assistant":
            for block in _claude_content_blocks(event):
                call = _claude_tool_call(block)
                if call is not None:
                    calls.append(call)
                text = _claude_text(block)
                if text is not None:
                    messages.append(text)
        elif event.get("type") in {"tool_use", "server_tool_use"}:
            call = _claude_tool_call(event)
            if call is not None:
                calls.append(call)
        elif event.get("type") == "result":
            result = event.get("result")
            if isinstance(result, str):
                result_messages.append(result)

    if not messages:
        messages = result_messages

    tool_calls.write_text(
        "".join(json.dumps(call, sort_keys=True) + "\n" for call in calls),
        encoding="utf-8",
    )
    transcript.write_text("\n\n".join(messages), encoding="utf-8")
