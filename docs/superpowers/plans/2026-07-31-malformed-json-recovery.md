# Malformed JSON-RPC recovery implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make both supported stdio framing modes return JSON-RPC parse error `-32700` for malformed JSON and continue processing the next valid message.

**Architecture:** Keep recovery inside the shared `read_message()` transport function so both server entry points inherit it. Treat each NDJSON line and each declared `Content-Length` payload as one frame, discard only a malformed frame, emit a parse-error response through the already detected output transport, and resume the read loop.

**Tech Stack:** Python 3.10+, standard-library `json`, `io`, `unittest`, and `unittest.mock`.

## Global constraints

- Do not install or execute the reporter's harness.
- Do not add dependencies, version bumps, release actions, commits, pushes, or pull requests.
- Do not edit generated plugin payloads by hand; regenerate them with `python -m cities2_mcp.plugin_packages sync`.
- Preserve the reporter's issue body and append `*Co-authored by Codex.*` to the maintainer comment.
- Keep Markdown headings in sentence case and prose paragraphs on single logical lines.

---

### Task 1: Add transport regression coverage and recover malformed frames

**Files:**
- Create: `tests/test_mcp_transport.py`
- Modify: `cities2_mcp/retrieval/mcp_server.py:1037-1107`
- Regenerate: `plugins/cities2-mcp/vendor/cities2_mcp/retrieval/mcp_server.py`

**Interfaces:**
- Consumes: `cities2_mcp.retrieval.mcp_server.read_message() -> Optional[object]` and `send_message(message: object) -> None`.
- Produces: unchanged `read_message()` signature with malformed-frame recovery and a focused `TransportTests` regression suite.

- [x] **Step 1: Write the failing NDJSON recovery test**

Create `tests/test_mcp_transport.py` with binary stdin/stdout wrappers, frame helpers, and this first test:

```python
from __future__ import annotations

import io
import json
import unittest
from unittest import mock

from cities2_mcp.retrieval import mcp_server


class BinaryTextStream:
    def __init__(self, data: bytes = b"") -> None:
        self.buffer = io.BytesIO(data)


def framed(payload: bytes) -> bytes:
    return f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload


def read_framed(data: bytes) -> dict:
    headers, payload = data.split(b"\r\n\r\n", 1)
    content_length = int(headers.split(b":", 1)[1].strip())
    return json.loads(payload[:content_length].decode("utf-8"))


class TransportTests(unittest.TestCase):
    def setUp(self) -> None:
        mcp_server.LAST_INPUT_TRANSPORT = "framed"

    def test_malformed_ndjson_returns_parse_error_and_recovers(self) -> None:
        valid = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
        stdin = BinaryTextStream(b'{"jsonrpc":"2.0", this is not json\n' + json.dumps(valid).encode("utf-8") + b"\n")
        stdout = BinaryTextStream()

        with mock.patch.object(mcp_server.sys, "stdin", stdin), mock.patch.object(
            mcp_server.sys, "stdout", stdout
        ):
            actual = mcp_server.read_message()

        self.assertEqual(actual, valid)
        self.assertEqual(
            json.loads(stdout.buffer.getvalue().decode("utf-8")),
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            },
        )
```

- [x] **Step 2: Run the regression test to verify RED**

Run:

```powershell
python -m unittest tests.test_mcp_transport.TransportTests.test_malformed_ndjson_returns_parse_error_and_recovers -v
```

Expected: FAIL because the current parser appends the valid `ping` line to the malformed frame, reaches EOF, and returns `None` without a parse-error response.

- [x] **Step 3: Add the remaining framing tests**

Add tests that assert valid NDJSON remains unchanged, valid `Content-Length` remains unchanged, and malformed framed JSON returns a framed parse error before successfully returning the following valid framed `ping`:

```python
    def test_valid_ndjson_is_unchanged(self) -> None:
        message = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
        stdin = BinaryTextStream(json.dumps(message).encode("utf-8") + b"\n")
        stdout = BinaryTextStream()
        with mock.patch.object(mcp_server.sys, "stdin", stdin), mock.patch.object(
            mcp_server.sys, "stdout", stdout
        ):
            self.assertEqual(mcp_server.read_message(), message)
        self.assertEqual(stdout.buffer.getvalue(), b"")

    def test_valid_content_length_is_unchanged(self) -> None:
        message = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
        stdin = BinaryTextStream(framed(json.dumps(message).encode("utf-8")))
        stdout = BinaryTextStream()
        with mock.patch.object(mcp_server.sys, "stdin", stdin), mock.patch.object(
            mcp_server.sys, "stdout", stdout
        ):
            self.assertEqual(mcp_server.read_message(), message)
        self.assertEqual(stdout.buffer.getvalue(), b"")

    def test_malformed_content_length_returns_parse_error_and_recovers(self) -> None:
        valid = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
        stdin = BinaryTextStream(
            framed(b'{"jsonrpc":"2.0", this is not json')
            + framed(json.dumps(valid).encode("utf-8"))
        )
        stdout = BinaryTextStream()

        with mock.patch.object(mcp_server.sys, "stdin", stdin), mock.patch.object(
            mcp_server.sys, "stdout", stdout
        ):
            actual = mcp_server.read_message()

        self.assertEqual(actual, valid)
        self.assertEqual(
            read_framed(stdout.buffer.getvalue()),
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            },
        )
```

- [x] **Step 4: Implement the minimal shared parser recovery**

In `read_message()`, replace multi-line JSON accumulation with strict single-line decoding, add a nested parse-error sender, and catch only UTF-8/JSON parsing failures after setting `LAST_INPUT_TRANSPORT`:

