# Design: Runtime Game Encyclopedia Source

## Problem

Cities2-MCP currently ships a prepared Cities: Skylines II Wiki corpus in `data/`. That corpus is useful, but the latest game includes an in-game Encyclopedia whose English text is stored locally in the game install, currently in `Cities2_Data/Content/Game/Locale.cok` as `Glossary.*` records. The Encyclopedia overlaps with the wiki but has distinct, structured, game-shipped content.

We should make this content available to MCP users without redistributing any extracted game text in the repository or release artifacts.

## Goals

- Read the Encyclopedia/Glossary from the user's local Cities: Skylines II installation by default when it is available.
- Keep all extracted game text local to the user's machine.
- Avoid committing, packaging, or publishing extracted game text.
- Rebuild the local Encyclopedia index only when the source game file or detected game build changes.
- Surface a clear non-fatal warning when the game Encyclopedia cannot be found.
- Keep the existing bundled wiki corpus working as a separate source.

## Non-Goals

- Replace the wiki corpus.
- Publish game-shipped text under the wiki corpus license.
- Support every storefront on day one.
- Read non-text image assets from the game files.
- Require the game to be running.

## User Experience

The MCP server enables the game Encyclopedia source by default. During startup it attempts to locate `Locale.cok` automatically. For a typical Windows Steam install, the expected file is:

```text
C:\Program Files (x86)\Steam\steamapps\common\Cities Skylines II\Cities2_Data\Content\Game\Locale.cok
```

If the source file is found, the MCP loads a local cached index or rebuilds it when needed. Search results clearly identify whether they came from the bundled wiki corpus or from the local game Encyclopedia.

If the source file is not found, startup remains successful and wiki tools continue to work. The MCP exposes a visible warning through initialization instructions and source-status diagnostics. The warning tells the user that the game Encyclopedia was not found and points them to configure the game location explicitly.

## Configuration

Discovery is automatic by default. Users can override it with either a game directory or direct `Locale.cok` path.

Inputs:

- CLI: `--game-dir <path>`
- CLI: `--locale-cok <path>`
- Env: `CITIES2_GAME_DIR`
- Env: `CITIES2_LOCALE_COK`

Precedence:

1. `--locale-cok`
2. `CITIES2_LOCALE_COK`
3. `--game-dir`
4. `CITIES2_GAME_DIR`
5. automatic Steam discovery

When a game directory is provided, the server resolves:

```text
<game-dir>\Cities2_Data\Content\Game\Locale.cok
```

## Discovery

Initial automatic discovery focuses on Steam because it is the known common install path.

Windows discovery:

- Check the default Steam library at `C:\Program Files (x86)\Steam`.
- Read `steamapps\libraryfolders.vdf` when present.
- For each Steam library, check `steamapps\common\Cities Skylines II\Cities2_Data\Content\Game\Locale.cok`.
- Read `steamapps\appmanifest_949230.acf` when present for Steam build id metadata.

macOS and Linux discovery should follow the same shape later:

- locate standard Steam library folders
- inspect `libraryfolders.vdf`
- test each candidate for app id `949230`

If automatic discovery fails, the source remains unavailable and the warning explains how to set `CITIES2_GAME_DIR` or `CITIES2_LOCALE_COK`.

## Cache

The extracted Encyclopedia index is stored in a user-local cache directory, not in the repository. Suggested locations:

- Windows: `%LOCALAPPDATA%\Cities2-MCP\cache\game-encyclopedia`
- macOS: `~/Library/Caches/Cities2-MCP/game-encyclopedia`
- Linux: `${XDG_CACHE_HOME:-~/.cache}/cities2-mcp/game-encyclopedia`

The cache contains:

- `manifest.json`
- `entries.jsonl`
- `chunks.jsonl`

The cache manifest includes:

- extractor version
- locale
- `Locale.cok` absolute path
- `Locale.cok` file size
- `Locale.cok` `mtime_ns`
- Steam app id when detected
- Steam build id when detected
- generated timestamp

The cache is reused only when all relevant manifest fields match the current source. It is rebuilt when the source file timestamp, source file size, Steam build id, locale, or extractor version changes.

## Extraction Model

The extractor reads `Locale.cok` and extracts English `Glossary.*` records. The expected record families are:

