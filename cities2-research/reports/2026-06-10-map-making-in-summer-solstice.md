---
schema_version: 1
title: Cities: Skylines II - Map Making in Summer Solstice
slug: map-making-in-summer-solstice
source_type: developer_livestream
source_url: https://www.youtube.com/watch?v=LG-_wMosklA
published_at: 2026-06-10
publication_date_basis: source_metadata
creators: Sini; Zoë
organizations: Iceflake Studios; Paradox Interactive
report_created_at: 2026-07-19
report_updated_at: 2026-07-19
event: Cities: Skylines II developer livestream
game_version: 1.6.0f1 prerelease
---

# Cities: Skylines II - Map Making in Summer Solstice

## Executive summary

This June 2026 livestream previews the terrain-rendering and terrain-painting work that shipped twelve days later in patch `1.6.0f1`, Summer Solstice. Most final technical facts are now documented more precisely in City Corner #8, the released patch notes, and the official map-creation guide. The stream remains useful because it demonstrates how the tools behave and records several practical details that are easy to miss in the written summaries.

The most useful livestream-only material concerns the four paintable ground materials and custom-map workflows. The hosts demonstrate per-material erasing, a fixed paint-layer priority from slot one at the bottom to slot four at the top, brush-strength blending, brush rotation, and painted material surviving later terraforming while automatic cliff texturing appears on steep faces. They also clarify that existing custom maps do not automatically gain hand-painted detail: creators must update their maps to use the new painting tools.

The stream's assurances were pre-release and qualified. Sini said the terrain overhaul was not expected to reduce performance and that the patch should not break mods, but the final patch notes warned that some custom maps could be affected. Current compatibility and authoring guidance should therefore come from the released patch and versioned official map-creation documentation, not from the broadcast alone.

## Source context and temporal scope

The official Cities: Skylines II livestream was published on 2026-06-10. Iceflake Studios community manager Sini and Paradox community ambassador Zoë used a prerelease Summer Solstice build to demonstrate a heightmap-based work-in-progress map, Mountain Village, and Archipelago Haven. The usable program runs for roughly 65 minutes after an introductory holding period.

At broadcast time, the update had no announced release date. City Corner #8, "Transforming the Terrain," followed on 2026-06-11 and supplied the more technical written explanation. Patch `1.6.0f1` shipped on 2026-06-22. This report distinguishes the stream's observations and provisional assurances from the behavior documented after release.

The supplied transcript is an auto-generated DownSub transcript. The original local file was restored and archived verbatim under the ignored research sources. A saved copy of Colossal Order's 2024 Map Editor development diary, the official City Corner #8 announcement, and the final Summer Solstice patch announcement were also archived as supporting first-party sources.

## Findings

### Terrain rendering overhaul

The stream visually compares the previous and Summer Solstice terrain rendering. The new defaults improve the transition between land and water, cliff definition, material blending, and the way terrain responds to light. Sini and Zoë explain that the old terrain normals were biased too far upward, making slopes look flatter than their geometry; correcting the normals exposes ridges, crevices, shadows, and surface depth more clearly.

The later City Corner provides the precise implementation description omitted from the stream: triplanar mapping was added for cliffs, terrain textures received individual smoothness maps, terrain-normal calculation was improved, and additional texture LOD levels were added. The final patch notes further specify three tiling levels and three-axis rock projection. Those written descriptions should be preferred over the hosts' deliberately informal technical language.

The stream sometimes describes the new grass, rock, and shoreline appearance as applying to all maps. The final patch notes are more specific: all Temperate-biome maps received reworked grass, dirt, and rock materials. Five maps also received manual paint work: Archipelago Haven, Great Highlands, Twin Mountain, River Delta, and Mountain Village. The team said it intended to continue hand-painting other maps, but the stream did not schedule that work.

### Four terrain-painting materials

Summer Solstice adds four paintable ground materials: dirt, rock, sand, and grass. The same painting tools are available in the Map Editor and in ordinary city gameplay, allowing players to create features such as beaches without building or republishing an entire map. Brush size and strength control coverage and blending, while `Shift + Mouse Wheel` rotates the selected brush.

