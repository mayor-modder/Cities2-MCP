---
name: cities2-knowledge
description: MUST use automatically for any Cities: Skylines II gameplay, city-management, or game-mechanics question, even when the user does not mention Cities2-MCP, wiki, Encyclopedia, or sources. Use for plain questions like "How do I grow office demand?", "How do I get more people to use my subway?", "What makes citizens healthier?", "Why is housing demand low?", "How do taxes affect industry?", or "How does zoning/pollution/education/transit work?" Answers use the Cities2-MCP wiki corpus plus the user's local in-game Encyclopedia.
---

# Cities2 Knowledge

Use this skill when answering Cities: Skylines II gameplay questions with Cities2-MCP. The goal is to retrieve focused evidence from both available sources and synthesize a normal answer, not to show raw search results.

## Source Roles

- **Game Encyclopedia**: More authoritative for current in-game wording, broad current mechanics, and terminology because it is read from the user's installed game files.
- **Wiki corpus**: Usually better for player advice, tables, examples, patch history, guide context, and fuller explanations.
- **Conflict handling**: If sources disagree, say so plainly. Prefer the Game Encyclopedia for current in-game terminology/mechanics, unless the wiki result is clearly a newer patch-specific note.

## Workflow

1. Call `source_status()` first.
2. Extract 4-10 keyword terms from the user's question. Do not send the whole natural-language question as the primary query.
3. Search the wiki with `search(query, limit=5)`. Use `query_reference(query, limit=5)` if page-level routing would help.
4. Search the Game Encyclopedia with `search_encyclopedia(query, limit=5)` when `source_status()` reports it is available.
5. Fetch fuller evidence:
   - Use `get_page(page_id)` for the best wiki page when snippets are not enough.
   - Use `get_encyclopedia_entry(entry_id)` for the best Encyclopedia entries.
6. Answer from the retrieved material. Explain what to do and why, with short source labels such as `Wiki` and `Game Encyclopedia` when useful.

## Querying Well

Use compact gameplay terms. Prefer nouns and mechanic names over conversational wording.

Examples:

- User: "How do I grow office demand?"
  Query: `office demand jobs education companies zoning workplace commercial industrial`
- User: "How do I get more users to use my subway system?"
  Query: `subway public transportation passengers stops comfort traffic bus train citizens`
- User: "What makes citizens healthier?"
  Query: `health healthcare citizens sick pollution noise deathcare hospital clinic welfare`

If the first search misses, rewrite the query with related in-game labels from the source results. For example, try `public transportation passenger transportation subway stations` after a subway query.

## Answer Style

- Synthesize; do not list every hit.
- Mention the Game Encyclopedia being unavailable only when it affects the answer.
- Be careful with guide-style claims. Phrase them as advice when they come from wiki guide pages, not as hard mechanics unless the Encyclopedia or patch notes support them.
- If evidence is thin, say what the sources covered and what they did not cover.
- Do not browse the live web unless the user explicitly asks for current external information.
