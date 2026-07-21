---
schema_version: 1
title: Tile Upkeep Explained
slug: tile-upkeep-explained
source_type: developer_diary
source_url: https://forum.paradoxplaza.com/forum/developer-diary/dev-diary-tile-upkeep-explained.1692037/
published_at: 2024-06-28
publication_date_basis: source_metadata
creators: Colossal Order development team
organizations: Colossal Order; Paradox Interactive
report_created_at: 2026-07-20
report_updated_at: 2026-07-20
event: Economy 2.0 follow-up developer diary
game_version: 1.1.5f1
---

# Tile Upkeep Explained

## Executive summary

This mini-diary supplies the missing model behind Economy 2.0 tile upkeep. The first nine starting tiles are free; later tiles incur annualized administrative upkeep based on each tile's purchase cost. The percentage rises along a curve from 5% toward 25% as more tiles are bought, and the higher percentage applies across purchased chargeable tiles rather than only to the latest tile.

Tile purchase cost reflects available buildable land and resources. Water-heavy tiles are cheaper, which can make an ocean route the least expensive early path to an outside connection. Terrain modification can affect upkeep by changing land inside a tile. Unlocking map tiles through Map Options disables both achievements and tile upkeep, providing an official escape hatch for dispersed village-style saves.

## Source context and temporal scope

Colossal Order published this explanation on 2024-06-28 after patch `1.1.5f1`, responding to questions about the new cost. It describes the initial Economy 2.0 balance and rationale.

Later patches may change percentages, cost inputs, exemptions, or options. Current UI and patch notes should be checked before treating the numbers as present-day constants.

## Findings

### Upkeep is progressive across expansion

The first nine tiles carry no upkeep. Beyond them, each tile's upkeep starts from its purchase cost, multiplied by a percentage that increases from 5% to 25% as the total purchased count grows. Because expansion raises the rate affecting purchased tiles, the marginal fiscal impact can be greater than the displayed cost of one isolated parcel.

The feature was intended to slow late-game territorial expansion and make unused land a continuing budget decision rather than a one-time purchase.

### Tile characteristics matter

Purchase prices account for buildable land, natural resources, and other tile attributes. Water-heavy tiles are generally cheapest. For an early outside connection, the diary recommends buying ocean tiles and extending a bridge or pipeline, or constructing a land bridge.

The note that adding land can affect upkeep implies terrain state participates in valuation. The source does not document when recalculation occurs or which terrain measurements are used.

### Map options offer a different play style

Existing saves with many unlocked tiles can receive a sudden large expense. Enabling `Unlock Map Tiles` when loading disables tile upkeep as well as achievements, allowing rural or multi-village layouts to continue without the intended territorial constraint.

This is a ruleset choice, not an economic fix within the normal progression model.

## Existing corpus overlap

The wiki and patch notes document tile upkeep in the released game. This diary adds the developer rationale, the rate's citywide progression, the relationship between water-heavy tiles and cheap outside connections, and the official option for legacy dispersed saves.

## Implications for Cities2 modding

Map and economy tools should not estimate expansion cost from tile count alone. They need purchase value, free-tile status, the current progressive rate, and any map-option exemptions.

Terrain-changing mods should verify whether valuation updates after land reclamation. Tests should compare the same tile before and after controlled terrain changes rather than assume the diary's qualitative statement reveals the exact calculation.

## Implications for Cities2-MCP

Cities2-MCP can use this report to explain why buying one more tile raises the overall upkeep burden, why water routes can be cheaper, and why a broad rural save may become insolvent after Economy 2.0.

Current version data should be retrieved before quoting 5% to 25% as today's balance.

## Uncertainties and transcript corrections

The source omits the curve formula, accounting period, precise tile-valuation inputs, recalculation timing, and later balance changes. Its graph is described but not preserved as machine-readable data.

Typographic decoding artifacts in the MHTML were normalized. Community replies were excluded.

## Sources

- Colossal Order, Tile Upkeep Explained, published 2024-06-28: https://forum.paradoxplaza.com/forum/developer-diary/dev-diary-tile-upkeep-explained.1692037/
- Cities: Skylines II Wiki, Patch `1.1.X`: https://cs2.paradoxwikis.com/Patch_1.1.X
- Cities: Skylines II Wiki, Maps: https://cs2.paradoxwikis.com/Maps
