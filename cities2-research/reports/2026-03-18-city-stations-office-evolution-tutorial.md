---
schema_version: 1
title: City Stations & Office Evolution Tutorial
slug: city-stations-office-evolution-tutorial
source_type: official_sponsored_tutorial
source_url: https://www.youtube.com/watch?v=cthUpLahqyM
published_at: 2026-03-18
publication_date_basis: source_metadata
creators: Sunny Scunny; BadPeanut; Titan
organizations: Paradox Interactive
report_created_at: 2026-07-19
report_updated_at: 2026-07-19
event: Cities: Skylines II official tutorial video
game_version: 1.5.6f1
---

# City Stations & Office Evolution tutorial

## Executive summary

This seven-minute release-day video is an official sponsored overview presented by community creator Sunny Scunny on the Cities: Skylines channel, not a direct Iceflake developer presentation. It contains little unique technical information by itself. Its useful contribution is a compact explanation of how the City Stations and Office Evolution creator packs can be used together: establish high-capacity, multimodal transit hubs and place denser office districts where that access makes urban-design sense.

The associated creator diaries are substantially more valuable. BadPeanut explains that many City Stations assets use custom placeholder objects to randomize platform roofs and colors, and that other asset creators can extend those roof pools through the `Spawnable Object Component`. Titan explains that Office Evolution contains 45 growable buildings across five lot sizes and adds visible changes at every building level, rather than following the base game's usual pattern of unique meshes only at levels one, three, and five.

The video's claims about stations attracting activity and offices responding to transit should be treated as design guidance, not proof of a special simulation link between the two paid packs. Patch `1.5.6f1`, released alongside them, separately increased office demand as the first step of an office-demand rework. That simultaneous balance change can affect what players observe in release-day cities.

## Source context and temporal scope

The video was published on 2026-03-18 on the official Cities: Skylines YouTube channel and runs 7 minutes 9 seconds. Sunny Scunny identifies herself as a UK-based Cities: Skylines II creator collaborating with Paradox Interactive. The video showcases City Stations by BadPeanut and Office Evolution by Titan, both released that day with game version `1.5.6f1`.

This source is closer to a narrated product tutorial than a developer diary. It shows intended uses and visual combinations but does not test capacity, pathfinding, demand, performance, or compatibility. Exact asset counts and authoring details come from the March 16 and March 17 creator diaries; patch behavior and known issues come from the release notes and later patches.

The temporal boundary matters. The initial release listed a road-connection issue for the circular Sunken Subway Park, and patch `1.5.9f1` later corrected several City Stations assets. Current guidance should account for the installed game version rather than treating the launch video as permanent documentation.

## Findings

### The tutorial presents a transit-to-jobs planning pattern

Sunny Scunny organizes City Stations as a progression from trains and buses through trams and subways, then zones Office Evolution around the resulting access. The practical pattern is to use major stations as district anchors, provide local transfers, and concentrate office density near well-connected locations.

That is sensible urban-design advice, but the video overstates the causal chain when it says Office Evolution "responds" to movement and that stations become busier while offices become taller once the systems are aligned. The source does not show a controlled comparison or identify a pack-specific mechanic that couples transit access to Office Evolution leveling. Normal accessibility, demand, profitability, and building-level systems remain the safer explanation.

### City Stations mixes repeatable stations with landmarks

BadPeanut's diary says the pack was structured around four intra-city modes—bus, tram, train, and subway—with two repeatable stations and one landmark station planned for each mode, plus compact or functionally distinct depots. The released pack contains 22 service buildings, 20 service upgrades, and 14 placeable props.

The tutorial highlights several useful combinations without enumerating everything. The City Central Train Station begins as a large terminal and can add underground through tracks, a subway interface, and botanical gardens. The creator diary adds that its base form has 12 platforms and an integrated eight-vehicle rail yard. This makes it both a passenger hub and fleet-capacity asset rather than a station facade alone.

Other stations include deliberate upgrade tradeoffs. The Sunken Subway Park can replace its central park with a deeper level containing eight additional platforms, which reduces the attraction value. Bypass train and subway stations can add platforms while preserving routes for through traffic. Several bus, tram, train, and subway buildings can add interfaces for another transport mode.

