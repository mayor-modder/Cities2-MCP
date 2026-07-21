# Cities2 research corpus design

## Summary

Cities2-MCP will gain a separately identified `cities2-research` corpus for curated research derived from conference talks, videos, interviews, and similar sources. Private source material such as full transcripts will remain in an ignored intake directory, while committed Markdown reports will be the canonical, reviewable source for a deterministic generated JSONL dataset bundled with the MCP server and plugins.

The research corpus will complement rather than modify the existing `cities2-docs` wiki corpus. Search results and retrieved pages will preserve their dataset identity and research provenance so an agent can distinguish current documentation from historically situated developer commentary.

## Goals

- Establish a safe local intake area for full transcripts and other source material that must not be committed or packaged.
- Make committed Markdown reports the canonical research source.
- Require an exact publication date and record how that date was established.
- Generate a deterministic `cities2-research` JSONL dataset from the reports.
- Load the wiki and research datasets together while keeping their identities, attribution, and licensing boundaries separate.
- Include the Unite 2024 ECS talk as the first research report and retrieval fixture.
- Make stale generated output detectable through an explicit check command.

## Non-goals

- Do not ship or commit complete transcripts, downloaded videos, slide decks, screenshots, or other private intake files.
- Do not merge research reports into the CC-BY-SA `cities2-docs` dataset.
- Do not treat historical talks as current API documentation or automatically override newer wiki or installed-game evidence.
- Do not add recency-based ranking, remote transcript downloading, speech-to-text generation, or automatic factual verification in this first version.
- Do not change MCP server or plugin version numbers as part of this feature.

## Repository layout

The canonical and generated files will use the following layout:

```text
cities2-research/
├── README.md
├── sources/
│   └── .gitignore
└── reports/
    └── 2024-10-09-tapping-ecs-cities-skylines-ii.md

cities2_mcp/
├── research.py
└── research_data/
    ├── ATTRIBUTION.md
    ├── manifest.json
    └── index/
        ├── pages.jsonl
        └── chunks.jsonl
```

`cities2-research/sources/` is local intake storage. Its committed `.gitignore` will ignore every child except itself, including nested directories. The repository-level `.gitignore` will also ignore `cities2-research/sources/**` while explicitly allowing the placeholder `.gitignore`, so raw sources remain ignored even if the nested file is removed accidentally.

`cities2-research/reports/` contains the human-authored canonical reports. `cities2_mcp/research_data/` contains generated distribution data and must not be edited manually.

## Report metadata

Each report will begin with a deliberately limited flat YAML-style front matter block. The research compiler will parse only `key: value` scalar fields, reject duplicate or unknown required-field spellings, and avoid adding a runtime YAML dependency.

Required fields are:

```yaml
---
schema_version: 1
title: Tapping the Entity Component System for Cities: Skylines II
slug: tapping-ecs-cities-skylines-ii
source_type: conference_talk
source_url: https://www.youtube.com/watch?v=nEkIyWhvq3o
published_at: 2024-10-09
publication_date_basis: source_metadata
creators: Damien Morello
organizations: Colossal Order; Unity
report_created_at: 2026-07-18
report_updated_at: 2026-07-18
---
```

The compiler will require `published_at` to be a real calendar date in `YYYY-MM-DD` format. The report filename must be `<published_at>-<slug>.md`, and the filename date and slug must match the front matter.

`publication_date_basis` must be either `source_metadata` or `user_confirmed`. `source_metadata` means the publication date is visible in supplied material or a public source page. `user_confirmed` means the maintainer supplied or confirmed the date when the source did not establish it clearly. The compiler will never infer publication date from file timestamps, download dates, event names, report dates, or repository history.

`source_url` must use `https://` or `http://`. Local filesystem paths are forbidden in committed report metadata and generated output. `creators` and `organizations` are semicolon-separated display values so the format remains dependency-free while supporting multiple people or organizations.

Optional flat metadata fields may include `event`, `game_version`, `unity_version`, and `entities_version`. An optional version field must be omitted when the transcript is ambiguous; uncertain values belong in the report's uncertainty section rather than metadata.

## Report structure

Every report will use these second-level sections in this order:

1. `Executive summary`
2. `Source context and temporal scope`
3. `Findings`
4. `Existing corpus overlap`
5. `Implications for Cities2 modding`
6. `Implications for Cities2-MCP`
7. `Uncertainties and transcript corrections`
8. `Sources`

The prose will distinguish direct source claims from analysis and recommendations. Time-sensitive or implementation-specific claims will be described as a snapshot at the source's publication date. Reports will not present internal Colossal Order architecture as a public modding API unless a separate current source establishes that availability.

Reports may use short quotations when necessary, but the default is original summary and analysis. Full transcripts and extensive source reproduction remain in the ignored intake area and are never copied into generated chunks.

## Research compiler

`cities2_mcp/research.py` will expose a development CLI:

```powershell
python -m cities2_mcp.research sync
python -m cities2_mcp.research check
```

`sync` will discover `cities2-research/reports/*.md`, validate metadata and section structure, compile page and chunk records in stable filename order, and atomically replace the generated files under `cities2_mcp/research_data/` only after all reports validate.

`check` will compile the expected output in memory and compare it byte-for-byte with the committed generated files. It will exit nonzero and identify stale or missing generated paths without changing the worktree.

Generation must be deterministic. JSON objects will use stable field ordering, JSONL records will follow report filename and section order, and no wall-clock timestamp will appear in generated content. The manifest will contain `name`, `dataset`, `source`, `page_count`, `chunk_count`, `report_count`, a SHA-256 digest of the canonical report bytes, paths to the indexes, and the attribution filename.

