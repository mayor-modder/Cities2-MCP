from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

JSON = Dict[str, Any]

_DOTNET_RE = re.compile(
    r"^(?P<file>.+?)\((?P<line>\d+),(?P<column>\d+)\):\s*(?P<severity>error|warning)\s*(?P<code>[A-Z]{1,6}\d+):\s*(?P<message>.+)$",
    re.IGNORECASE,
)
_MSBUILD_BARE_RE = re.compile(
    r"^(?P<file>.+?)\((?P<line>\d+),(?P<column>\d+)\):\s*(?P<severity>error|warning)\s*:\s*(?P<message>.+?)(?:\s+\[[^\]]+\])?$",
    re.IGNORECASE,
)
_TS_PAREN_RE = re.compile(
    r"^(?P<file>.+?)\((?P<line>\d+),(?P<column>\d+)\):\s*(?P<severity>error|warning)\s*(?P<code>TS\d+):\s*(?P<message>.+)$",
    re.IGNORECASE,
)
_COLON_RE = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+):(?P<column>\d+):\s*(?:(?P<severity>error|warning)\s*)?(?:(?P<code>[A-Z]{1,6}\d+)\s*)?(?P<message>.+)$",
    re.IGNORECASE,
)
_MSB_RE = re.compile(r"^(?P<severity>error|warning)\s+(?P<code>MSB\d+):\s*(?P<message>.+)$", re.IGNORECASE)
_ESBUILD_HEADER_RE = re.compile(r"^[✘x]\s*\[(?P<severity>ERROR|WARNING)\]\s*(?P<message>.+)$")
_ESBUILD_FILE_RE = re.compile(r"^\s*(?P<file>[^:]+):(?P<line>\d+):(?P<column>\d+):")
_NPM_ERR_RE = re.compile(r"^npm\s+ERR!\s*(?P<message>.+)$", re.IGNORECASE)


def _normalize_severity(value: str) -> str:
    return "error" if value.strip().lower() == "error" else "warning"


def _tool_for_code(code: str, fallback: str) -> str:
    code_upper = code.upper()
    if code_upper.startswith("TS"):
        return "typescript"
    if code_upper.startswith("MSB"):
        return "msbuild"
    if re.match(r"^[A-Z]{1,6}\d+$", code_upper):
        return "dotnet"
    return fallback


def _mk_diag(
    *,
    file: str,
    line: int,
    column: int,
    severity: str,
    code: str,
    message: str,
    tool: str,
    raw: str,
) -> JSON:
    return {
        "file": file,
        "line": max(0, int(line)),
        "column": max(0, int(column)),
        "severity": _normalize_severity(severity),
        "code": code,
        "message": message.strip(),
        "tool": tool,
        "raw": raw,
    }


def parse_build_output(build_output: str, tool_hint: Optional[str] = None) -> List[JSON]:
    """Parse mixed build output into normalized diagnostics.

    Output shape:
    - file
    - line
    - column
    - severity
    - code
    - message
    - tool
    - raw
    """

    lines = build_output.splitlines()
    diags: List[JSON] = []
    fallback_tool = tool_hint or "build"

    idx = 0
    while idx < len(lines):
        raw = lines[idx]
        line = raw.strip()
        if not line:
            idx += 1
            continue

        m = _DOTNET_RE.match(line)
        if m:
            code = m.group("code")
            diags.append(
                _mk_diag(
                    file=m.group("file"),
                    line=int(m.group("line")),
                    column=int(m.group("column")),
                    severity=m.group("severity"),
                    code=code,
                    message=m.group("message"),
                    tool=_tool_for_code(code, fallback_tool),
                    raw=raw,
                )
            )
            idx += 1
            continue

        m = _MSBUILD_BARE_RE.match(line)
        if m:
            message = m.group("message").strip()
            if (
                not message
                or message.startswith("[")
                or re.match(r"^\d+\.\d+\.\d+\s+at\s+\[", message)
                or message.lower().startswith(
                    (
                        "app:",
                        "architecture:",
                        "framework:",
                        ".net location:",
                        "no frameworks were found.",
                        "the following frameworks were found:",
                        "learn more:",
                        "to install missing framework",
                        "https://",
                    )
                )
            ):
                idx += 1
                continue
            code = "DOTNET_RUNTIME" if message.lower().startswith("you must install or update .net") else "MSBUILD"
            diags.append(
                _mk_diag(
                    file=m.group("file"),
                    line=int(m.group("line")),
                    column=int(m.group("column")),
                    severity=m.group("severity"),
                    code=code,
                    message=message,
                    tool="dotnet" if code == "DOTNET_RUNTIME" else "msbuild",
                    raw=raw,
                )
            )
            idx += 1
            continue

        m = _TS_PAREN_RE.match(line)
        if m:
            code = m.group("code")
            diags.append(
                _mk_diag(
                    file=m.group("file"),
                    line=int(m.group("line")),
                    column=int(m.group("column")),
                    severity=m.group("severity"),
                    code=code,
                    message=m.group("message"),
                    tool=_tool_for_code(code, "typescript"),
                    raw=raw,
                )
            )
            idx += 1
            continue

        m = _COLON_RE.match(line)
        if m and m.group("file") and not m.group("file").lower().startswith("http"):
            sev = m.group("severity") or "error"
            code = (m.group("code") or "")
            msg = m.group("message")
            file_name = m.group("file")
            if file_name.startswith("npm ERR"):
                idx += 1
                continue
            diags.append(
                _mk_diag(
                    file=file_name,
                    line=int(m.group("line")),
                    column=int(m.group("column")),
                    severity=sev,
                    code=code,
                    message=msg,
                    tool=_tool_for_code(code, fallback_tool),
                    raw=raw,
                )
            )
            idx += 1
            continue

        m = _MSB_RE.match(line)
        if m:
            diags.append(
                _mk_diag(
                    file="",
                    line=0,
                    column=0,
                    severity=m.group("severity"),
                    code=m.group("code"),
                    message=m.group("message"),
                    tool="msbuild",
                    raw=raw,
                )
            )
            idx += 1
            continue

        m = _ESBUILD_HEADER_RE.match(line)
        if m:
            severity = _normalize_severity(m.group("severity"))
            message = m.group("message")
            file = ""
            line_no = 0
            col_no = 0
            for look_ahead in range(1, 4):
                next_idx = idx + look_ahead
                if next_idx >= len(lines):
                    break
                fm = _ESBUILD_FILE_RE.match(lines[next_idx])
                if fm:
                    file = fm.group("file")
                    line_no = int(fm.group("line"))
                    col_no = int(fm.group("column"))
                    break
            diags.append(
                _mk_diag(
                    file=file,
                    line=line_no,
                    column=col_no,
                    severity=severity,
                    code="ESBUILD",
                    message=message,
                    tool="esbuild",
                    raw=raw,
                )
            )
            idx += 1
            continue

        m = _NPM_ERR_RE.match(line)
        if m:
            msg = m.group("message")
            code = "NPM"
            if msg.lower().startswith("code "):
                code = msg.split(" ", 1)[1].strip() or "NPM"
            diags.append(
                _mk_diag(
                    file="",
                    line=0,
                    column=0,
                    severity="error",
                    code=code,
                    message=msg,
                    tool="npm",
                    raw=raw,
                )
            )
            idx += 1
            continue

        idx += 1

    # Keep order but drop duplicates that differ only by repeated raw lines.
    seen = set()
    unique: List[JSON] = []
    for d in diags:
        key = (d["file"], d["line"], d["column"], d["severity"], d["code"], d["message"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(d)

    return unique
