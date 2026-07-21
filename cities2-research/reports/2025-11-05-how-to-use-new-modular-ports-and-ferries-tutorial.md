---
schema_version: 1
title: How to Use the New Modular Ports and Ferries Tutorial
slug: how-to-use-new-modular-ports-and-ferries-tutorial
source_type: official_sponsored_tutorial
source_url: https://www.youtube.com/watch?v=gdEuDLWxLak
published_at: 2025-11-05
publication_date_basis: user_confirmed
creators: BakaNa
organizations: Colossal Order; Paradox Interactive
report_created_at: 2026-07-19
report_updated_at: 2026-07-19
event: Cities: Skylines II official tutorial video
game_version: 1.3.6f1
---

# How to use the new modular ports and ferries tutorial

## Executive summary

This official sponsored tutorial, presented by Cities: Skylines II creator BakaNa in collaboration with Paradox Interactive, demonstrates the transport and industry systems introduced by Bridges & Ports: ferries, offshore oil, fishing, and modular ports. It is a practical placement walkthrough rather than a complete mechanical specification.

The most useful model is that a port is not one cargo-terminal building. It is a bounded logistics complex anchored by an immutable main gate and assembled from quay-mounted cargo interfaces, resource-specific storage, internal roads, auxiliary gates, service buildings, passenger facilities, and an optional intermodal rail terminal. Cargo ships, trucks, trains, and internal Reach Stackers participate in different legs of the flow.

The related Ports & Beyond developer diary contains important rules omitted by the video. Port sub-buildings must be placed within 1 km of the main gate, most upgrades unlock through cargo shipped by sea, and road access that bypasses a port gate imposes a 50% Efficiency penalty. Reach Stackers use dedicated Port Roads, but cargo transfer can continue through a fallback when they cannot reach a facility. These distinctions are valuable for both gameplay diagnosis and mod instrumentation.

The tutorial is time-bounded to game version `1.3.6f1`. Later patches fixed crashes involving the Ferry Terminal, port mail-transfer pathfinding, specialized-industry export trucks, and—most materially—commercial and industrial buildings failing to use Bridges & Ports facilities for imports. Its placement guidance remains useful, but launch-version observations must not be treated as proof of current logistics behavior.

## Source context and temporal scope

The video was published on 2025-11-05, one week after Bridges & Ports and patch `1.3.6f1` released on 2025-10-29. BakaNa describes it as the second of two tutorial videos produced for the expansion. The first covered bridges, zoneable buildings, piers, parks, and signature buildings; this video concentrates on ferries, fishing, offshore oil, and the port system.

Although the video appears on the official Cities: Skylines channel and was made in collaboration with Paradox Interactive, it is presented by a community creator rather than a Colossal Order developer. The official Ports & Beyond developer diary, published 2025-10-21, is the stronger primary source for port constraints and simulation intent. Patch notes are stronger for later behavior changes.

The tutorial shows successful examples but provides no controlled measurements of throughput, travel time, Efficiency, operating cost, or resource volume. Statements such as a road layout working well should be read as build advice, not benchmark evidence.

## Findings

### Ferries use the standard line-and-depot transport pattern

Ferry service requires stops, a completed ferry line, navigable Boatways connected to the stops, and a Ferry Depot with available vehicles. Stops can be attached to quays or placed on a shoreline. The larger Ferry Terminal starts from the shoreline and supports a player-defined pier arrangement.

Lines are created and edited like other public-transport lines: connect stops into a completed loop, drag an existing line onto another stop to insert it, and inspect usage in the Transportation panel. Ferries leave the depot and travel to their assigned route rather than spawning directly on the line.

The depot is therefore a fleet-capacity constraint. In the demonstrated city all ferries were already in use, so the creator added a depot upgrade providing ten more ferries. A line that is geometrically valid but receives no vehicle should be diagnosed for depot existence, fleet capacity, depot-to-line Boatway reachability, and only then passenger demand.

The Ferry Terminal can integrate a bus terminal, making it a multimodal transfer point. The developer diary clarifies the division of labor: passenger ships connect the city to outside connections, while ferries circulate citizens and tourists within the city.

### Offshore oil has separate deep-water and near-shore extraction paths