The compiler will create one page per report. It will split the Markdown body on second-level headings and produce section-aware chunks. Sections longer than 4,000 characters will be split on paragraph boundaries with up to 400 characters of overlap. Front matter will not be embedded verbatim in chunk text; instead, the title, publication date, source type, creators, source URL, and temporal-context sentence will be included in each chunk's searchable metadata or preamble.

Every page and chunk record will preserve these research fields:

- `published_at`
- `publication_date_basis`
- `source_type`
- `creators`
- `organizations`
- `report_created_at`
- `report_updated_at`
- `dataset`, set to `cities2-research`

## MCP integration

The generic `Corpus` class already accepts multiple data directories and performs per-dataset fan-out search. The application server will preserve the existing wiki `--data-dir` behavior and add a repeatable `--research-data-dir` option whose default is the bundled `cities2_mcp/research_data` directory. It will construct the corpus with the wiki directory followed by the configured research directories.

Keeping a dedicated research option preserves backward compatibility for callers that override the wiki data directory and makes the source boundary explicit. A caller may repeat `--research-data-dir` for future research collections, while the standard installed server loads the bundled research dataset automatically.

Search, reference, page, and resource results will continue returning `dataset`. When present, `format_doc_result()` and `get_page` will also return the research provenance fields listed above. Wiki results will not gain empty research-only fields.

Tool descriptions and server documentation will describe the bundled sources as the CS2 wiki corpus plus curated research reports. `get_snippets` will continue extracting fenced code across loaded datasets; the first research report contains no code and therefore will not add research snippets.

`source_status()` will report both dataset names, paths, and record counts. A missing optional research dataset will be reported separately from wiki availability, and the wiki knowledge tools will remain usable. A malformed bundled research dataset will produce an explicit research-loading diagnostic rather than being mislabeled as a wiki failure.

## Attribution and source boundaries

`cities2_mcp/data/` remains the transformed wiki dataset under its existing CC-BY-SA terms. `cities2_mcp/research_data/ATTRIBUTION.md` will state that the dataset contains original research summaries and analysis, identify the original sources by report and URL, and explain that complete source media and transcripts are not redistributed.

The research manifest will not claim the wiki corpus license. It will reference its own attribution file and the repository license for original report prose while noting that original linked source material remains subject to its source terms.

Generated research data must not contain absolute paths, source filenames from the ignored directory, or copied transcript blocks. The compiler will reject local-path metadata and tests will scan generated output for the repository user's path and Windows drive-qualified paths.

## First report

The first canonical report will cover Damien Morello's `Tapping the Entity Component System for Cities: Skylines II` session from Unite 2024, published on 2024-10-09. The ignored source intake may contain the supplied auto-generated transcript, but the committed report will link to the public Unity video and contain original synthesis.

The report will cover the prefab-to-ECS boundary, reverse prefab dependencies, runtime asset storage designed for mods, lazy GUID-based asset loading, explicit simulation phases and entity-command-buffer barriers, Burst and job scheduling, data structures that deliberately remain outside ECS, UI data separation, visualization-led debugging, profiler-driven dependency analysis, and long-running pathfinding jobs.

The uncertainty section will normalize obvious caption errors such as `EntityCommandBuffer`, `IJobChunk`, `AsyncReadManager`, `BatchRendererGroup`, Burst, and pathfinding. It will avoid asserting an exact Entities package version because the auto-generated transcript is ambiguous at that point.

## Error handling

The compiler will report all validation errors in one run, prefixed by report-relative path and field or section name. It will not write partial output when any report fails.

Missing or invalid `published_at` values will produce an actionable message that publication date must be confirmed with the maintainer. An absent `publication_date_basis`, a filename mismatch, a missing required section, a non-web source URL, duplicate slug, duplicate page ID, or unsupported schema version will also fail validation.

`check` will distinguish invalid canonical reports from valid reports with stale generated output. This lets contributors correct source metadata before interpreting a generated-data mismatch as a packaging failure.

## Testing strategy

Tests will follow red-green TDD during implementation.

Focused compiler tests will verify valid parsing, exact date validation, rejected missing dates, both permitted date bases, filename/date/slug matching, source URL validation, required section validation, deterministic generation, paragraph-aware chunking, duplicate detection, atomic failure behavior, and stale-output detection.

Retrieval tests will load a small wiki fixture and research fixture together, then verify dataset-qualified IDs, cross-dataset search, research provenance in search and page results, and unchanged wiki result shapes.

Server and packaging tests will verify default dual-dataset startup, independent research diagnostics, wheel inclusion, generated Antigravity vendor inclusion, and plugin package sync/check behavior.

Privacy tests will verify that a representative file under `cities2-research/sources/` is ignored, the placeholder remains tracked, and generated files contain neither private source paths nor full transcript text.

The required repository gates are:

```powershell
python -m cities2_mcp.research check
python -m cities2_mcp.plugin_packages sync
python -m cities2_mcp.plugin_packages check
python -m unittest discover -s tests -v
```

## Documentation

`cities2-research/README.md` will explain the intake-to-report workflow, required publication-date confirmation, report template, sync/check commands, and the rule against committing source material. The root README will mention the research dataset alongside the wiki and local game encyclopedia and explain that research reports are historically situated sources.

`CONTRIBUTING.md` will require contributors to run the research check after editing reports and to obtain maintainer confirmation when a publication date is unclear. Generated plugin metadata files will continue to be updated only through the existing plugin package sync command.

## Delivery boundaries

Implementation will stop after the feature, first report, generated dataset, documentation, and tests are complete and verified. It will not push, open a pull request, merge, publish, release, or bump versions without separate explicit authorization.
