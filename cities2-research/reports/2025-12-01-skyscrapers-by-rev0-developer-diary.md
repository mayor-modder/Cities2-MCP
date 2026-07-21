---
schema_version: 1
title: Skyscrapers by REV0 Developer Diary
slug: skyscrapers-by-rev0-developer-diary
source_type: developer_diary
source_url: https://forum.paradoxplaza.com/forum/developer-diary/dev-diary-skyscrapers-by-rev0.1883633/
published_at: 2025-12-01
publication_date_basis: source_metadata
creators: REV0
organizations: REV0; Paradox Interactive; Colossal Order
report_created_at: 2026-07-20
report_updated_at: 2026-07-20
event: Skyscrapers Creator Pack developer diary
game_version: 1.5.2f1 prerelease
---

# Skyscrapers by REV0 Developer Diary

## Executive summary

REV0's creator diary is valuable as a first-party case study in building very large Cities: Skylines II assets. The pack uses upgrades to layer service, recreation, education, transit, utility, safety, and economic functions into signature-building footprints. That establishes upgrades and placeable sub-buildings as a supported way to model vertical mixed use rather than embedding every function in an opaque monolith.

The strongest production lessons concern performance and shaders. REV0 built reusable high-detail components, baked frames and edges into lower-poly parts, and assembled the final structures from those parts. One example fell from roughly two million triangles to 150,000. Rectilinear International Style forms also avoided the triangle cost of curved curtain walls and distortion of parallax interiors on curved faces.

## Source context and temporal scope

The diary was published on 2025-12-01 before the Skyscrapers Creator Pack release. It is written by the pack creator and mixes architectural rationale, workflow observations, asset inventory, and gameplay descriptions.

Its optimization techniques are practical evidence, not universal hard budgets. Current asset requirements and supported components remain authoritative.

## Findings

### Component modeling enables aggressive baking

Rather than modeling a tower as one unique mesh, REV0 created repeatable facade and structural elements. High-poly component detail, including edges and frames, could be baked into low-poly parts and reused in the building assembly.

The Tower of Commerce example was reduced from approximately two million triangles to 150,000. This is evidence that silhouette, repetition, and baked surface detail can preserve perceived scale while reducing geometry; it is not a recommended target for every asset.

### Art direction can solve renderer constraints

Curved modern glass surfaces raise polygon counts and can distort the parallax-interior shader. The rectangular language of International Style towers worked with the glass and parallax shaders rather than against them. The source demonstrates that technical constraints should influence concept selection early, not be treated only as a final optimization pass.

### Color masks need consistent semantic assignment

The pack uses color variation broadly and assigns mask channels to consistent building parts across assets. Consistency makes authored color combinations predictable and helps a collection feel coherent.

### Upgrades can create vertical mixed use

Signature buildings serve as bases for functional upgrades including post, police, fire, schools, universities, healthcare, telecom, electricity, shelters, transit, leisure, and commercial uses. Some upgrades are placeable secondary towers or wings; others modify the main lot or function, and some can be placed multiple times to increase capacity.

This supports a modular asset pattern: visual massing, access, service vehicles, rooftop helicopters, and gameplay effects can be distributed across an upgrade graph. Every module still needs correct paths and access.

### Balance was benchmarked against comparable assets

REV0 created a spreadsheet of base-game and region-pack values and compared size, function, and price while balancing service upgrades. This is a strong general method for custom content: use a peer set rather than inventing costs and capacities in isolation.

### Pathfinding remains a core art requirement

The diary closes by naming pedestrian pathfinding alongside triangle counts and shader work as a central challenge. Complex plazas, roofs, attached towers, and service modules are not complete when the mesh looks correct; their accessible spaces and entrances must work under simulation.

## Existing corpus overlap

The wiki asset corpus defines current mesh, material, color-mask, prefab, path, sub-object, and packaging requirements. This report adds a real production example tying component baking, architectural style, mask discipline, upgrade composition, spreadsheet balancing, and pedestrian validation together.

The general custom-assets diary explains the public Editor workflow and should be paired with this case study.

## Implications for Cities2 modding

Asset-tooling reports should track triangles by component and LOD, identify repeated geometry suitable for baking, and preview parallax interiors on the actual surface curvature. A high total alone does not explain where optimization will preserve the most value.

Complex service buildings should be modeled as explicit upgrade and sub-building relationships where supported, with per-module access and capacity tests. Balance reviews should compare similarly sized official assets and document deviations.

## Implications for Cities2-MCP

Cities2-MCP should retrieve this report for questions about skyscraper optimization, parallax interiors on curved glass, mixed-use service upgrades, color-mask consistency, or how a professional creator balanced a large pack.

The two-million-to-150,000 example must be labeled as one asset case, not a formal polygon limit.

## Uncertainties and transcript corrections

The diary does not publish source files, LOD breakdowns, texture sizes, bake settings, collider budgets, or formal performance measurements. Pack-specific gameplay effects may be rebalanced later.

MHTML punctuation artifacts were normalized and community replies excluded.

## Sources

- REV0, Skyscrapers Developer Diary, published 2025-12-01: https://forum.paradoxplaza.com/forum/developer-diary/dev-diary-skyscrapers-by-rev0.1883633/
- Cities: Skylines II Wiki, Asset Creation: https://cs2.paradoxwikis.com/Asset_Creation
- Cities: Skylines II Wiki, Assets: Importing: https://cs2.paradoxwikis.com/Assets:_Importing