### Many transit assets also provide leisure or attraction

Several City Stations buildings double as public spaces. Bus stations and tram plazas provide park leisure; the Sunken Subway Park supports picnicking, yoga, and watching trains; pedestrian overpasses provide a small amount of attraction. These functions mean placement can affect more than passenger transfer capacity.

The creator diary says upgraded shelters offer greater waiting comfort and suggests passengers may prefer a line using them. The current in-game encyclopedia confirms that shelters provide a nicer waiting place, especially in bad weather, but does not establish the claimed route-choice priority. That stronger behavior should remain creator-described until verified in runtime or code.

Pedestrian overpasses can snap to road centers or be placed freely, but their stairs still need pedestrian connections. The medium, large, and extra-large versions can add median access where an appropriate road and wide-sidewalk upgrade exist. BadPeanut recommends combining them with the crosswalk tool to remove nearby surface crossings; the tutorial's joke about banning crosswalks should not be treated as a requirement.

### Placeholder roofs expose a useful asset-modding extension point

The most technically interesting discovery is in the City Stations creator diary rather than the video. Repeatable stations use custom placeholder objects for platform and concourse roofs. Placement randomly chooses one of two supplied roof designs, and roof colors vary independently from the main building. This gives repeated stations visual variation without requiring separate station assets.

BadPeanut says another asset creator can add compatible roofs to a station's random selection pool by assigning the station's custom placeholder object in the new roof's `Spawnable Object Component`. This is a concrete, creator-tested extension mechanism and a useful candidate for future toolkit guidance or snippets. It still needs versioned editor/API verification before being turned into generated code.

The roof objects are technically sub-objects that function as props. Most were exposed as placeable landscaping props, including 11 pavilion pieces whose collision geometry is limited to their structure or supporting pillars. Players can therefore build beneath much of the roof area while avoiding the supports.

### Office Evolution is visually medium-density despite its zone category

The game categorizes Office Evolution as a new high-density office zone. Titan designed it to fill what he regarded as a missing medium-density visual tier between single-story suburban offices and very tall vanilla high-rises. Toolkit answers should preserve both facts: it uses high-density office zoning mechanics, but its architectural purpose is a less extreme office district.

The pack contains 45 growable buildings across 2x2, 3x2, 3x3, 4x4, and 5x6 lots, plus three signature buildings. Titan says most growables visibly transition from historic to modern architecture as they level, with small changes at every level. He contrasts this with the usual base-game pattern in which levels one, three, and five receive unique meshes while intermediate levels mainly add props.

The tutorial accurately shows old facades persisting while glass, steel, rooftop terraces, and larger additions appear. The three signature buildings provide more dramatic compositions; Frankfort Court has a tower upgrade. These are authored visual progressions, not evidence that real construction history or redevelopment is separately simulated.

### The release patch can confound observations about the packs

Patch `1.5.6f1` shipped on the same day and increased office demand as the first step of a broader office-demand rework. A player seeing Office Evolution grow quickly on release day may therefore be observing both the new zone content and a base-game balance change.

The release also introduced road-side zoning toggles, the first version of the in-game Encyclopedia, and unrelated fixes. Those features are not part of either creator pack even though they appear in the same release announcement.

The initial known issues said some round buildings were treated as having square footprints, making road connections difficult for the Sunken Subway Park. Patch `1.5.9f1` later fixed unlock criteria for the Compact Bus Depot, reversed bus-lane direction in the Small Bus Terminal, corrected misplaced lighting at City Central Train Station, improved a sharp-angle connection for the Compact Refurbished Tram Depot, and fixed erroneous road requirements for the Small Tram Plaza. These later notes supersede the launch tutorial for troubleshooting.

## Existing corpus overlap

The wiki corpus already has dedicated City Stations and Office Evolution pages with release dates, asset counts, lot sizes, names, store links, and links to both creator diaries. It also indexes the tutorial itself. For basic questions such as what each pack contains, the wiki pages are more complete than the transcript.

