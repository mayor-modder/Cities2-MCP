from __future__ import annotations

import io
import json
import unittest
from unittest import mock

from cities2_mcp.retrieval import mcp_server


class BinaryTextStream:
    def __init__(self, data: bytes = b"") -> None:
        self.buffer = io.BytesIO(data)


class LimitedWriteBuffer(io.BytesIO):
    def __init__(self, max_writes: int) -> None:
        super().__init__()
        self.max_writes = max_writes
        self.write_count = 0

    def write(self, data: bytes) -> int:
        self.write_count += 1
        if self.write_count > self.max_writes:
            raise AssertionError("transport emitted repeated parse errors")
        return super().write(data)


class LimitedOutputStream:
    def __init__(self, max_writes: int = 2) -> None:
        self.buffer = LimitedWriteBuffer(max_writes)


def framed(payload: bytes) -> bytes:
    return f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload


def content_type_framed(payload: bytes) -> bytes:
    return (
        b"Content-Type: application/vscode-jsonrpc; charset=utf-8\r\n"
        + f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii")
        + payload
    )


def read_framed(data: bytes) -> dict:
    headers, payload = data.split(b"\r\n\r\n", 1)
    content_length = int(headers.split(b":", 1)[1].strip())
    return json.loads(payload[:content_length].decode("utf-8"))


class TransportTests(unittest.TestCase):
    def setUp(self) -> None:
        original_transport = mcp_server.LAST_INPUT_TRANSPORT
        self.addCleanup(
            setattr, mcp_server, "LAST_INPUT_TRANSPORT", original_transport
        )
        mcp_server.LAST_INPUT_TRANSPORT = "framed"

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

    def test_content_type_before_content_length_is_unchanged(self) -> None:
        message = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
        stdin = BinaryTextStream(
            content_type_framed(json.dumps(message).encode("utf-8"))
        )
        stdout = BinaryTextStream()
        with mock.patch.object(mcp_server.sys, "stdin", stdin), mock.patch.object(
            mcp_server.sys, "stdout", stdout
        ):
            self.assertEqual(mcp_server.read_message(), message)
        self.assertEqual(stdout.buffer.getvalue(), b"")

    def test_incomplete_invalid_content_length_body_closes_silently(self) -> None:
        stdin = BinaryTextStream(b"Content-Length: 100\r\n\r\n{")
        stdout = BinaryTextStream()

        with mock.patch.object(mcp_server.sys, "stdin", stdin), mock.patch.object(
            mcp_server.sys, "stdout", stdout
        ):
            self.assertIsNone(mcp_server.read_message())

        self.assertEqual(stdout.buffer.getvalue(), b"")

    def test_incomplete_valid_content_length_body_closes_silently(self) -> None:
        stdin = BinaryTextStream(b"Content-Length: 100\r\n\r\n{}")
        stdout = BinaryTextStream()

        with mock.patch.object(mcp_server.sys, "stdin", stdin), mock.patch.object(
            mcp_server.sys, "stdout", stdout
        ):
            self.assertIsNone(mcp_server.read_message())

        self.assertEqual(stdout.buffer.getvalue(), b"")

    def test_negative_content_length_returns_parse_error_and_recovers(self) -> None:
        valid = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
        stdin = BinaryTextStream(
            b"Content-Length: -1\r\n\r\n"
            + json.dumps(valid).encode("utf-8")
            + b"\n"
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

    def test_malformed_ndjson_returns_parse_error_and_recovers(self) -> None:
        valid = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
        stdin = BinaryTextStream(
            b'{"jsonrpc":"2.0", this is not json\n'
            + json.dumps(valid).encode("utf-8")
            + b"\n"
        )
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

    def test_invalid_utf8_ndjson_returns_parse_error_and_recovers(self) -> None:
        valid = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
        stdin = BinaryTextStream(
            b"\xff\n" + json.dumps(valid).encode("utf-8") + b"\n"
        )
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

    def test_header_shaped_malformed_ndjson_returns_parse_error_and_recovers(
        self,
    ) -> None:
        valid = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
        stdin = BinaryTextStream(
            b"not: json\n" + json.dumps(valid).encode("utf-8") + b"\n"
        )
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

    def test_content_length_without_colon_does_not_loop(self) -> None:
        self._assert_malformed_ndjson_line_recovers(b"Content-Length\n")

    def test_indented_content_length_does_not_loop(self) -> None:
        self._assert_malformed_ndjson_line_recovers(b" Content-Length: 4\n")

    def _assert_malformed_ndjson_line_recovers(self, malformed: bytes) -> None:
        valid = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
        stdin = BinaryTextStream(
            malformed + json.dumps(valid).encode("utf-8") + b"\n"
        )
        stdout = LimitedOutputStream()

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

    def test_incomplete_content_type_header_does_not_consume_next_ndjson(
        self,
    ) -> None:
        valid = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
        stdin = BinaryTextStream(
            b"Content-Type: application/json\n"
            + json.dumps(valid).encode("utf-8")
            + b"\n"
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

    def test_invalid_utf8_content_length_returns_parse_error_and_recovers(
        self,
    ) -> None:
        valid = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
        stdin = BinaryTextStream(
            framed(b"\xff") + framed(json.dumps(valid).encode("utf-8"))
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
