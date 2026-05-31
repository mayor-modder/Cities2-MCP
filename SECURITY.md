# Security policy

## Supported versions

Security fixes are applied to the default branch first. When practical, fixes are
also included in the latest public release.

| Version | Supported |
| --- | --- |
| Default branch | Yes |
| Latest public release | Yes |
| Older releases | Best effort |

## Reporting a vulnerability

Please do not open a public issue with exploit details.

Use GitHub private vulnerability reporting for this repository:

<https://github.com/mayor-modder/Cities2-MCP/security/advisories/new>

You can also reach the same form from the repository's Security tab by choosing
**Report a vulnerability**.

Do not post proof-of-concept payloads, local file paths, tokens, save data, or
other sensitive details publicly.

Please include:

- the affected version, commit, or release
- operating system and MCP client, if relevant
- a short description of the impact
- reproduction steps or a minimal proof of concept
- whether the issue requires a trusted workspace, user-provided mod project, or
  local Cities: Skylines II install

You can expect an initial response as soon as maintainers are available. We will
try to confirm the issue, discuss impact and timeline, and credit reporters who
want credit.

## Scope

Cities2 MCP and Modding Toolkit is a local MCP server for Cities: Skylines II
knowledge and modding workflows. It includes Python MCP server code, bundled
wiki retrieval data, agent skills, mod project templates, local game
Encyclopedia extraction, plugin manifests, launchers, packaged client
integration payloads, and workflow tools that can read, write, build, package,
and dry-run launch local mod projects.

Reports are especially useful when they involve:

- path traversal in project, package, scaffold, or file-write tools
- reading or writing files outside configured `--workspace` roots
- command injection or unsafe argument handling in build, package, analyzer, or
  launch helpers
- unsafe handling of untrusted mod project files, template metadata, package
  names, or generated files
- leaking local game files, generated Encyclopedia caches, personal paths,
  secrets, or user data through tool responses, packages, logs, or generated
  files
- release workflow or artifact integrity issues
- denial of service caused by malformed corpus, encyclopedia, project, or
  template inputs

The following are usually out of scope unless they bypass a documented security
control:

- vulnerabilities in Cities: Skylines II, Unity, Paradox Mods, GitHub, MCP
  clients, .NET, Python, Node.js, or other third-party platforms
- malicious mod code intentionally written by a user into a trusted workspace
- risks that require a user to run arbitrary shell commands outside this server
- prompt-injection behavior in an AI client that does not cause this project to
  violate its documented filesystem or command-execution boundaries
- dependency reports that do not affect this project
- denial-of-service reports based only on excessive automated traffic

## Safe configuration notes

- Configure trusted workspace roots narrowly, whether through `--workspace` or
  your client/plugin settings. Only include repositories or parent folders you
  trust the MCP workflow tools to read, write, build, and package.
- Treat build, package, analyze, and launch helpers as local development
  actions. They may execute project toolchains or inspect project files and
  should only be used on trusted projects.
- Do not commit locally extracted game Encyclopedia text, user save data,
  generated caches, or personal paths.
- Review generated mod files before publishing or distributing them.

## Disclosure

Please allow a reasonable coordination period before public disclosure. After a
fix is available, maintainers may publish a GitHub advisory, release notes, or a
public issue describing the impact and upgrade path without exposing sensitive
details unnecessarily.
