---
schema_version: 1
title: Iceflake Studios May 2026 Cities: Skylines II AMA
slug: iceflake-studios-reddit-ama
source_type: developer_ama
source_url: https://www.reddit.com/r/CitiesSkylines/comments/1t59nyo/were_iceflake_studios_the_new_development_team/
published_at: 2026-05-06
publication_date_basis: source_metadata
creators: Sini; Timo; Jesse; Jarkko; Kimmo
organizations: Iceflake Studios
report_created_at: 2026-07-19
report_updated_at: 2026-07-19
event: Iceflake Studios Reddit AMA held 2026-05-08
---

# Iceflake Studios May 2026 Cities: Skylines II AMA

## Executive summary

Iceflake Studios' first Cities: Skylines II Reddit AMA is a high-value primary source for the team's May 2026 understanding of the simulation, performance constraints, traffic, engine architecture, and relationship with mods. Lead programmer Timo described a central design problem as insufficient simulation transparency and player agency: the game calculates many individual details, but players cannot always see why an outcome occurred or influence it effectively. The team intended to improve explanation and visualization before or alongside adding new controls.

The most useful technical disclosures concern the resource economy, abstract outside connections, pathfinding as the principal CPU bottleneck, tension between agent-level and statistical simulation, the continued importance of DOTS and ECS, and the difficulty of adopting newer rendering features while the game remains on Unity 2022.3 with a heavily customized HDRP. These statements provide architectural and diagnostic context, not stable public modding APIs.

## Source context and temporal scope

The Reddit post was published on 2026-05-06 to solicit questions for a formal AMA held on 2026-05-08. Answers came from community manager Sini, lead programmer Timo, game designer Jesse, producer Jarkko, and QA representative Kimmo. Iceflake staff continued adding some answers after the formal session, including replies dated as late as 2026-05-14 in the captured page.

The thread mixes several levels of confidence. Statements that work was active or planned carry more weight than items merely added to a suggestion board. Speculative examples, personal wishes, and phrases such as "never say never" are not commitments. All roadmap and platform statements are historically situated in May 2026 and require comparison with later patches and developer communication.

## Findings

### Simulation visibility and player agency

Timo said the game simulates substantially more than Cities: Skylines, but can still fail to feel like a simulator because players lack understandability and agency. His proposed direction was first to communicate what is happening and why through UI information, world feedback, overlays, and other visualization, then give players more meaningful ways to control the systems. In practice, information and control improvements could arrive in parallel rather than as a strict sequence.

For the resource economy, companies order inputs they need and try to sell their outputs, while warehouses and cargo facilities attempt to maintain a middle level of stock across resources. Players influence the result indirectly through taxes, subsidies, and transportation costs; ship and rail connections can make trade cheaper. Iceflake considered this insufficient control. Timo offered separate warehouse zoning, district-level permissions for stored or produced resources, citywide import restrictions, and direct control over some specialized or signature production as possible directions, while explicitly saying these were not promises.

Outside-connection city names were described as flavor over a shared abstract external city rather than separate simulated neighbors. Timo believed some modeling still represented the wider world, such as rail and ship trade serving a larger area, but noted that he had not recently verified every inherited detail. His recommended first step was to expose the behavior already present before deciding whether more control or simulation was necessary.

### Agent simulation and performance

Pathfinding was repeatedly identified as the largest CPU-side performance problem. GPU rendering was described as having more straightforward headroom through better LODs, culling, and related rendering work, while large-city CPU gains could require behavioral changes. The linked City Corner #4 adds that water simulation is GPU-based and expensive on lower-end hardware, and that excessive or unnecessary path requests can make simulation problems worse.

Iceflake did not describe an intentional population cap. Instead, simulation speed degrades at a city size that varies with hardware and player tolerance. Timo rejected expectations of a quick jump from hundreds of thousands of individually simulated agents to a smoothly running million-agent city. Replacing journeys with statistically generated traffic would change the nature of the game, and he did not expect traffic to become a statistical abstraction.