```python
    def send_parse_error() -> None:
        send_message(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            }
        )

    def read_json_line(first_line: bytes) -> object:
        return json.loads(first_line.decode("utf-8"))
```

For each transport branch in the outer `while True`, call its parser inside:

```python
        try:
            return read_json_line(stripped)
        except (UnicodeDecodeError, json.JSONDecodeError):
            send_parse_error()
            continue
```

or, for framed input:

```python
        try:
            return read_content_length_payload(first_line)
        except (UnicodeDecodeError, json.JSONDecodeError):
            send_parse_error()
            continue
```

Keep EOF, missing length, and empty payload behavior unchanged. Validate the declared body length, reject negative lengths, and preserve the first non-header line encountered after a supported framed header so it can be processed on the next loop iteration.

- [x] **Step 5: Run focused tests to verify GREEN**

Run:

```powershell
python -m unittest tests.test_mcp_transport -v
```

Expected: all 14 focused transport tests pass with no warnings or errors.

- [x] **Step 6: Run complete repository verification**

Run:

```powershell
python -m unittest discover -s tests -v
python -m cities2_mcp.plugin_packages sync
python -m cities2_mcp.plugin_packages check
```

Expected: all unit tests pass, the canonical source is copied into the generated plugin payload, and the plugin package check reports synchronized payloads.

- [x] **Step 7: Repeat the independent subprocess probe**

Run this standard-library-only probe. It launches `python -m cities2_mcp.mcp_server`, initializes over NDJSON, sends one malformed line, asserts the `-32700` response, sends `ping`, and asserts the same process returns `result: {}`:

```powershell
@'
import json
import subprocess
import sys

proc = subprocess.Popen(
    [sys.executable, "-m", "cities2_mcp.mcp_server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding="utf-8",
)
assert proc.stdin and proc.stdout and proc.stderr

def send(value):
    text = value if isinstance(value, str) else json.dumps(value)
    proc.stdin.write(text + "\n")
    proc.stdin.flush()

try:
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "local-regression-probe", "version": "1"}}})
    assert json.loads(proc.stdout.readline())["id"] == 1
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    send('{"jsonrpc":"2.0", this is not json')
    parse_error = json.loads(proc.stdout.readline())
    assert parse_error == {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
    send({"jsonrpc": "2.0", "id": 2, "method": "ping"})
    assert json.loads(proc.stdout.readline()) == {"jsonrpc": "2.0", "id": 2, "result": {}}
    assert proc.poll() is None
    print("malformed-frame recovery probe: pass")
finally:
    proc.terminate()
    proc.wait(timeout=5)
'@ | python -
```

Expected: `malformed-frame recovery probe: pass` and exit code 0.

- [x] **Step 8: Review the diff without committing**

Run:

```powershell
git diff --check
git diff -- cities2_mcp/retrieval/mcp_server.py tests/test_mcp_transport.py docs/superpowers/specs/2026-07-31-malformed-json-recovery-design.md docs/superpowers/plans/2026-07-31-malformed-json-recovery.md
git status --short --branch
```

Expected: only the canonical parser, synchronized generated parser copy, focused tests, design, and plan are changed; no commit is created.

### Task 2: Correct issue #163 metadata and document the verified impact

**Files:**
- Modify externally: `mayor-modder/Cities2-MCP#163` title, labels, and comments.

**Interfaces:**
- Consumes: successful Task 1 verification results and the repository's existing issue labels.
- Produces: corrected public issue metadata and one maintainer comment; the reporter's original body remains unchanged.

- [x] **Step 1: Read the current issue and available labels**

Confirm issue #163 is still open and unchanged. List repository labels and select the existing ordinary bug label only if its exact name is present.

- [x] **Step 2: Restate the external write target**

Before mutating GitHub, state that the exact target is `mayor-modder/Cities2-MCP#163`, the replacement title is `Malformed JSON-RPC frame prevents subsequent stdio messages`, the reporter's body will remain unchanged, and only an existing ordinary bug label will be added.

- [x] **Step 3: Update the issue title and label**

Set the title to `Malformed JSON-RPC frame prevents subsequent stdio messages`. Add the ordinary bug label if available. Do not close the issue because the fix is not committed, pushed, merged, or released.

- [x] **Step 4: Add the maintainer comment**

Post this comment after verifying that the complete suite contains 486 passing tests:

```markdown
Thanks for the report. We independently reproduced the malformed-frame behavior without installing or running the linked harness.

The exact observed behavior is that a malformed newline-delimited JSON frame leaves the process alive but causes the parser to absorb subsequent messages, so a following `ping` times out. The process does not exit in this reproduction; it exits normally only after its stdin is closed.

We classify this as a low-severity local stdio robustness and JSON-RPC conformance issue rather than a high-severity security denial of service. In the standard MCP stdio model, the client launches the server subprocess and is the only writer to its stdin, and the MCP transport specification requires the client not to send invalid messages. The server should nevertheless recover correctly.

A local fix now treats each NDJSON line or declared `Content-Length` payload as one frame, returns JSON-RPC parse error `-32700` with `id: null`, discards only the malformed frame, and continues processing. Focused recovery tests, the complete unit suite (486 tests), the plugin-package check, and an independent same-process malformed-frame/`ping` probe pass. The issue will remain open until the fix is committed and published.

For future reports that may contain security-sensitive details, please use this repository's private vulnerability-reporting form linked from `SECURITY.md` before posting a public proof of concept.

*Co-authored by Codex.*
```

- [x] **Step 5: Re-fetch the issue and verify external state**

Confirm the issue remains open, has the corrected title, retains the reporter's original body, has only the intended added label, and contains the maintainer comment exactly once.
