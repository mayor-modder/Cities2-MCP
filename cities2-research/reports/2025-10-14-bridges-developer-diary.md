---
schema_version: 1
title: Bridges and Ports Developer Diary #1 - Bridges
slug: bridges-developer-diary
source_type: developer_diary
source_url: https://forum.paradoxplaza.com/forum/developer-diary/bridges-bridges-ports-developer-diary-1.1862912/
published_at: 2025-10-14
publication_date_basis: source_metadata
creators: Colossal Order development team
organizations: Colossal Order; Paradox Interactive
report_created_at: 2026-07-20
report_updated_at: 2026-07-20
event: Bridges and Ports expansion developer diary
---

# Bridges and Ports Developer Diary #1 - Bridges

## Executive summary

This expansion diary adds one distinctive network mechanic: movable bridges synchronize ship passage with road, rail, transit, or pedestrian traffic. A movable section appears only where the bridge crosses a Narrow Seaway. The bridge stays closed until a ship approaches, stops new entrants, waits for occupants to clear, opens for the vessel, then closes and releases land traffic.

This creates a deliberate capacity tradeoff. A movable bridge preserves a low crossing but imposes a much longer interruption than a signal cycle whenever ships pass. The source also documents double-deck bridges as compact composite networks, including decks that can continue toward different destinations.

## Source context and temporal scope

Colossal Order published the diary on 2025-10-14 before the Bridges & Ports expansion's scheduled 2025-10-29 release. It previews 20 expansion bridges and uses marketing language alongside mechanical explanation.

Actual released asset availability, ownership requirements, fixes, and later behavior should be checked against current expansion and patch documentation.

## Findings

### Movable sections depend on Narrow Seaways

The ten movable bridges include five bascule or drawbridge variants and five vertical-lift variants. They can be built elsewhere like ordinary bridges, but the animated movable section appears only when crossing a Narrow Seaway.

Drawbridges include road and pedestrian variants. Lift designs serve train, tram, subway, and a combined highway-and-rail bridge, reflecting their suitability for heavier loads.

### Opening is a staged traffic-control process

Movable bridges are normally closed. When a ship approaches, traffic at both ends is stopped while vehicles or pedestrians already on the bridge clear it. Only then does the bridge open. After the ship passes, it closes and traffic resumes.

The interruption can be materially longer than a red light. Busy land crossings with frequent ship movement need alternative capacity or a higher fixed bridge.

### Double-deck bridges are composite corridors

Additional double-deck bridges stack road networks, highway carriageways, or road and rail within one structure. The two-lane-over-four-lane example allows the decks to connect to different parts of the city or continue as a stacked network. This is not merely a visual variant: each deck has its own connectivity and capacity.

### Regular bridges retain upgrade behavior

The expansion also added fixed pedestrian, road, highway, subway, and other bridge designs. Suitable road bridges can receive public-transport upgrades such as bus lanes or tram tracks. Large suspension variants can span Medium and Wide Seaways, unlike movable bridges' Narrow Seaway trigger.

## Existing corpus overlap

Expansion and patch pages provide the released asset roster. This report adds the clearest event sequence for a bridge opening, the Narrow Seaway trigger, the resulting land-traffic tradeoff, and the independent connectivity of double-deck networks.

The ports diary is already synthesized in the modular-ports tutorial report and was not duplicated here.

## Implications for Cities2 modding

Traffic tools should model a movable bridge as a stateful conflict between seaway and land-network reservations. Measuring average lane capacity without ship frequency and opening duration will misrepresent the bottleneck.

Composite-bridge validation should test every deck and network type independently. A visually continuous structure can still contain a disconnected upper or lower route.

## Implications for Cities2-MCP

Cities2-MCP should use this report for questions about when a bridge opens, why a movable bridge creates queues, why an animated section is absent, or how double-deck connections work.

It should check current content ownership and patch state before recommending a specific expansion asset.

## Uncertainties and transcript corrections

The preview gives no approach distance, clearing timeout, opening duration, ship priority, queue policy, or pathfinding penalty. It does not establish how emergency vehicles are handled during an opening.

MHTML punctuation artifacts were normalized and community replies excluded.

## Sources

- Colossal Order, Bridges and Ports Developer Diary #1 - Bridges, published 2025-10-14: https://forum.paradoxplaza.com/forum/developer-diary/bridges-bridges-ports-developer-diary-1.1862912/
- Cities: Skylines II Wiki, Bridges and Ports: https://cs2.paradoxwikis.com/Bridges_and_Ports
- Cities: Skylines II Wiki, Transportation: https://cs2.paradoxwikis.com/Transportation
