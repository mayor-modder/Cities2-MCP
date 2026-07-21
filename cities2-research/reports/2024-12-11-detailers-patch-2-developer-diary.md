---
schema_version: 1
title: Detailer's Patch #2 Developer Diary
slug: detailers-patch-2-developer-diary
source_type: developer_diary
source_url: https://forum.paradoxplaza.com/forum/developer-diary/detailers-patch-2-developer-diary.1720275/
published_at: 2024-12-11
publication_date_basis: source_metadata
creators: Colossal Order development team
organizations: Colossal Order; Paradox Interactive
report_created_at: 2026-07-20
report_updated_at: 2026-07-20
event: Detailer's Patch #2 developer diary
---

# Detailer's Patch #2 Developer Diary

## Executive summary

This diary documents a substantial road and detailing release. The most mechanically useful feature is Traffic Routes: selecting a vehicle, pedestrian, road, or building can display persistent routes divided into road, water, air, rail, and pedestrian modes, with line width indicating heavier traffic. This gives mod and city diagnostics a route-oriented view rather than only congestion heat.

The update also added asymmetric roads, parking roads and structures, service-vehicle parking, pocket parks, cul-de-sacs, a spacing-aware straight/curve Line Tool, and a Roadside Tree Selector that accepts all vegetation. Several assets and counts are historical inventory, but the interaction model remains useful.

## Source context and temporal scope

Colossal Order published the diary on 2024-12-11 alongside Detailer's Patch #2. It links full patch notes for fixes and focuses on new features and assets.

Current road assets, parking behavior, route visualization, vegetation compatibility, and service-vehicle staging should be verified against the installed version.

## Findings

### Traffic Routes exposes route composition

The toggle is available from the Selected Info Panel for a vehicle, pedestrian, road, or building. Once enabled, it remains visible until disabled. Routes are categorized by road, water, air, rail, and pedestrian traffic, and thicker lines represent heavier use.

Selecting different entity types answers different questions: a road segment shows contributing trips, a building shows its connections, and an individual shows a specific itinerary. The visualization is evidence of route selection, not by itself proof of why that route won.

### New roads target constrained geometry

Eight roads included one-way gravel, one-way alley, a one-way small pedestrian street, and asymmetric medium, large, and highway configurations. The asymmetric variants add capacity in one direction and can supply turning lanes where flow is imbalanced.

Twelve parking-road variants use angled or perpendicular spaces to construct irregular parking areas. Nine ploppable parking lots and halls include gravel, solar-covered, compact, and multi-level options; the multi-level hall can be upgraded to 300 spaces.

### Service vehicles can stage visibly

Base-game dispatch buildings received dedicated service-vehicle parking where space allowed. Existing buildings had to be re-plopped to gain the new parking locations. That migration detail matters when two otherwise identical saves show different visible staging.

### Detailing tools encode ordered placement

The Line Tool places trees or props along a straight or curved line with adjustable spacing. Trees also expose life-stage selection. The Roadside Tree Selector can replace existing roadside trees or add vegetation without the normal tree-road upgrade, controlling sides and supported medians. All items in the Vegetation menu were said to work with it, including bushes.

The patch also added ten compact parks, seven roundabout decoration families in four sizes, and three cul-de-sac styles.

## Existing corpus overlap

The patch corpus records the asset list and fixes. This diary adds practical behavior of persistent route overlays, line thickness, selection scope, the re-plop requirement for service parking, and how the Line Tool and Roadside Tree Selector differ.

## Implications for Cities2 modding

Traffic debugging tools should preserve modal and selection context. A building-level aggregate, segment flow, and single-agent route are related but not interchangeable observations.

Road or vehicle mods should test asymmetric lane use, roadside parking, service staging, and whether an existing prefab instance needs reconstruction after prefab changes.

Vegetation tools should account for life stage, side, median support, and compatibility with shrubs rather than assuming a tree-only upgrade.

## Implications for Cities2-MCP

Cities2-MCP should use this report for questions about Traffic Routes, service vehicles not appearing in new parking spaces, the distinction between parking roads and lots, and placement behavior of the Line Tool or Roadside Tree Selector.

Current patch and road documentation should answer exact inventory or capacity questions first.

## Uncertainties and transcript corrections

The diary does not define route aggregation windows, line-width thresholds, parking-choice weights, or the prefab migration mechanism. Asset counts and capacities may have changed.

MHTML punctuation was normalized. Community replies were excluded.

## Sources

- Colossal Order, Detailer's Patch #2 Developer Diary, published 2024-12-11: https://forum.paradoxplaza.com/forum/developer-diary/detailers-patch-2-developer-diary.1720275/
- Cities: Skylines II Wiki, Patches: https://cs2.paradoxwikis.com/Patches
- Cities: Skylines II Wiki, Transportation: https://cs2.paradoxwikis.com/Transportation
