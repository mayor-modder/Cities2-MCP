---
schema_version: 1
title: Everything New in the Bike Patch Tutorial
slug: everything-new-bike-patch-tutorial
source_type: official_sponsored_tutorial
source_url: https://www.youtube.com/watch?v=ILoq9ocvMsM
published_at: 2025-11-19
publication_date_basis: source_metadata
creators: Timeister
organizations: Colossal Order; Paradox Interactive
report_created_at: 2026-07-19
report_updated_at: 2026-07-19
event: Cities: Skylines II official tutorial video
game_version: 1.4.2f1
---

# Everything new in the Bike Patch tutorial

## Executive summary

This five-minute release-day video is an official sponsored overview presented by community creator Timeister on the Cities: Skylines channel. It accurately introduces bicycles, parking, lanes and paths, new service and transport buildings, parks, and Old Town zoning, but it is not literally an exhaustive account of patch `1.4.2f1`. The full patch notes contain many gameplay fixes and the associated Building for Bicycles diary provides substantially deeper simulation detail.

The most important technical disclosure is how bicycles were added without expanding every citizen's pathfinding comparison from three transport choices to four. When a household car is available, a citizen compares walking, driving, and public transport. When no car is available, the citizen compares walking, cycling, and public transport. This conditional choice was explicitly designed to avoid a noticeable performance cost from evaluating another mode for every trip.

Bicycle adoption is therefore not controlled by lanes alone. It depends on household car availability, destination parking, and the existing pathfinding cost factors of Time, Comfort, Behavior, and Money. Dedicated paths have the highest bicycle Comfort score, followed by on-road lanes and then mixed carriageway travel. Later patches materially changed bicycle balance, so the launch tutorial should not be used as current tuning: `1.5.4f1` reduced bicycle trips by 80%, and `1.5.7f1` strengthened the Urban Cycling Initiative.

## Source context and temporal scope

The video premiered on 2025-11-19 on the official Cities: Skylines YouTube channel and runs 5 minutes 13 seconds. Timeister identifies the presentation as a collaboration with Paradox Interactive. Patch `1.4.2f1`, known as the Bike Patch, was released the same day as free base-game content.

This was historically one of Colossal Order's final Cities: Skylines II updates before development transferred to Iceflake Studios at the start of 2026. Paradox's November 17 transition announcement explicitly said Colossal Order would deliver the Bike Patch and additional editor asset support before leaving. The tutorial is therefore official release material from the Colossal Order period, not an Iceflake presentation.

The source is a narrated feature showcase rather than a controlled test or developer talk. The November 18 Building for Bicycles diary is the primary source for travel-choice logic, parking, comfort, policies, and performance rationale. The full patch notes are the primary source for asset lists, bug fixes, and modding changes.

## Findings

### Bicycle choice is conditional on household car availability

Before bicycles, the game compared walking, driving, and public transportation when choosing a route. Colossal Order says adding bicycles as a fourth simultaneously evaluated option would have caused a noticeable performance impact. Instead, the Bike Patch kept the comparison to three modes by checking household car availability first.

If a household has an unreserved car, citizens compare walking, driving, and public transport. If driving wins, the citizen reserves the car so another household member cannot use it. If the household has no car or its car is already reserved, the citizen compares walking, cycling, and public transport, including multimodal combinations where appropriate.

This means a bicycle is not simply considered alongside every other mode on every trip. Household members indirectly affect one another's travel choices by reserving the shared car. A household with a car may still produce bicycle trips when that car is unavailable, while the Urban Cycling Initiative increases cycling partly by lowering the probability that a citizen reserves the car.

### Bicycles are abstractly available but must be parked during trips

All households are treated as having enough bicycles for every eligible member. Teens, adults, and seniors can cycle; children were not supported at launch because the implementation reused animations across supported character models.

When a citizen chooses a bicycle, it belongs to that citizen for the remainder of the trip. It cannot be put away between trip legs, so a parking space is needed while the citizen works, shops, visits a park, or transfers to public transportation. Once the citizen completes errands and returns home, the bicycle returns to household storage and any household bicycle may be used on a later trip.

Destination parking is therefore a mode-viability constraint rather than decoration. If parking repeatedly cannot be found, a citizen may choose public transport or driving instead. The tutorial correctly emphasizes adding parking near shops and transit; the diary extends that advice to schools, offices, and industrial workplaces.

