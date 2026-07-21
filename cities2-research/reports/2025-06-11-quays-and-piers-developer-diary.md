---
schema_version: 1
title: Quays and Piers Developer Diary
slug: quays-and-piers-developer-diary
source_type: developer_diary
source_url: https://forum.paradoxplaza.com/forum/developer-diary/quays-piers-developer-diary.1766166/
published_at: 2025-06-11
publication_date_basis: source_metadata
creators: Colossal Order development team
organizations: Colossal Order; Paradox Interactive
report_created_at: 2026-07-20
report_updated_at: 2026-07-20
event: Quays and Piers Patch developer diary
game_version: 1.3.3f1
---

# Quays and Piers Developer Diary

## Executive summary

This diary explains that quays and piers are functionally different networks, not merely alternative waterfront skins. Quays detect even small elevation changes and form a retaining wall on the lower side; medium and wide variants carry road traffic and accept upgrades, while narrow quays are pedestrian-only. Piers are elevated pedestrian leisure networks that generate visits when connected to the city.

It also supplies an important cargo diagnostic: a cargo terminal's red resource indicator means the building is below its desired reserve, not necessarily that the whole city lacks that resource. Green means storage surplus that the facility will try to export. Terminals aim to maintain a balanced reserve so local companies can restock quickly.

## Source context and temporal scope

Colossal Order published the diary on 2025-06-11 for patch `1.3.3f1`. The content had originally been planned as a free update accompanying Bridges & Ports but was released earlier.

The diary describes the shipped network behavior and cargo-panel interpretation at that date. Later network, cargo, and terrain changes may supersede exact behavior.

## Findings

### Quays are terrain-sensitive retaining networks

Ordinary roads and paths follow terrain and form structures only after substantial elevation change. Quays respond to the slightest change and construct a retaining wall on the lower side, making them easier to align along shorelines. They can extend into water as jetties.

Narrow quays carry pedestrians and appear with paths. Medium and wide quays carry vehicles and sidewalks and support road upgrades including wide sidewalks, trees, bus lanes, and tram tracks.

`Snap to shoreline` is enabled by default. It follows the water edge and maintains a consistent height above the water, adjusted by elevation steps. Disabling it gives more direct height and alignment control and makes a quay follow terrain once out of water.

Quays do not require water and can make terraces. Their retaining side pushes terrain downward, and the diary recommends at least a 10-meter height difference between quay-built terraces.

### Piers generate leisure trips

Narrow, medium, and wide piers are elevated pedestrian networks with a minimum height. Citizens visit them for outdoor leisure, so they need a pedestrian connection to a path, road, or quay. A visually complete but disconnected pier will not function as an accessible leisure destination.

### Cargo-panel colors describe terminal inventory

Cargo buildings try to stock a consistent reserve of all supported resources so industry and commercial companies can refill local storage. Red indicates that the terminal is below its own target and is seeking imports. Green indicates a surplus in the terminal, often from local overproduction, that it will attempt to export.

This prevents a common interpretation error: red is not direct proof of a citywide resource shortage, and green is not proof that an export has already completed.

### Deactivation allows trips in progress to finish

The patch fixed cargo-harbor deactivation so new truck visits stop while already-started trips can complete. Diagnostics immediately after switching a terminal off must therefore distinguish existing assignments from new dispatches.

## Existing corpus overlap

The patch and network corpus document the new assets and fixes. This report adds a concise behavioral distinction between quays and piers, shoreline snapping and terrain deformation, functional leisure connectivity, and the exact interpretation of cargo reserve colors.

The later modular-ports tutorial report covers port modules and ferries more deeply and should take precedence for those systems.

## Implications for Cities2 modding

Quay tools should model which side receives the retaining wall, shoreline snapping, elevation offsets, and terrain deformation. A generic road-placement abstraction can produce unexpected grading.

Pier validation should test path connectivity and leisure visits, not only network continuity. Cargo overlays should label terminal reserve state separately from citywide supply and actual imports or exports.

## Implications for Cities2-MCP

Cities2-MCP should retrieve this report when a user asks why a quay reshapes land, how `Snap to shoreline` behaves, whether piers have gameplay, or what red and green cargo-storage rows mean.

It should avoid saying that a red row proves citywide scarcity or that a disabled terminal instantly cancels every truck already en route.

## Uncertainties and transcript corrections

The source does not define terrain thresholds, leisure attractiveness, cargo reserve targets, dispatch cadence, or export priority. The 10-meter terrace guidance is practical advice, not a disclosed hard validation constant.

MHTML punctuation artifacts were normalized and community replies excluded.

## Sources

- Colossal Order, Quays and Piers Developer Diary, published 2025-06-11: https://forum.paradoxplaza.com/forum/developer-diary/quays-piers-developer-diary.1766166/
- Cities: Skylines II Wiki, Patch `1.3.X`: https://cs2.paradoxwikis.com/Patch_1.3.X
- Cities: Skylines II Wiki, Transportation: https://cs2.paradoxwikis.com/Transportation
