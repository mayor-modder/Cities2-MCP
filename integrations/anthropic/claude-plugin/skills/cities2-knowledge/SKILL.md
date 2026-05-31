---
name: cities2-knowledge
description: "Use when answering Cities: Skylines II gameplay, city-management, mechanics, patch/update, or known-issue questions."
metadata:
  short-description: "Answer CS2 gameplay and patch questions"
---

# Cities2 Knowledge

Use this skill when answering Cities: Skylines II gameplay questions with Cities2-MCP. The goal is to retrieve focused evidence from both available sources and synthesize a normal answer, not to show raw search results.

Trigger this skill for plain questions like "How do I grow office demand?", "What changed in the latest patch?", "Did traffic change?", "What makes citizens healthier?", "Why is housing demand low?", or "How does zoning/pollution/education/transit work?", even when the user does not mention this plugin, wiki, encyclopedia, patch notes, or sources.

## Source Roles

- **Game encyclopedia**: More authoritative for current in-game wording, broad current mechanics, and terminology because it is read from the user's installed game files.
- **Wiki corpus**: Usually better for player advice, tables, examples, patch history, guide context, and fuller explanations.
- **Conflict handling**: If sources disagree, say so plainly. Prefer the game encyclopedia for current in-game terminology/mechanics, unless the wiki result is clearly a newer patch-specific note.

## Workflow

1. Call `source_status()` first.
2. Extract 4-10 keyword terms from the user's question. Do not send the whole natural-language question as the primary query.
3. Search the wiki with `search(query, limit=5)`. Use `query_reference(query, limit=5)` if page-level routing would help.
4. Search the game encyclopedia with `search_encyclopedia(query, limit=5)` when `source_status()` reports it is available.
5. Fetch fuller evidence:
   - Use `get_page(page_id)` for the best wiki page when snippets are not enough.
   - Use `get_encyclopedia_entry(entry_id)` for the best encyclopedia entries.
6. Keep track of source titles and URLs:
   - Wiki page title and `url` from `get_page` or search results.
   - Game encyclopedia entry titles from `get_encyclopedia_entry`.
7. Answer from the retrieved material. Explain what to do and why, with short source labels such as `wiki` and `game encyclopedia` when useful.

## Patch And Update Questions

For questions about what is new, changed, fixed, currently broken, patched, or recently released, treat the wiki corpus as the primary patch-note source and the game encyclopedia as supporting terminology.

1. Call `source_status()` first.
2. Search compact update terms such as `latest patch game history patch notes`, `Main Page/news`, `Patches`, a version number, or a codename from the question.
3. Fetch exact pages before summarizing. Read `Main Page/news` or `Patches` to identify the newest listed version, then fetch the patch-family page. If the newest version is in Patch 1.5.X, use `get_page("patch-1-5-x")` and inspect the exact version section.
4. Do not stop at older sections such as `1.5.7f1` if `Main Page/news`, `Patches`, or the patch-family page list newer versions.
5. Summarize practical impact in plain English. Group broad update answers by gameplay/simulation, UI/player-facing changes, visuals/performance/crashes, modding/editor workflow, DLC/asset fixes, and known issues when those categories are relevant.

## Querying Well

Use compact gameplay terms. Prefer nouns and mechanic names over conversational wording.

Examples:

- User: "How do I grow office demand?"
  Query: `office demand jobs education companies zoning workplace commercial industrial`
- User: "How do I get more users to use my subway system?"
  Query: `subway public transportation passengers stops comfort traffic bus train citizens`
- User: "What makes citizens healthier?"
  Query: `health healthcare citizens sick pollution noise deathcare hospital clinic welfare`
- User: "What's new in the latest patch?"
  Query: `latest patch game history patch notes`
- User: "Did traffic change?"
  Query: `vehicles U-turns turn lanes highway exits intersections`

If the first search misses, rewrite the query with related in-game labels from the source results. For example, try `public transportation passenger transportation subway stations` after a subway query.

## Answer Style

- Synthesize; do not list every hit.
- Mention the game encyclopedia being unavailable only when it affects the answer.
- Be careful with guide-style claims. Phrase them as advice when they come from wiki guide pages, not as hard mechanics unless the encyclopedia or patch notes support them.
- If evidence is thin, say what the sources covered and what they did not cover.
- Do not browse the live web unless the user explicitly asks for current external information.

## Source Citation Style

When sources were used, include a compact source note at the end of the answer. Prefer one short sentence or a `Sources:` line, not a bibliography.

Good patterns:

- `Sources used: game encyclopedia entries for Demand and Office Zones, plus the CS2 Wiki Zoning page: https://cs2.paradoxwikis.com/Zoning.`
- `Source note: the game encyclopedia explains the in-game Demand and Office Zones entries; the wiki adds player-facing context from Zoning.`

Use Markdown links for wiki pages when the client supports them. Name the game encyclopedia entries, but do not invent links for them unless the MCP resource URI is directly useful to the user. If the wiki and encyclopedia disagree or emphasize different things, say that briefly in the answer.
