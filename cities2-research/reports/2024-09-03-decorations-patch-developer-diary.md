---
schema_version: 1
title: Decorations Patch Developer Diary
slug: decorations-patch-developer-diary
source_type: developer_diary
source_url: https://forum.paradoxplaza.com/forum/developer-diary/dev-diary-decorations-patch.1701853/
published_at: 2024-09-03
publication_date_basis: source_metadata
creators: Colossal Order development team
organizations: Colossal Order; Paradox Interactive
report_created_at: 2026-07-20
report_updated_at: 2026-07-20
event: Decorations Patch developer diary
game_version: 1.1.8f1 prerelease
---

# Decorations Patch Developer Diary

## Executive summary

This diary combines two unrelated but useful `1.1.8f1` changes. First, it moved a curated set of 298 safe props from developer mode into eight supported Landscaping categories. Placed props have collision, can sit on surfaces, can be relocated or bulldozed, cost nothing, and were described as simulation-neutral. Building-mounted props were omitted because prop placement on buildings was not supported in ordinary gameplay.

Second, it explains the 2024 homelessness fix. Homeless households were changed from randomly checking for housing to always seeking a suitable home. Homelessness reduced new-household spawning while increasing high-density residential demand, giving existing homeless households a better chance to occupy new housing. Affordable households could leave, and outbound public transport could help them do so. Later homelessness changes must supersede this initial fix.

## Source context and temporal scope

The diary was published on 2024-09-03 before patch `1.1.8f1`. It explicitly says the update was smaller than Detailer's Patch #2 and bundled the ready Decorations menu with urgent homelessness fixes.

Its catalog counts and homelessness behavior describe that patch's initial state. Current prop availability, collision, costs, homelessness priorities, and demand effects require newer verification.

## Findings

### Supported decoration is curated

The team selected existing game props that made sense and behaved correctly when independently placed. Eight categories exposed 298 items. Props intended to attach to a building, including chimneys and air-conditioning units, were excluded because ordinary in-game placement on buildings was unsupported.

Props behave like placeable trees or buildings in having size- and shape-based collision. They can be placed over surfaces, relocated through the Selected Info Panel, or bulldozed. They were free and described as having no simulation impact.

### Homeless households gained priority over new arrivals

Citizens become homeless after losing an unaffordable or destroyed home. Those who can afford to leave may depart; those who cannot use parks or abandoned buildings as temporary shelter.

The patch removed the random test controlling whether a homeless household looked for housing. Homeless households would always search for a suitable home. At the demand level, homelessness suppressed creation of new households and raised high-density residential demand so vacant housing was less likely to be filled by newcomers first.

Providing demanded housing and public transport to outside connections was presented as the player's practical intervention. Recovery could still take time in cities with a large backlog.

## Existing corpus overlap

Patch notes and current wiki pages are better for today's homelessness implementation and decoration inventory. This diary adds the explicit prioritization rationale connecting new-household spawning, high-density demand, and re-housing.

The later Detailer's Patch #2 report covers the Line Tool and roadside vegetation controls, which were not part of this release.

## Implications for Cities2 modding

Decoration mods should distinguish world-placeable props from sub-objects intended to bind to buildings. A visible prefab is not automatically safe for independent placement.

Homelessness diagnostics should observe both household search behavior and demand/spawn suppression. Adding housing without allowing the simulation to prioritize existing households can mask the original failure mode.

## Implications for Cities2-MCP

Cities2-MCP should use this report for historical questions about when supported prop placement appeared and how patch `1.1.8f1` tried to clear trapped homelessness.

Newer sources must rank first for present homelessness advice. The report should not imply that every homeless household necessarily finds housing or that every game prop is placeable.

## Uncertainties and transcript corrections

The diary gives no search interval, affordability threshold, demand coefficient, collision schema, or complete prop list. Later patches changed homelessness behavior, so this source is explicitly version-bound.

MHTML punctuation artifacts were normalized and community replies excluded.

## Sources

- Colossal Order, Decorations Patch Developer Diary, published 2024-09-03: https://forum.paradoxplaza.com/forum/developer-diary/dev-diary-decorations-patch.1701853/
- Cities: Skylines II Wiki, Patch `1.1.X`: https://cs2.paradoxwikis.com/Patch_1.1.X
