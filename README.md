# Cities2 MCP and Modding Toolkit

<!-- mcp-name: io.github.mayor-modder/cities2-mcp -->

Cities2 MCP and Modding Toolkit is a local MCP server and agent skill bundle for Cities: Skylines II.

It gives AI agents access to a local, searchable version of the Cities: Skylines II Wiki. It also lets them search the game encyclopedia, if the game is installed locally. This gives them the ability to answer general knowledge questions about playing the game and offer advice on how to solve problems in your city. It includes agent skills for creating, inspecting, building, and packaging CS2 mod projects. The modding skills are designed to ensure that mods built with this plugin conform to the best practices documented in the wiki.

## Quick install

Choose your client: [Claude Code](INSTALL.md#install-in-claude-code) | [Claude desktop](INSTALL.md#install-in-claude-desktop) | [Codex CLI](INSTALL.md#install-in-codex-cli) | [Codex app](INSTALL.md#install-in-the-codex-app) | [Google Antigravity](INSTALL.md#install-in-google-antigravity)

See [INSTALL.md](INSTALL.md) for full installation details, direct MCP config,
workspace setup, build prerequisites, and troubleshooting.

## What it can do

### Search game and modding information

The MCP server includes a prepared text corpus from the Cities: Skylines II Wiki. An AI assistant can:

- search the wiki
- retrieve reference-style snippets for game systems and modding topics
- answer questions about game mechanics and how they affect your city

### Search the local game encyclopedia

When Cities: Skylines II is installed locally, the MCP server reads the game encyclopedia from the installed game files. This source is enabled by default when the server can find `Cities2_Data/Content/Game/Locale.cok`.

The extracted encyclopedia index is cached locally on the user's machine and rebuilt only when the source game file, detected Steam build id, locale, or extractor version changes. Extracted game text is not committed to this repository, shipped in releases, or part of the redistributed wiki corpus.

### Help with mod project workflows

The server also includes local workflow tools for CS2 mod projects. An AI assistant can:

- scaffold C# code, UI, or hybrid mod project templates
- write files inside configured workspaces
- list project trees
- run project builds and analyzers
- package project output

These tools are meant for local development workflows. Claude, Codex, and Antigravity can use them to write and run trusted workspace code during builds, so configure workspaces deliberately and use manual playtesting.

## Agent skills

- [`cities2-knowledge`](skills/cities2-knowledge/SKILL.md): answers gameplay, city-system, and player-facing patch/update questions.
- [`cities2-modding`](skills/cities2-modding/SKILL.md): handles general modding questions and local mod project workflows.
- [`cities2-mod-review`](skills/cities2-mod-review/SKILL.md): reviews CS2 mods for safety, maintainability, user value, packaging hygiene, and verification gaps.
- [`cities2-mod-debugging`](skills/cities2-mod-debugging/SKILL.md): helps debug CS2 mod build, packaging, runtime, log, UI debugger, and in-game behavior issues.
- [`cities2-mod-release`](skills/cities2-mod-release/SKILL.md): checks whether a mod is ready to share.

The modding quality skills use documented CS2 best practices and negative constraints as defaults, and they do not present a mod as ready to share until it has been locally playtested.

## Privacy

The MCP server runs locally and does not collect telemetry. See
[PRIVACY.md](PRIVACY.md) for details.

## Licensing

The MCP server code is licensed under the MIT License. The included `cities2_mcp/data` corpus is licensed under Creative Commons Attribution-ShareAlike 3.0; source attribution and transformation notes are in `cities2_mcp/data/ATTRIBUTION.md`.

This project is not developed by, endorsed by, reviewed by, or approved by
Paradox Interactive, Iceflake Studios, Colossal Order, Paradox Wikis, or any
related company. Cities: Skylines II and related names are used referentially.