The Offshore Oil Drilling Hub is the shoreline anchor. Its pier is created through the hub's upgrade menu, and a longer pier provides more landing berths. Oil resource coverage is shown by the purple specialized-industry overlay.

Deep-water extraction uses a Semi-Submersible Oil Platform. The platform and hub require compatible Boatway access plus a completed tanker route; oil tankers spawn after the route becomes operational and move oil from platform to hub.

Near-shore extraction uses the smaller Compliant Tower. It does not require tankers. Instead, it connects directly to the hub with an oil pipeline placed from the upgrade menu, with the connection indicator confirming a valid link.

The two platform types are therefore not interchangeable decorations. They encode different placement depths and transfer networks: tanker route and berth capacity for deep water, direct pipeline continuity for near shore. Storage tank upgrades increase local capacity but do not replace those extraction connections.

### Fishing mirrors parts of the oil pattern but produces a different logistics network

Open-water fishing begins with a Fishing Harbor, a constructed pier, a drawn fishing or fish-farming area, and a route between the harbor and production area. The area must connect to the relevant waterways. Fishing vessels operate on the completed route, and cold-storage buildings can be placed within the industry's upgrade area.

Inland fish farms use a drawn specialized-industry area like land-based farms and do not require the vessel route. They still support the associated cold-storage upgrades. This makes open-water and inland fishing two related production layouts with different network dependencies rather than merely visual variants.

The tutorial also notes Bridges & Ports industrial props, but their use in the demonstration is decorative. Props should not be mistaken for storage capacity or simulated transfer infrastructure.

### The port is a modular logistics campus

The Water Transportation menu provides Small, Medium, and Large Port main gates. The selected main gate establishes the port and exposes its upgrades. The developer diary adds that the gate cannot be replaced with a different size after construction, so initial gate choice determines the available extensions and supported traffic scale.

There are 23 upgrades in the release configuration. The Customs Office is available to Medium and Large Ports, while the Reach Stacker Garage extension is exclusive to the Large Port. Other modules are placeable sub-buildings rather than direct extensions. All sub-buildings must remain within 1 km of their port's main gate.

Most advanced modules are not immediately available in progression play. They unlock as the port ships specified amounts of cargo by sea. A dry port can use already-unlocked modules, but sea shipping is the progression mechanism that opens the full upgrade set.

Container Cranes and Passenger Terminals must be placed on Port Quays because they require vessel access. Storage and land-side facilities can be arranged within the port radius and connected by roads. The result is a distributed service complex whose spatial relationships matter.

### Storage specialization determines what the port can buffer

Ports have four storage families, each available in Small, Medium, and Large sizes:

- Cargo Container Yards and Cargo Warehouses accept broad sets of raw materials, processed goods, and mail.
- Tank Farms specialize in oil, petrochemicals, and chemicals.
- Bulk Storage Yards specialize primarily in bulk raw materials such as ore, coal, and stone, plus processed concrete.

Every storage module contributes to total port capacity, but resource eligibility still matters. A port with ample aggregate capacity can remain ineffective for a particular supply chain if the capacity is in the wrong storage family.

This suggests a better diagnostic than simply asking whether the port is full: inspect resource-specific stock, free capacity in the eligible storage type, cargo routes, and downstream demand together.

### Port gates are an efficiency boundary, not ordinary scenery

Trucks can path to storage using any connected road with the lowest pathfinding cost. However, the developer diary states that a road connection bypassing the main or auxiliary port gates reduces port Efficiency by 50%. Auxiliary Gates exist both to preserve the controlled boundary and to distribute entry and exit traffic.

This creates a non-obvious failure mode: an extra ordinary road may improve visible connectivity while halving the facility's Efficiency. A traffic diagnosis must distinguish gate-controlled access from ungated shortcuts instead of treating every road connection as beneficial.

The tutorial's use of direct highway connections and auxiliary gates is therefore mechanically significant, even though it does not explain the penalty. Layout guidance should favor multiple legitimate gates and deliberate one-way circulation rather than uncontrolled external connections.

### Reach Stackers are visible internal logistics, but not a hard cargo prerequisite

Reach Stackers move containers between quay-side cranes, storage, and the Intermodal Train Terminal. They are wider than normal vehicles and can drive only on Port Roads. The Large Port's Reach Stacker Garage increases loading and unloading speed.