- `Glossary.TITLE`
- `Glossary.TAB[...]`
- `Glossary.CATEGORY[...]`
- `Glossary.SECTION_TITLE[...]`
- `Glossary.SECTION_CONTENT[...]`

The output model should preserve enough structure to support direct lookup and search:

- entry id
- source key
- title
- tab
- category
- content
- cleaned text
- raw markup text
- locale
- source file metadata
- detected game build metadata

Markup cleanup should produce retrieval-friendly text while preserving a raw field for troubleshooting. Cleanup must be conservative: remove or normalize markup tokens, but do not rewrite game prose except for whitespace normalization and clearly mechanical title spacing cases. The cleanup should handle:

- `<image:...>` references
- `<icon:...>` references
- `<inputAction:...>` references
- bold markdown-style markers
- CRLF normalization
- suspicious title spacing or missing spaces where safe

## MCP Tools And Resources

The existing wiki tools remain available:

- `search`
- `get_page`
- `query_reference`
- `get_snippets`

New game Encyclopedia tools:

- `search_encyclopedia(query, limit=5)`: search only the local game Encyclopedia.
- `get_encyclopedia_entry(entry_id)`: return one full Encyclopedia entry.
- `source_status()`: report wiki corpus status, game Encyclopedia discovery status, cache status, source path, detected build id, and warnings.

For the first release, keep the existing `search` tool wiki-only and use `search_encyclopedia` for game content. This avoids mixing ranking behavior before the game-source result shape has real user mileage. A later release can add combined search once result formatting clearly labels each result's `source`.

Resources should use a distinct URI scheme or prefix, for example:

```text
cities2encyclopedia://entry/{entry_id}
```

## Warning Behavior

Missing wiki corpus remains a blocking docs guard for wiki tools.

Missing game Encyclopedia is non-fatal because it depends on a local game install. The warning appears in:

- server initialization instructions
- `source_status()` output
- debug logs when enabled

The warning text should be direct:

```text
Game Encyclopedia not found. Wiki search is still available. Set CITIES2_GAME_DIR or CITIES2_LOCALE_COK to enable local game Encyclopedia search.
```

## Licensing And Release Constraints

The public repository may include parser, indexing, cache, tests, and documentation code. It must not include extracted game Encyclopedia text.

Release artifacts must not package:

- `entries.jsonl`
- `chunks.jsonl`
- copied `Locale.cok`
- extracted Markdown or JSON previews containing game text

Documentation should state that Encyclopedia results are read from the user's local game installation and are not part of the redistributed wiki corpus.

Tests must use synthetic fixture data that resembles the file structure enough to exercise parsing logic without copying game text.

## Testing

Unit tests:

- Steam path discovery from synthetic `libraryfolders.vdf` and app manifest fixtures.
- explicit path and env var precedence.
- cache hit when path, size, mtime, build id, locale, and extractor version match.
- cache rebuild when any cache key changes.
- parser extraction from synthetic `Glossary.*` records.
- markup cleanup behavior for image, icon, input action, bold, and CRLF cases.
- missing Encyclopedia source produces a non-fatal warning.

Integration tests:

- MCP `tools/list` includes Encyclopedia tools.
- `source_status()` reports unavailable source clearly when no game install is configured.
- `search_encyclopedia` returns an error payload, not an RPC crash, when the source is unavailable.
- with a synthetic local cache, `search_encyclopedia` returns labeled source results.
- smoke test still passes without a local game install.

## Implementation Notes

Likely public repo files:

- `server/game_encyclopedia.py`
- `server/mcp_server.py`
- `tests/test_game_encyclopedia.py`
- `tests/test_mcp_game_encyclopedia.py`
- `INSTALL.md`
- `README.md`
- `.gitignore`

The first implementation should keep extraction and indexing small and dependency-free, matching the current MCP server style. If the cached `entries.jsonl` and `chunks.jsonl` match the existing corpus shape closely enough, reuse the existing `HybridIndex` for ranking.

## Decisions

- Keep wiki and Encyclopedia search separate in the first release.
- Recommend automatic discovery first. Document `CITIES2_GAME_DIR` and `CITIES2_LOCALE_COK` as fixes when discovery fails or when users have a non-standard install.
- Apply conservative cleanup only. Preserve raw game text in cached entries for diagnostics, and use cleaned text only for retrieval and display.