The smallest network-mounted parking objects hold 2, 8, and 10 bicycles. Larger buildings range from a 16-space one-tile storage building to an Underground Bicycle Hall with 452 base spaces and repeatable 50-space sub-building upgrades. Exact capacity questions should use the diary or installed prefab data rather than the overview video.

### Path Comfort can outweigh a shorter route

Bicycle pathfinding uses the game's existing cost dimensions: Time, Comfort, Behavior, and Money. Standalone bicycle paths have the highest bicycle Comfort, followed by painted on-road bicycle lanes. Riding in ordinary vehicle lanes is allowed by default but is less comfortable.

Cyclists may therefore take a slightly longer dedicated route rather than the shortest mixed-traffic route. The tutorial states this directly and the developer diary confirms the ordering. A road that appears geometrically optimal is not necessarily the preferred bicycle route.

On-road bicycle lanes are road-service upgrades and replace parallel roadside parking. Almost all non-highway roads can accept them, including roads with bus lanes or tram tracks. Standalone one-way and two-way paths can connect to road sidewalks like pedestrian paths, can be elevated or tunneled, and can be combined with divided pedestrian-bicycle paths and wide quays. Cyclists slow when crossing the sidewalk during a path-to-road transition.

### Restrictions affect carriageway access, not bicycle existence

The Bicycle Restriction road upgrade can be applied to individual segments, while the Bicycle Traffic Restriction policy applies across a district. Both prevent bicycles from using ordinary carriageways, keeping riders on bicycle lanes or forcing them to find another route.

Restrictions can create access problems if bicycle parking remains on a road that cyclists can no longer reach. The developer diary explicitly warns that restricted areas should place parking on roads with bicycle lanes. Toolkit guidance should therefore treat parking reachability and network restrictions as a coupled diagnostic problem.

The Urban Cycling Initiative operates differently. It reduces the probability that citizens reserve the household car, increasing the chance that cycling enters the three-mode comparison, and grants a small health bonus. It does not guarantee that cycling wins if time, comfort, parking, or public transport makes another option preferable.

### The bicycle Info View supports network diagnosis

The default Bicycle Info View shows the reachable bicycle network, dedicated lanes and paths, carriageways, and locations where carriageway cycling is prohibited. A Bicycle Traffic Volume overlay identifies heavily used routes, while the parking view shows occupied and available spaces.

Together these views support a practical diagnosis loop: find destinations with insufficient parking, inspect whether restrictions block access, locate high-volume mixed-traffic segments, and add comfortable shortcuts or lanes. The tutorial mentions parking availability but does not explain the full diagnostic workflow.

### The patch included much more than bicycles

Despite the video's title, it is a selective showcase. Patch `1.4.2f1` also added five service buildings, eight public-transport buildings, five parks, European and North American mixed-use Old Town zones, and new low-density residential variations.

The patch changed building-level resource delivery so industrial companies, warehouses, and outside connections could service upgrade requests. Delivery vehicles could carry resources for multiple targets and accept new requests during a trip, with local surplus prioritized. The stated goal was to reduce traffic in large cities with many simultaneous building-upgrade requests. This is a material simulation change absent from the video.

Other fixes covered tourism, attractiveness, lodging, excessive shopping traffic, signature-building occupancy and bonuses, company resource purchasing, pedestrian connections, crime effects, service-vehicle spawning, crashes, custom-map tile distribution, and the modding toolchain. The Paradox SDK moved to version `1.39.2`. The tutorial should never substitute for the complete patch notes when answering what changed in `1.4.2f1`.

### Later patches changed the launch balance

Patch `1.5.4f1`, released in February 2026, reduced bicycle trips by 80%. Patch `1.5.7f1` later increased the Urban Cycling Initiative's bicycle-usage effect from 20% to 50%. These changes mean the November 2025 tutorial remains valid for system structure but not for original mode-share expectations.

Later traffic and pathfinding patches also changed route behavior more broadly. Any current diagnosis should combine this foundational bicycle model with the installed game version and subsequent patch notes.

## Existing corpus overlap

The wiki corpus already contains the full `1.4.2f1` content and fix list and indexes Building for Bicycles under developer diaries. For exact asset names or an exhaustive change log, the `Patch 1.4.X` page is stronger than the transcript.

