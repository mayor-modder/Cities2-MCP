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
event: Unite 2024
unity_version: 2022.3
---

# Tapping the Entity Component System for Cities: Skylines II

## Executive summary

Damien Morello's Unite 2024 session explains why Cities: Skylines II combines Unity ECS, the Job System, Burst, managed systems, custom prefab authoring, and custom runtime asset infrastructure. Its strongest value for modding is not a list of public APIs but the engineering rationale behind simulation phases, prefab conversion, job dependencies, debugging, and deciding which data should remain outside ECS.

## Source context and temporal scope

The session was published on 2024-10-09 and describes Colossal Order's architecture at that time. It reports Unity 2022.3 and a codebase shaped by adopting Entities while the package was still experimental. Internal systems and package behavior described here must not be assumed to remain current or publicly accessible to mods without newer documentation or installed-assembly evidence.

## Findings

CS2 uses a small managed shell around a manually updated ECS world. Input, simulation, UI transfer, allocator cleanup, main-thread dispatch, and platform callbacks occupy deliberate positions in the frame.

Designer-facing prefabs are ScriptableObject-style objects rather than Unity GameObject prefabs. Registration converts authoring data into a compact ECS representation that may use several components. A prefab accepts one component of each type, and reverse relationships let later content declare itself as a variation or replacement without patching a central list.

The runtime asset database was designed partly to support mods. Assets from the installation, user storage, cloud storage, and subscriptions are indexed by GUID, remain lazy until used, and load minimal metadata before heavier content. Geometry and texture streaming request only required data, with budgets and graceful fallback behavior.

The team kept managed systems but moved heavy work into Burst-compiled jobs, predominantly `IJobChunk`. Explicit update phases act as synchronization points. Entity command buffers are paired with barriers because playback in the wrong phase can appear harmless before causing intermittent invalid state.

The talk cautions that not every large data structure belongs in ECS. Pathfinding and utility-flow work may use persistent native collections outside entity storage while still participating in job dependencies and Burst compilation.

UI-facing systems query and cache simulation data, then send changed values through a binding layer to the JavaScript and React UI. Debug visualization systems follow the same separation: they query data without changing the simulation and are enabled only when needed.

Profiling is presented as dependency analysis as well as timing analysis. Incorrect dependencies can stall the main thread or leave worker threads idle. Long-running pathfinding jobs also led the team to disable main-thread job stealing rather than allow a several-hundred-millisecond job to create visible stutter.

## Existing corpus overlap

The wiki corpus already explains entities, components, archetypes, queries, systems, update phases, Burst-related memory handling, and basic entity-command-buffer use. The talk overlaps those definitions but adds production rationale, scale, failure modes, and architecture boundaries that are not returned clearly by the existing pages.

The wiki's `Developer diaries` page separately indexes developer communications, including the later City Corner series, but it does not contain this conference talk or a comparable architectural synthesis.

## Implications for Cities2 modding

Mods should choose update phases from actual data dependencies instead of treating modification phases as interchangeable. Structural changes should use a barrier appropriate to the chosen phase, and job handles must describe real dependencies without unnecessary serialization.

Performance-sensitive mods should profile scheduling, allocations, and worker utilization. Burst and jobs can help only when the work is large enough to justify scheduling overhead and uses unmanaged data safely.

Mod architecture should not force every custom structure into ECS. Stable graphs, flow networks, or other specialized structures may be better stored in native collections owned by a system, with ECS used at the integration boundary.

Internal CS2 facilities mentioned in the talk are architectural evidence, not automatic API recommendations. Current wiki pages, installed assemblies, logs, and profiler evidence remain necessary for implementation decisions.

## Implications for Cities2-MCP

The toolkit should retrieve this report for questions about ECS architecture, update barriers, job scheduling, prefab conversion, runtime asset loading, UI data separation, and debugging strategy. Results must identify the `cities2-research` dataset and preserve the 2024-10-09 publication date so agents can state that the material is historically situated.

The report should complement the wiki rather than outrank current documentation automatically. When research and current sources differ, agents should identify both sources and validate current APIs independently.

## Uncertainties and transcript corrections

The supplied transcript is auto-generated and repeatedly mistranscribes technical names. Normalized terms include `EntityCommandBuffer`, `IJobChunk`, `AsyncReadManager`, `BatchRendererGroup`, Burst, and pathfinding.

The transcript's exact Entities package version is ambiguous and is therefore omitted from metadata. Screenshot-only debugging examples and the unfinished question period are not recoverable from the text transcript alone.

## Sources

- Unity, Tapping the Entity Component System for Cities: Skylines II, Unite 2024: https://www.youtube.com/watch?v=nEkIyWhvq3o
- Cities: Skylines II Wiki, ECS - Entity Component System: https://cs2.paradoxwikis.com/ECS_-_Entity_Component_System
- Cities: Skylines II Wiki, Systems: https://cs2.paradoxwikis.com/Systems
- Cities: Skylines II Wiki, Developer diaries: https://cs2.paradoxwikis.com/Developer_diaries