The developer diary includes an important exception: if normal roads are used or a Reach Stacker cannot reach a facility, cargo is still transferred. The animated vehicle is therefore evidence of the preferred internal transfer path, not necessarily a complete representation of every successful inventory movement.

For toolkit work, absence of a visible Reach Stacker trip should not automatically be labeled a cargo deadlock. Diagnostics need separate signals for inventory transfer, vehicle dispatch, path availability, loading state, and overall port Efficiency.

### The Intermodal Train Terminal changes the truck boundary

The Intermodal Train Terminal gives a port two cargo tracks and supports Cargo Train Routes to the city or an outside connection. Reach Stackers can transfer cargo between ships, storage, and rail, reducing the need for external road vehicles to enter the harbor for every movement.

The developer diary explicitly supports a dry-port configuration: a main gate, appropriate storage, and the Intermodal Train Terminal can form a flexible inland cargo terminal connected by rail to a seaport, the city, or an outside connection. This is broader than the tutorial's framing of rail mainly as a way to bypass truck traffic at a waterfront port.

Rail does not eliminate all road activity. Companies still deliver to and collect from the logistics system where routes and economics select that path. The module changes available transfer paths and potential bottlenecks; it does not guarantee a truck-free port.

### Passenger and cargo port roles can coexist or be separated

The Passenger Terminal allows citizens and tourists to enter or leave through passenger ships. It can be combined with waterfront parks, commercial buildings, ferries, and bus service to form a tourism-focused harbor.

Because port modules are composable, cargo, passenger, and rail functions can share a port or be separated into specialized facilities. The main gate and 1 km radius define membership, while storage mix, terminals, routes, and land access define the operational role.

This flexibility is useful for troubleshooting. A port should be evaluated according to its intended role rather than against an assumed universal layout.

### Later patches materially qualify launch-version observations

Patch `1.4.2f1` fixed a crash that could occur when running a save with the Ferry Terminal. Patch `1.5.7f1` fixed port mail-transfer pathfinding and a Bridges & Ports bug where commercial and industrial buildings did not use DLC ports for importing goods even when the goods were available there. Patch `1.5.9f1` fixed specialized-industry delivery trucks failing to leave farms and similar extractors to export and sell accumulated stock.

The `1.5.7f1` import fix is especially important. A launch-era city could have a correctly built, stocked, and connected port yet still see companies import through other outside routes because of a game defect. Advice based only on the tutorial could incorrectly blame road design, storage selection, or player error.

Current answers must prefer newer patch evidence over this November 2025 tutorial whenever behavior conflicts. The tutorial remains useful for system topology and build workflow, not for asserting that every launch interaction still behaves identically.

## Existing corpus overlap

The wiki corpus already contains the Bridges and Ports overview, the `1.3.6f1` asset list, the Ports & Beyond diary listing, and later patch histories. It is stronger for exhaustive asset names, release metadata, and dated fixes.

The report adds a mechanics-centered synthesis that is difficult to retrieve from the overview alone: ferry depot capacity as a no-service cause; separate tanker and pipeline topologies for offshore oil; storage eligibility as distinct from total capacity; gate bypasses as a 50% Efficiency penalty; Reach Stacker animation as non-authoritative evidence of transfer; and the dry-port pattern enabled by the Intermodal Train Terminal.

The transcript itself contributes little that contradicts or extends the developer diary. Its main value is the concrete order of operations and a visible troubleshooting sequence. The developer diary supplies most of the unique constraints.

## Implications for Cities2 modding

A port-aware mod should model the port as a group of related entities rather than a single building. At minimum, investigation should look for the main gate, ownership or upgrade relationships, the 1 km placement rule, storage resource filters, routes and stops, gate and road networks, internal transfer vehicles, extensions, and aggregate Efficiency.

Visible vehicle behavior is not a sufficient proxy for resource movement. Since cargo can transfer when Reach Stackers cannot physically access a module, instrumentation should compare inventory changes and transfer events with spawned-vehicle paths instead of assuming a one-to-one correspondence.