The report adds value by separating the video's planning advice from hard mechanics, preserving the release-patch confound, and extracting the creator diaries' more technical material. The strongest unique item for modding is the placeholder-roof extension point. The strongest design item is Office Evolution's deliberate high-density-mechanics versus medium-density-appearance distinction.

## Implications for Cities2 modding

The City Stations placeholder system is worth investigating directly in installed assets and editor metadata. A future toolkit workflow could identify a station's custom placeholder object, scaffold a compatible roof sub-object, assign it through `Spawnable Object Component`, and verify alignment and collision behavior. The diary proves the intended pattern but does not document stable type names, serialization details, or compatibility guarantees.

Asset analysis should distinguish a service building, its upgrades, sub-buildings, placeholder-spawned sub-objects, and user-placeable props. The same visual component may participate in more than one authoring workflow, as the exposed pavilion roofs demonstrate.

Mods or reports comparing office growth before and after March 18 must control for patch `1.5.6f1`'s office-demand increase. Otherwise a change attributed to Office Evolution may actually be a global balance change.

Troubleshooting for City Stations should be version-aware. Advice about the Sunken Subway Park footprint or the five assets corrected in `1.5.9f1` should not be offered without checking the game version and whether the affected building was placed before or after a relevant fix.

## Implications for Cities2-MCP

This report should be retrieved for questions about the tutorial, how the two packs complement one another, City Stations upgrade tradeoffs, Office Evolution's visual density, or extending the randomized station roofs.

For exhaustive asset lists, supported lot sizes, or current store descriptions, Cities2-MCP should prefer the dedicated wiki pages and official pack listings. For exact launch-patch behavior and later fixes, it should retrieve `Patch 1.5.X` rather than relying on the video.

Answers should label the transit-and-office relationship as a planning strategy. The report does not support claims that buying both packs unlocks a unique simulation bonus, that transit automatically causes Office Evolution buildings to level, or that every shelter definitively changes route choice.

The placeholder-roof workflow should be presented as creator-documented and pending installed-asset verification. It is promising evidence for toolkit development, not yet a complete public API recipe.

## Uncertainties and transcript corrections

The transcript is auto-generated and mistranscribes Sunny Scunny's name, City Stations, Cities: Skylines II, facades, and several asset names. Names and technical terms in this report were normalized against official listings and the creator diaries.

The tutorial uses promotional language and does not disclose test conditions. Statements about reducing out-of-service travel, improving transfers, increasing station use, encouraging office growth, or giving districts personality are reasonable design interpretations but are not quantified findings.

The creator diary's statement that passengers may prioritize comfortable shelters is stronger than the current encyclopedia wording and has not been independently verified. Likewise, the exact implementation of placeholder spawning should be confirmed against the installed game/editor before toolkit automation depends on it.

## Sources

- Cities: Skylines and Sunny Scunny, original tutorial, published 2026-03-18: https://www.youtube.com/watch?v=cthUpLahqyM
- BadPeanut, Dev Diary - City Stations, published 2026-03-16: https://forum.paradoxplaza.com/forum/index.php?threads/1906527
- Titan, Dev Diary - Office Evolution, published 2026-03-17: https://forum.paradoxplaza.com/forum/index.php?threads/1907696
- Paradox Interactive, Office Evolution & City Stations Available Now!, published 2026-03-18: https://www.paradoxinteractive.com/games/cities-skylines-ii/news/office-evolution-and-city-stations-available-now
- Steam, City Stations product page: https://store.steampowered.com/app/3579770/Cities_Skylines_II__Creator_Pack_City_Stations/
- Steam, Office Evolution product page: https://store.steampowered.com/app/3579780/Cities_Skylines_II__Creator_Pack_Office_Evolution/
- Cities: Skylines II Wiki, City Stations: https://cs2.paradoxwikis.com/City_Stations
- Cities: Skylines II Wiki, Office Evolution: https://cs2.paradoxwikis.com/Office_Evolution
- Cities: Skylines II Wiki, Patch 1.5.X: https://cs2.paradoxwikis.com/Patch_1.5.X
