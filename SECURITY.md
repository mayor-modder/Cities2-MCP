# Security Policy

## Supported Versions

Security fixes are applied to the default branch first. When practical, fixes are
also included in the latest tagged release.

| Version | Supported |
| --- | --- |
| Default branch | Yes |
| Latest tagged release | Yes |
| Older releases | Best effort |

## Reporting a Vulnerability

Please do not open a public issue with exploit details.

Use GitHub private vulnerability reporting for this repository. From the
repository's Security tab, choose **Report a vulnerability**.

Do not open a public issue for security reports, and do not post
proof-of-concept payloads, local file paths, tokens, save data, or other
sensitive details publicly.

Please include:

- the affected version, commit, or tag
- operating system and MCP client, if relevant
- a short description of the impact
- reproduction steps or a minimal proof of concept
- whether the issue requires a trusted workspace, user-provided mod project, or
  local Cities: Skylines II install

You can expect an initial response as soon as maintainers are available. We will
try to confirm the issue, discuss impact and timeline, and credit reporters who
want credit.

## Scope

Cities2-MCP is a local MCP server for Cities: Skylines II knowledge and modding
workflows. The most important security boundaries are local filesystem access,
configured workspace allowlists, command execution for build/package workflows,
and data read from a user's local game installation.

Reports are especially useful when they involve:

- reading or writing files outside configured `--workspace` roots
- path traversal in project, package, scaffold, or file-write tools
- command injection or unsafe argument handling in build, package, analyzer, or
  launch helpers
- leaking local game files, generated encyclopedia caches, secrets, or personal
  paths through tool responses, packages, logs, or generated files
- unsafe handling of untrusted mod project files, template metadata, or package
  names
- denial of service caused by malformed corpus, encyclopedia, project, or
  template inputs

The following are usually out of scope unless they bypass a Cities2-MCP security
control:

- vulnerabilities in Cities: Skylines II, the Paradox/Colossal Order toolchain,
  .NET, Python, Node.js, or an MCP client
- malicious mod code intentionally written by a user into a trusted workspace
- risks that require a user to run arbitrary shell commands outside this server
- prompt-injection behavior in an AI client that does not cause Cities2-MCP to
  violate its documented filesystem or command-execution boundaries

## Safe Configuration Notes

- Configure `--workspace` roots narrowly. Only include repositories or parent
  folders you trust the MCP workflow tools to read, write, build, and package.
- Treat build and package tools as local development actions. They may execute
  project toolchains and should only be used on trusted projects.
- Do not commit locally extracted game encyclopedia text, user save data,
  generated caches, or personal paths.
- Review generated mod files before publishing or distributing them.

## Disclosure

Please allow a reasonable coordination period before public disclosure. After a
fix is available, maintainers may publish a GitHub advisory, release notes, or a
public issue describing the impact and upgrade path without exposing sensitive
details unnecessarily.