Mods that diagnose or alter port traffic should distinguish external trucks, ships, trains, ferries, tankers, fishing vessels, and internal Reach Stackers. They serve different systems and may use different networks. A generic vehicle count around the harbor will blur operational bottlenecks with decorative or internal traffic.

The public sources do not identify ECS component names, systems, job dependencies, update phases, or prefab field names. Terms such as Port, Efficiency, Gate, Storage, Route, and Reach Stacker are gameplay concepts, not confirmed code identifiers. Installed-assembly and prefab inspection is required before implementing hooks.

Version-aware testing is essential. Test cases should record the game version, DLC availability, gate size, unlocked upgrades, storage types, sea and rail routes, gated versus bypass access, and whether the city predates relevant fixes. A regression fixture for imports should use a version at or after `1.5.7f1`.

## Implications for Cities2-MCP

This report should be retrieved for questions about building modular ports, ferries without vehicles, ferry terminals and bus transfers, offshore oil platform connections, fishing routes, port storage selection, auxiliary gates, Reach Stackers, intermodal terminals, dry ports, and why a stocked port is not serving companies.

Troubleshooting should follow the system boundary involved:

- For ferries, verify completed lines, Boatway reachability, depot access, and spare fleet capacity.
- For deep-water oil, verify the resource location, compatible platform depth, pier berths, Boatways, and tanker route; for near-shore oil, verify the pipeline instead.
- For fishing, distinguish open-water vessel routes from inland area production and verify eligible storage.
- For cargo ports, verify the main gate, 1 km module membership, sea-route unlock progression, resource-compatible storage, quay access, gated roads, and the selected ship, rail, or truck transfer path.
- For current import failures, check the installed version and retrieve the `1.5.7f1` fix before diagnosing the layout.

Answers should not promise that adding an Intermodal Train Terminal removes all trucks, that a missing Reach Stacker proves cargo is stuck, or that every road connection improves the port. Those claims are contradicted or qualified by the official diary.

## Uncertainties and transcript corrections

The supplied transcript is auto-generated. It renders quay as “key wall,” Reach Stacker as “reacher stacker,” Boatway or waterway terminology inconsistently, and BakaNa as “BakaNa” without independent pronunciation context. Game terms were normalized against the developer diary and patch index.

The statement that a longer oil-hub pier provides more landing berths is clearly presented in the tutorial, but the source does not quantify the length-to-berth relationship or throughput effect.

The exact tutorial demonstration shows a ferry-depot upgrade adding ten vehicles, but capacity values can be balance data rather than enduring mechanics. Current numeric questions should use installed prefab data or current encyclopedia content.

The report infers diagnostic implications from published rules, especially around storage mismatch, invisible fallback transfers, and gate topology. Those implications are reasoned interpretations rather than direct developer claims about debugging APIs.

## Sources

- Cities: Skylines and BakaNa, original tutorial, published 2025-11-05: https://www.youtube.com/watch?v=gdEuDLWxLak
- Colossal Order, Bridges & Ports Dev Diary #2 - Ports & Beyond, published 2025-10-21: https://www.paradoxinteractive.com/games/cities-skylines-ii/news/bridges-and-ports-dev-diary-ports
- Paradox Interactive, Bridges & Ports Now Available!, published 2025-10-29: https://www.paradoxinteractive.com/games/cities-skylines-ii/news/bridges-and-ports-now-available
- Paradox Interactive and Iceflake Studios, Spring Cleaning - Patch `1.5.7f1`, published 2026-04-29: https://www.paradoxinteractive.com/games/cities-skylines-ii/news/patch-notes-spring-cleaning
- Paradox Interactive and Iceflake Studios, Patch `1.5.9f1` - Morning Dew, published 2026-05-27: https://www.paradoxinteractive.com/games/cities-skylines-ii/news/patch-notes-morning-dew
- Cities: Skylines II Wiki, Bridges and Ports: https://cs2.paradoxwikis.com/Bridges_and_Ports
- Cities: Skylines II Wiki, Patch `1.3.X`: https://cs2.paradoxwikis.com/Patch_1.3.X
- Cities: Skylines II Wiki, Patch `1.4.X`: https://cs2.paradoxwikis.com/Patch_1.4.X
- Cities: Skylines II Wiki, Patch `1.5.X`: https://cs2.paradoxwikis.com/Patch_1.5.X