The report's main added value is synthesis. It connects the tutorial's player-facing advice to the diary's conditional three-mode comparison, explains household car reservation as a bicycle gate, distinguishes abstract household bicycle availability from destination parking, and preserves later bicycle-balance changes.

The local game encyclopedia currently provides general policy and transportation terminology but did not surface dedicated bicycle entries in search. For bicycle-specific mechanics, the versioned diary and patch sources are presently more informative.

## Implications for Cities2 modding

Mods analyzing or changing mode choice should not assume that walking, driving, cycling, and public transport are scored together. Car availability determines which three-option set is evaluated. A mod that adds a transport mode or forces bikes into every comparison could reintroduce the performance cost the original implementation deliberately avoided.

Household vehicle reservation, bicycle parking availability, route Comfort, restrictions, and district policy are all relevant inputs to observed bicycle use. Diagnostics that look only at bicycle-lane coverage will miss important causes.

The developer's explicit performance tradeoff is useful architectural evidence but not a stable API contract. The diary does not name ECS components, systems, update phases, or callable interfaces. Installed assembly and prefab inspection remains necessary before implementing bicycle-aware toolkit code.

Version-aware testing is essential. A test city's bicycle share under `1.4.2f1`, `1.5.4f1`, and `1.5.7f1` reflects different balance. Reports should record the game version, relevant district policies, parking supply, household car availability where observable, network restrictions, and route comfort.

The patch's multi-target upgrade-resource delivery is another modding-relevant change. Traffic or logistics mods built against earlier one-request assumptions may misinterpret delivery-vehicle behavior after `1.4.2f1`.

## Implications for Cities2-MCP

This report should be retrieved for questions about bicycle mode choice, why citizens are not cycling, the relationship between cars and bikes, bicycle parking, comfort, restrictions, the Urban Cycling Initiative, or what the tutorial omitted.

For an exhaustive `1.4.2f1` change list, Cities2-MCP should prefer `Patch 1.4.X`. For the bicycle decision model, Building for Bicycles is the primary source. Current bicycle-volume advice must also retrieve later `1.5.X` changes.

A useful troubleshooting answer should proceed in this order: confirm an eligible citizen and version, check whether car availability excludes cycling from the initial comparison, verify destination parking and its reachability, inspect restrictions and network continuity, compare route comfort and time, and then inspect the district policy and traffic overlay.

The toolkit should not promise that adding lanes automatically creates cyclists. Lanes improve Comfort, but cycling must first enter and then win the relevant pathfinding comparison, with usable parking at the destination.

## Uncertainties and transcript corrections

The supplied transcript is auto-generated and renders Timeister as "Tim Meister," omits punctuation, and inconsistently transcribes Cities: Skylines II, one-way, bidirectional, and asset names. Names and terminology were normalized against the official patch page and developer diary.

The video makes no measurements of congestion, mode share, parking occupancy, or route choice. Its statements about bicycles easing road and transit congestion describe intended use, not quantified results.

The developer diary precisely describes the launch decision model, but later patches may have changed internal implementation beyond the published balance adjustments. Current code-level claims require installed-assembly verification.

## Sources

- Cities: Skylines and Timeister, original tutorial, published 2025-11-19: https://www.youtube.com/watch?v=ILoq9ocvMsM
- Colossal Order, Dev Diary: Building for Bicycles, published 2025-11-18: https://www.paradoxinteractive.com/games/cities-skylines-ii/news/dev-diary-building-for-bicycles
- Colossal Order and Paradox Interactive, Bike `1.4.2f1` overview, published 2025-11-19: https://www.paradoxinteractive.com/games/cities-skylines-ii/news/bike-patch-notes
- Colossal Order, full Bike Patch `1.4.2f1` notes: https://steamcommunity.com/games/949230/announcements/detail/633446704518004756
- Paradox Interactive, An Update on Cities: Skylines II, published 2025-11-17: https://www.paradoxinteractive.com/games/cities-skylines-ii/news/an-update-on-cities-skylines-ii
- Cities: Skylines II Wiki, Patch 1.4.X: https://cs2.paradoxwikis.com/Patch_1.4.X
- Cities: Skylines II Wiki, Patch 1.5.X: https://cs2.paradoxwikis.com/Patch_1.5.X
