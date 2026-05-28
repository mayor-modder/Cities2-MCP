---
name: cities2-game-updates
description: >-
  MUST use automatically when a user asks what is new, changed, fixed, patched,
  added, removed, improved, or currently known-broken in Cities: Skylines II,
  including patch notes, game updates, recent releases, version summaries,
  codenames, DLC/asset-pack fixes, traffic changes, UI changes, modding changes,
  editor changes, or known issues.
---

# Cities2 Game Updates

Use this skill to answer user-facing questions about what changed in Cities: Skylines II. The goal is to turn patch notes and changed wiki pages into a clear player/modder summary, not to expose raw corpus maintenance details.

## Source Roles

- **Wiki corpus**: Primary source for patch history, release notes, new feature/fix lists, DLC notes, and public wiki update pages.
- **Game Encyclopedia**: Useful for explaining current in-game terminology that appears in patch notes, but it usually does not replace patch notes.
- **Live web**: Use only when required by the user or when they ask for the latest/current state beyond the bundled corpus.

## Workflow

1. Call `source_status()` first so you know whether local sources are available.
2. Search the wiki with compact patch/update terms:
   - `Patch 1.5.9`, `Morning Dew patch`, `latest patch`, `game history`, `patch notes`
   - Feature phrases from the user's question, such as `vehicles U-turns`, `coal power plant`, `zone cell grid`, `Modding.log`
3. Use `query_reference(query, limit=5)` when routing to the best page is unclear.
4. Fetch the strongest pages with `get_page(page_id)`, especially patch pages such as `patch-1-5-x`, `patches`, or `main-page-news`.
5. If search ranking favors hub pages, use the exact page ID from results or page metadata instead of repeating title-only searches.
6. If the user asks what the update means, translate the notes into practical impact for players and modders.

When a local workspace or bundled corpus is available, check it directly before declaring it stale. For a newly refreshed corpus, exact page reads and feature-phrase searches can succeed even when broad title searches rank older hub pages first.

Search snippets are routing evidence, not enough for a "what changed?" answer. Once the latest version or patch-family page is identified, read the exact patch page or exact version chunks before summarizing gameplay, UI, modding, editor, DLC, or known-issue changes. If MCP page reads are unavailable but the repo corpus is local, inspect `data/index/chunks.jsonl` rows for the patch page ID and version section.

## Answer Pattern

For broad "what's new?" questions, group changes by audience:

- Gameplay and simulation.
- UI and player-facing fixes.
- Visuals, performance, logging, and crashes.
- Modding and editor workflow changes.
- DLC, Creator Pack, Region Pack, or asset fixes.
- Known issues.

Use plain English. Keep exact version numbers, release dates, and codenames when the source has them, but avoid dumping raw patch-note bullets.

## Querying Well

Do not rely only on page-title searches. Hub pages such as `Patches`, `Modding`, or `Cities Skylines 2 Wiki` can rank above the exact patch or asset page because they link to many related pages.

Before using live web results for a "latest update" answer:

1. Query the likely current version number or codename.
2. Query `Patches` and `Main Page/news`.
3. Fetch the exact patch-family page when it appears, such as `patch-1-5-x`.
4. Inspect the returned page's `oldid`, sections, release date, and patch version.

Only say the local corpus is stale after checking exact version/codename terms and exact patch pages. If live web is newer, say which local page or corpus date lagged behind which live source.

When the user or context imposes a small query budget, spend it like this:

1. Find the latest version/date with `latest patch game history patch notes`.
2. Read the exact patch page or exact version chunks. For Patch 1.5.x, that means `get_page("patch-1-5-x")` or `data/index/chunks.jsonl` rows where `page_id` is `patch-1-5-x` and `section` is the exact version, such as `1.5.9f1`.
3. Use one targeted feature/modding query only if the exact patch text is still unclear.

Do not spend limited queries on older expansion, DLC, or diary pages after identifying a newer patch version. Do not use older update pages as substitute context for "what's new" in the current patch. If the exact patch page exists but you cannot read its detailed notes within the query budget, report that as a retrieval limitation instead of summarizing unrelated older releases.

Good query examples:

- User: "What's new in the latest patch?"
  Query: `latest patch game history patch notes`
- User: "Did traffic change?"
  Query: `vehicles unnecessary U-turns turn lanes highway exits intersections`
- User: "Anything for modders?"
  Query: `Modding.log active playset enabled mods mod loading background download`
- User: "What does Morning Dew do?"
  Query: `Morning Dew Patch 1.5.9`

## Source Notes

Include a compact source note when sources were used, for example:

`Sources used: CS2 Wiki pages Patch 1.5.X and Patches.`

Use Markdown links for wiki URLs when available. If the user asks for "latest" and the bundled corpus might be stale, state the corpus source date or use live web verification when required.