Some background citizen attributes are updated infrequently and therefore cost little individually, although they increase code complexity. Examples given included free-time shortages influencing reckless driving, divorce and remarriage, school path distance affecting residential choice, and personal sleep preferences. These examples help explain why apparently small simulation systems can create indirect behavior and maintenance cost.

The AMA also exposed a mismatch between simulation layers. Some demand calculations use city-level modifiers rather than individual agent decisions. Timo used taxes as an example: companies may struggle financially because of high taxes while a separate global demand modifier still permits demand. This is an important explanation for cases where observed agent conditions and aggregate indicators appear inconsistent.

### Traffic and transport behavior

Traffic was a high-priority area under active incremental work. Iceflake specifically recognized late lane changes, excessive U-turns, and other reckless behavior. Some cases could be improved by pathfinding-weight adjustments, but the team stressed that there were many distinct failure situations and that traffic changes affect the wider simulation.

Emergency-vehicle behavior was described as a larger task that was not then under active development. For traffic signals, Timo expected relatively simple improvements to automatic logic first; precise per-intersection timing was presented as the kind of specialized control that mods can serve well. These statements describe May 2026 priorities, not the final scope of later traffic patches.

### Engine and rendering constraints

Timo said DOTS and ECS were necessary to achieve the game's current simulation scope. Their immaturity slowed early development, but he considered the architecture successful by 2026. This reinforces the architectural picture in Colossal Order's 2024 Unite presentation while showing that Iceflake expected to continue with the same fundamental data-oriented foundation.

The game was reported to remain on Unity 2022.3 with a heavily customized, correspondingly old HDRP. Modern FSR and newer DLSS integration were therefore not direct upgrades. Iceflake had investigated both rendering technology updates and a broader Unity upgrade, but customizations, backported features, and the need to undo or reconcile those backports made an engine upgrade a large project without guaranteed gains.

Console development was active but had no public date. The console effort required optimization across the game, with memory savings especially important; Timo gave small examples such as streaming compressed audio and reducing an intermediate UI-rendering buffer. macOS was not on the roadmap at the time of the AMA.

### Citizen models and animation

Iceflake continued to use Didimo's Popul8 and had no near-term plan to replace it. More situational animations were intended to make the city feel alive. Rebuilding citizen models had been discussed but was not a priority, and the stated motivation would be visual rather than performance-related. Pathfinding and other systems, not the citizen meshes themselves, were identified as the more important simulation bottlenecks, although LOD and culling work could still improve rendering.

### Mods and the base game

Iceflake said it monitors popular mods, draws inspiration from them, and tries to contact creators before implementing similar features. Building recoloring and the zoning toggle were named as examples influenced by mods. The team distinguished vanilla development from mod development: a base-game feature must be robust for a broad audience and preserve game integrity, while a mod can serve a niche audience or expose controls that can break a city when used without care.

The team therefore did not intend to copy Anarchy wholesale, but expected to bring selected mod-like quality-of-life features into free patches. Items described as active work included dirt or gravel paths, network fences, hedges, a forest brush, park-building improvements, and grass-visual improvements. This list records activity in May 2026 and must not be read as a permanent roadmap.

### Development and release approach

Iceflake planned work in smaller chunks so regressions would be easier to isolate and hotfix. The team wanted to avoid hotfixes but remained prepared to issue them. Its stated general order was to fix bugs and make current systems understandable, then judge where larger redesigns or additional controls were needed.

Specialized industry was described by Timo as relatively high on the medium-term improvement list, while Sini confirmed that the visual and functional awkwardness of farms and specialized-industry areas had been discussed without a schedule. Numerous other answers merely recorded suggestions or personal preferences; those should not be elevated to planned features.

## Existing corpus overlap

The wiki corpus's `Developer diaries` page indexes City Corner #4 and the later community posts, but only summarizes them. It does not preserve the AMA's direct explanations of logistics, outside connections, mixed statistical and agent simulation, engine-upgrade constraints, or vanilla-versus-mod design policy.

The existing Unite 2024 research report covers Colossal Order's ECS implementation in much greater architectural detail. This AMA confirms that Iceflake still regarded DOTS and ECS as foundational, while adding a newer maintainer's perspective on pathfinding, performance, inherited design complexity, and current development priorities.