The demonstration distinguishes two erasing operations. Right-clicking with a material selected removes only that material, while the general eraser removes all painted materials from the affected area. The four custom material slots have a fixed drawing priority: slot one is the bottom layer, slots two and three are progressively higher, and slot four is topmost. Lower brush strength creates subtler transitions; the hosts say early internal strength tuning became ineffective too quickly below approximately half strength and was adjusted before release.

Painted material remains attached when the ground is subsequently terraformed. On steepened faces, the renderer can expose automatic rock or cliff texturing beneath or alongside the painted surface. This is a demonstrated visual behavior rather than a complete specification of how splat weights or slope thresholds are calculated.

### Custom terrain materials and map distribution

Map creators can replace the four extra paintable materials through a map's terrain-render settings. The stream demonstrates the concept with intentionally crude color textures and states that a player loading the finished map would use those map-specific materials when painting in normal gameplay.

The hosts refer informally to a diffuse texture and a normal texture. The current official version `1.6.0f1` map-creation guide uses the authoritative names `Albedo (BaseColor)` and `Normal`, and documents important alpha-channel data for smoothness and height blending. Toolkit guidance should use the current written terminology and validation rules rather than reproduce the stream's shorthand.

The current official guide also adds a packaging distinction absent from the stream. Locally stored terrain-render settings selected by a map are packaged into the map's `.cok` file, while settings subscribed from Paradox Mods remain an external required dependency. That distinction matters when diagnosing a map that looks different for its author and subscribers.

### Existing custom maps require creator work

The stream explicitly says that the four paintable detail layers will not automatically appear on existing custom maps. A map creator can reopen and update a published map to add beaches, dirt around roads, darker forest floors, or other painted detail. The underlying renderer and default materials may still change with the game update, but authored paint placement is not synthesized for an older map.

The final patch announcement warns that Summer Solstice can affect some custom maps even though loading old maps and savegames is supported. It also lists fixes for saving maps with custom climate, water, or terrain settings and for maps using custom terrain textures. That released warning supersedes the stream's tentative statement that the patch should not break mods.

### Editor usability changes

The stream demonstrates a gizmo cleanup that makes transform gizmos appear only where relevant instead of across every repeated object. Zoë describes the old state as both visual clutter and a source of editor lag. The final patch notes phrase the shipped behavior more precisely: gizmos appear only for transparent objects and the selected object, and widgets appear only on selected assets.

A global contour-line or topography toggle is shown in both the editor and normal gameplay. It can remain visible while inspecting the map, planning, zoning, or placing objects rather than appearing only in a terrain operation. The final patch notes add that its new keybind is unbound by default.

### Rendering and performance claims

Sini says Iceflake's technical director confirmed that the new textures would not reduce performance. City Corner #8 goes further and says the team avoided a negative rendering impact and improved rendering performance. The released patch makes a narrower measurable claim: lower Texture Quality settings reduce terrain VRAM use and improve GPU performance.

The stream contains no benchmark, hardware description, frame-time comparison, or VRAM measurement. It supports the conclusion that the feature was designed to avoid a regression, not a universal promise that every machine, camera angle, custom texture set, or map will run faster.

### Pathfinding preview

Although the stream focuses on terrain, Sini briefly previews more sensible trip distances. Citizens should be less likely to cross the map for shopping, leisure, work, or school when a reasonable destination is available. The watermelon-store example is an informal illustration of the shopping bug later described in City Corner #8.

The final patch and City Corner contain the authoritative details: limits became trip-type-specific; move-outs without a route teleport off-map; workers can drop their job; leisure seekers wait at home before retrying; and a known issue remained for some excessively long student walks. The livestream adds little unique mechanical information beyond showing how the feature was communicated before the written explanation.

## Existing corpus overlap

The bundled wiki already indexes this livestream and City Corner #8. Its `Patch 1.6.X` page contains the released Summer Solstice notes, while the Paradox-verified `Map Creation` and `Map Creation: Terrain` pages provide substantially deeper current guidance for heightmaps, brush behavior, terrain materials, texture channels, render settings, packaging, and sharing.

The older 2024 Map Editor development diary covers the original editor model, 4096-by-4096 16-bit heightmaps, the playable and surrounding world maps, workspace organization, climate selection, outside connections, objects, and the checklist. It is useful historical background but predates the Summer Solstice terrain system and should not override the version `1.6.0f1` guide.

