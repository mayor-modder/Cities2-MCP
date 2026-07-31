# Malformed JSON-RPC recovery design

## Goal

Make the stdio transport recover from one malformed JSON-RPC frame without hanging or terminating the server, return the standard JSON-RPC parse error, and preserve normal processing of the next valid message.

## Scope

The change applies to both supported input formats in `cities2_mcp/retrieval/mcp_server.py`: newline-delimited JSON and the legacy `Content-Length` framing accepted for compatibility. The canonical source change is synchronized into the generated plugin vendor copy with `python -m cities2_mcp.plugin_packages sync`; generated files are not edited by hand. It changes only transport parsing and error recovery. Request dispatch, tool behavior, protocol negotiation, and output framing remain unchanged.

## Parser behavior

Each newline-delimited input line is one complete MCP frame. A valid line is decoded and returned exactly as it is today. A line that cannot be decoded as JSON is discarded as a single malformed frame; the server sends `{"jsonrpc":"2.0","id":null,"error":{"code":-32700,"message":"Parse error"}}` using the transport detected for that frame and resumes reading the next line.

For `Content-Length` input, the declared payload remains one complete frame. Invalid UTF-8 or malformed JSON produces the same parse-error response using `Content-Length` output framing, discards that payload, and resumes at the next header. Only `Content-Length` and `Content-Type` begin framed input; a different header-shaped NDJSON line is rejected without consuming the following line. Negative lengths are rejected, while EOF and bodies shorter than their declared length mean the transport has closed and do not produce a response.

The recovery is implemented once inside the shared `read_message()` transport function so both the retrieval-only entry point and the full Cities2-MCP entry point inherit identical behavior. The server loops will not gain duplicate malformed-input branches.

## Tests

A focused `tests/test_mcp_transport.py` module will exercise the real `read_message()` and `send_message()` functions with in-memory binary stdin and stdout wrappers.

The required regression cases are:

- malformed newline-delimited JSON returns `-32700` with `id: null`, then a following valid `ping` frame is parsed successfully;
- malformed `Content-Length` JSON returns the same error in framed form, then a following valid framed message is parsed successfully;
- invalid UTF-8 recovers in both transport modes;
- header-shaped NDJSON, incomplete `Content-Type` headers, and malformed supported header names do not consume the next NDJSON message or loop on pending input;
- negative lengths are rejected, and truncated framed bodies close silently even when the partial body is valid JSON;
- existing valid newline-delimited and `Content-Length` parsing behavior remains intact.

The first malformed-newline test must be run against the current implementation before production code changes and must fail because the parser consumes the later valid line and reaches EOF. After the minimal parser change, the focused tests and the complete unit suite must pass.

## Issue handling

After the implementation is verified, issue #163 will be retitled to `Malformed JSON-RPC frame prevents subsequent stdio messages`. The reporter's original body will remain unchanged. If an existing ordinary bug label is available, it will be added; security or high-severity labels will not be added.

A maintainer comment will thank the reporter, state that the observation was independently reproduced without their harness, distinguish the observed hang from a process exit, classify the standard local-stdio impact as a low-severity robustness issue, summarize the fix and verification, and note that future security-sensitive reports should use the repository's private vulnerability-reporting form. The comment will end with `*Co-authored by Codex.*` as required by repository policy.

## Non-goals

This change will not add a network transport, restart policy, rate limiting, dependency, version bump, release, commit, push, or pull request. It will not install or execute the reporter's harness.

## Verification

Verification consists of the focused transport tests, `python -m unittest discover -s tests -v`, `python -m cities2_mcp.plugin_packages sync`, and `python -m cities2_mcp.plugin_packages check`. The independent subprocess probe used during triage will be repeated against the changed server to confirm that the parse error is returned and the subsequent `ping` succeeds in one process.