## Implications for Cities2 modding

Mods that inspect or alter traffic, demand, trade, or citizen decisions should expect behavior to cross system boundaries. A visible inconsistency may arise from separate agent-level and aggregate calculations rather than a single defective component. Diagnostic tools should expose both the local entity state and the relevant citywide modifier before claiming a cause.

Traffic and pathfinding modifications have unusually high regression and performance risk. They should be tested on small and large cities, with attention to path-request frequency, simulation speed, invalid routes, lane selection, and downstream effects rather than visual traffic flow alone.

The reported Unity and HDRP versions are a warning against assuming that APIs or packages documented for newer Unity releases exist in the installed game. Current assemblies and runtime evidence remain authoritative for implementation. Likewise, internal ECS architecture described by developers does not make an internal type a supported mod API.

The team's mod-integration policy suggests a durable role for mods: experimental, niche, or expert controls may remain appropriate even when a safer subset later enters vanilla. A toolkit should help authors identify the feature gap they are filling and avoid promising that a popular mod will or will not be absorbed into the base game.

## Implications for Cities2-MCP

The toolkit should retrieve this report for questions about Iceflake's development philosophy, resource logistics, outside connections, traffic priorities, pathfinding performance, agent simulation, Unity-version constraints, citizen models, and the relationship between popular mods and vanilla features.

Answers must preserve status language. "Actively being worked on," "planned," "discussed," "on the suggestion board," and a staff member's personal preference represent different evidence levels. For current roadmap or platform questions, later patch notes and developer posts should outrank this May 2026 snapshot.

The report can also help interpret city evidence. For example, contradictory demand and company-finance signals may reflect separate aggregate and agent calculations, while cargo inventories may reflect facilities targeting broad stock levels rather than a player's desired specialization. These are investigation hypotheses, not substitutes for current save or runtime evidence.

## Uncertainties and transcript corrections

The AMA is conversational and distributed across more than one hundred Iceflake comments. Some answers were added or edited after the formal event, and Reddit can change presentation or collapse reply branches. The archived page is therefore a source snapshot rather than a guarantee that every later edit is represented.

Staff frequently distinguished personal wishes, suggestions, and actual work. This report omits unsupported community claims and does not treat a suggestion-board entry as a roadmap commitment.

The May 13 livestream `Designing a Five-Way Interchange` paraphrased many AMA answers. Its auto-generated transcript variously mistranscribes Iceflake, Sini, Timo, Reddit AMA, Linux, and technical road terminology. The written AMA is preferred whenever both sources cover the same answer.

## Sources

- Iceflake Studios, Reddit AMA announcement and full discussion, published 2026-05-06: https://www.reddit.com/r/CitiesSkylines/comments/1t59nyo/were_iceflake_studios_the_new_development_team/
- Timo on transportation, resources, and possible player controls: https://www.reddit.com/r/CitiesSkylines/comments/1t59nyo/comment/okncq4n/
- Timo on simulation understandability and agency: https://www.reddit.com/r/CitiesSkylines/comments/1t59nyo/comment/okn0031/
- Timo on traffic behavior: https://www.reddit.com/r/CitiesSkylines/comments/1t59nyo/comment/oknfo6p/
- Timo on mod inspiration and vanilla constraints: https://www.reddit.com/r/CitiesSkylines/comments/1t59nyo/comment/oknk2v9/
- Iceflake Studios and Paradox Interactive, Designing a Five-Way Interchange, streamed 2026-05-13: https://www.youtube.com/watch?v=liuqwdHj720
- Iceflake Studios, City Corner #4 - A Peek into Performance, published 2026-04-09: https://steamcommunity.com/games/949230/announcements/detail/532128384944178048
- Colossal Order, Behind the Scenes #5: Citizen Characters, published 2023-10-21: https://colossalorder.fi/news/behind-the-scenes-5-citizen-characters/
- Cities: Skylines II Wiki, Developer diaries: https://cs2.paradoxwikis.com/Developer_diaries