The research report adds the demonstrated layer-priority and erase behavior, the distinction between default rendering changes and author-painted updates, the hosts' qualified performance and mod-compatibility statements, and the exact temporal relationship between preview, City Corner, and released patch.

## Implications for Cities2 modding

Map tooling should treat terrain materials as ordered layers rather than interchangeable paint labels. Diagnostics and authoring helpers can usefully expose the slot-one-to-slot-four priority, identify which material a selective erase affects, and warn when a desired visual result is hidden by a higher-priority layer.

Texture validation should follow the current official guide: distinguish BaseColor from Normal inputs, inspect alpha-channel smoothness and height data, encourage seamless square power-of-two textures, and account for legacy terrain-texture behavior. The stream is evidence of intended workflow, not a sufficient file-format specification.

Packaging checks should distinguish local terrain-render settings embedded in a map from subscribed settings referenced as dependencies. A map that renders correctly only in the creator's playset may be missing a declared dependency or may have used a subscribed prefab when the creator expected it to be embedded.

Compatibility claims must be versioned. The pre-release stream expected mods to remain compatible, while the final patch explicitly allowed for effects on custom maps. Testing a map under `1.6.0f1` or later, with a controlled editor playset, is more reliable than relying on the stream's assurance.

## Implications for Cities2-MCP

For current map-making instructions, Cities2-MCP should route users first to the Paradox-verified `Map Creation` pages and use this report for livestream-specific context. The report is especially relevant to questions about paint-layer order, selective erasing, whether older maps gain painted details automatically, what the hosts meant by custom terrain textures, and what they actually promised about mod compatibility or performance.

The toolkit should avoid flattening three distinct facts into one claim: the renderer changed globally, five official maps received authored paint, and old custom maps require their creators to add new painted detail. Similarly, it should distinguish map-embedded terrain settings from subscribed settings that remain external dependencies.

When answering performance questions, the narrow released claim about lower texture settings and VRAM should outrank the stream's general reassurance. When answering technical texture questions, current BaseColor, Normal, alpha-channel, and packaging documentation should outrank the hosts' improvised terminology.

## Uncertainties and transcript corrections

The transcript repeatedly mistranscribes Iceflake Studios, Sini, Zoë, Tampere, gizmo, topography, Archipelago Haven, Mountain Village, pathfinding, and terrain terminology. Those names and terms are normalized in this report.

The broadcast does not expose numeric thresholds for slope-based cliff rendering, material blend weights, brush falloff, texture resolution, texture-channel layout, or performance. Any such details must come from the official map-creation guide, released patch documentation, or runtime/code inspection.

The stream was recorded against a prerelease build and included statements such as "should not break mods" and "no exact date." The patch's 2026-06-22 release notes and current versioned documentation supersede those provisional claims.

## Sources

- Iceflake Studios and Paradox Interactive, original livestream, published 2026-06-10: https://www.youtube.com/watch?v=LG-_wMosklA
- Iceflake Studios, City Corner #8 - Transforming the Terrain, published 2026-06-11: https://steamcommunity.com/gid/103582791473275351/announcements/detail/699893179027030812
- Iceflake Studios, Patch 1.6.0f1 - Summer Solstice, published 2026-06-22: https://steamcommunity.com/ogg/949230/announcements/detail/699893179027031260
- Colossal Order, Modding Development Diary #2 - Map Editor, published 2024-03-20: https://www.paradoxinteractive.com/games/cities-skylines-ii/modding/dev-diary-2-map-editor
- Cities: Skylines II Wiki, Patch 1.6.X: https://cs2.paradoxwikis.com/Patch_1.6.X
- Cities: Skylines II Wiki, Map Creation: https://cs2.paradoxwikis.com/Map_Creation
- Cities: Skylines II Wiki, Map Creation: Terrain: https://cs2.paradoxwikis.com/Map_Creation:_Terrain
- Cities: Skylines II Wiki, Editor: Interface: https://cs2.paradoxwikis.com/Editor:_Interface
- Cities: Skylines II Wiki, Developer diaries: https://cs2.paradoxwikis.com/Developer_diaries
