# Cities2 research

This directory holds canonical research reports used to generate the separately identified `cities2-research` MCP dataset.

## Private source intake

Put full transcripts, downloaded media, slide decks, and other private working material under `sources/`. Everything below that directory is ignored except its `.gitignore`; never force-add source material.

## Canonical reports

Commit original research summaries under `reports/`. Name each report `<published_at>-<slug>.md` and follow the metadata and section structure demonstrated by the existing reports.

`published_at` must be an exact publication date. Use `publication_date_basis: source_metadata` when supplied material or a public source establishes the date, and `publication_date_basis: user_confirmed` when the maintainer confirms a date that was otherwise unclear. Do not infer the date from local file metadata or an event name.

## Generate and verify

Run `python -m cities2_mcp.research sync` after editing reports. Review the generated `cities2_mcp/research_data/` diff, then run `python -m cities2_mcp.research check`.
