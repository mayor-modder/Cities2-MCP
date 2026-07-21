---
schema_version: 1
title: Behind the Scenes #2 - Editor
slug: behind-the-scenes-2-editor
source_type: developer_diary
source_url: https://forum.paradoxplaza.com/forum/developer-diary/behind-the-scenes-2-editor.1602378/
published_at: 2023-10-18
publication_date_basis: source_metadata
creators: Colossal Order development team
organizations: Colossal Order; Paradox Interactive
report_created_at: 2026-07-20
report_updated_at: 2026-07-20
event: Cities: Skylines II Behind the Scenes developer diary
game_version: pre-release
---

# Behind the Scenes #2 - Editor

## Executive summary

This pre-release developer diary presents Colossal Order's original design and rollout plan for the Cities: Skylines II Editor. Its enduring architectural idea is a single contextual editor shared across maps and assets rather than separate task-specific editors. Creators would be able to load a map, place an asset among roads and buildings, shape terrain around placed content, and use broadly the same internal tools as the developer.

Its release roadmap is historically important but materially inaccurate as a description of what shipped. The diary said the first post-launch editor update would combine map creation, building asset import, code mods, Paradox Mods sharing, and savegame sharing. The March 25, 2024 modding release delivered the Map Editor, code mods, and Paradox Mods support for maps, saves, and code mods, but custom asset import was deferred. Public asset creation and sharing arrived with patch `1.5.2f1` on December 4, 2025, more than two years after this post.

The diary also records longer-term plans for vehicles, trees, bushes, and citizen models. Aging trees are represented in current verified asset documentation, but this 2023 roadmap does not prove the present support status of every promised asset category. Current editor and asset-pipeline documentation must take precedence.

For the toolkit, the main value is historical orientation: the editor was conceived as a unified, extensible creation environment; custom assets were expected to combine imported meshes and textures with prefab configuration and simulation statistics; and Cities: Skylines I mods were explicitly expected to be recreated rather than reused unchanged because the sequel uses different technology and a deeper simulation.

## Source context and temporal scope

The diary was published on 2023-10-18, six days before the PC release of Cities: Skylines II. The public game did not yet include an editor. Colossal Order described the editor as being in beta with a group of experienced modders and asset creators and said it would be added after release once beta testing was sufficiently complete.

This is a roadmap and design-intent source, not a manual for a released tool. Terms such as initial release, next step, goal, and want describe the plan as of October 2023. The diary itself states that the plans were intentionally open-ended and makes no guarantees about additional requested features.

The actual public rollout must be read separately. Patch `1.1.0f1` on 2024-03-25 added code modding, the modding toolchain, map creation, and Paradox Mods integration for code mods, savegames, and custom maps. The contemporaneous developer-diary index records that asset importing needed more time. Patch `1.5.2f1` on 2025-12-04 added public asset creation and sharing.

## Findings

### One editor was intended to cover different creation modes

Cities: Skylines used separate editors and category-specific subsets of tools. Colossal Order's sequel design replaced that model with one Editor intended to support maps, buildings, and later content types. The resulting interface could expose many options at once and therefore risk feeling daunting, but the team considered the shared environment worth that cost.

The current editor documentation retains this broad model. Its interface includes an Asset Importer, Asset Browser, Workspace, Inspector, simulation overrides, infoviews, world camera controls, and other tools rather than presenting the editor as a single-purpose building or map wizard.

This does not mean every content type shares an identical pipeline. Maps, buildings, props, decals, surfaces, trees, and code mods have different inputs, validation rules, and packaging requirements. “One Editor” describes the encompassing application and interaction model, not one interchangeable data format.

### Contextual editing was a core design goal

The diary emphasizes that an asset need not be created against an empty flat background. A creator could load a map, place a building into the environment, add neighboring buildings and roads, and judge how the asset fits its likely surroundings. A map creator could place buildings while shaping hills and valleys to check scale.

This is useful design rationale for preview and validation tooling. Asset dimensions, entrances, built-in networks, terrain fit, props, and visual scale are better evaluated in a representative scene than in isolation. Toolkit workflows should preserve an in-editor placement and contextual inspection step rather than treating successful mesh import as sufficient validation.

### The first-wave roadmap combined capabilities that shipped separately

The planned first release included four major areas:

- Map creation, including terrain, water sources, resources, forests, outside connections, climate, temperature, and weather.
- Initial custom-building support through imported `.fbx` meshes and matching textures, color variations, decoration, and configurable statistics.
- Code modding, with prominent Cities: Skylines modders receiving early game access.
- Paradox Mods sharing for maps, buildings, code mods, savegames, and downloadable cities.

The March 2024 release delivered map creation, code mods, and Paradox Mods integration, but not the promised custom-building import. The actual `1.1.0f1` sharing list contains code mods, savegames, and custom maps. Asset support did not arrive until `1.5.2f1` in December 2025.

This divergence is the report's most important temporal finding. The diary is good evidence of intended scope and sequencing at launch, but poor evidence of availability on any later date unless checked against the corresponding patch.

### Asset creation was conceived as import plus prefab configuration

The early asset workflow combined external content preparation with in-editor setup. Creators would import an `.fbx` model and matching textures, define color variations, decorate the result, and adjust its statistics so the asset behaved appropriately in the simulation. Existing assets could also be edited to produce new color or decoration variants.

Current verified asset documentation is much more specific. It defines project-root and asset-folder conventions, mesh and texture naming, the Asset Importer, prefab components, sub-objects, sub-networks, lanes, effects, packaging, and sharing. Those current requirements supersede the diary's high-level description.

The diary's phrase “tweak its stats” should not be interpreted as permission to change arbitrary simulation data safely. Modern asset work must follow the supported prefab components and editor constraints for the target game version.

### The team expected sequel mods to be rebuilt

Colossal Order explicitly warned that Cities: Skylines I mods could not be used as-is. Cities: Skylines II uses new technology and a deeper simulation, so mods needed to be created from scratch even when their ideas or user-facing purpose carried over.

This is a durable migration principle. A toolkit may help port concepts, settings, localization, algorithms, or visual references, but it should not imply binary compatibility, direct project conversion, or stable class equivalence between the two games.

### The editor was developed with community and internal use in mind

The editor was being tested with a closed group of experienced modders and asset creators, and Colossal Order said development occurred in close cooperation with the modding community. The same tool family was also intended for internal development.

That shared-tool premise helps explain the editor's low-level prefab and inspection capabilities. It does not establish that every internal option is supported for public content or that internal and public permissions are identical. Current verified documentation and editor validation remain the authority for what creators may package and share.

### Later asset categories were explicitly more complex

The longer-term roadmap named vehicles, trees, bushes, and citizen models. Trees required multiple models for lifecycle stages from sapling to adult to dead. Citizens required models across life stages from children through seniors.

This is valuable pipeline rationale: a seemingly singular visual asset may actually be a coordinated set of state- or age-specific models. Current documentation includes an aging-tree pipeline, confirming that lifecycle complexity became part of the supported asset model. The diary does not provide enough technical detail to scaffold those assets by itself.

Vehicle and citizen support should not be inferred solely from their appearance in the roadmap. Their current availability, required components, animation systems, and packaging rules need independent verification.

### Cross-platform language was intentionally qualified

The diary described Paradox Mods as available on all platforms “within the limits of each platform” and deferred console specifics. That qualification is material. It does not promise that code mods, every asset type, or the full Editor would operate identically on consoles.

Toolkit documentation should make platform claims from current Paradox Mods and console documentation, not from the broad 2023 aspiration.

### Feedback requests were not commitments

Colossal Order described the roadmap as intentionally open-ended and invited feedback about previous editors and desired content. It also said it could not guarantee requested additions. A user suggestion, beta discussion, or named future goal therefore cannot be treated as scheduled work without later confirmation.

## Existing corpus overlap

The wiki corpus already indexes this diary and contains current, Paradox-verified pages for the Editor interface, asset importing, prefab inspection, asset principles, aging trees, packaging, and map creation. It also contains the patch history that reveals the staged rollout.

The corpus is stronger for current procedures and exact supported fields. This report adds the historical comparison between the promised first wave and the actual March 2024 and December 2025 releases, plus synthesis of the unified-editor rationale, contextual asset testing, community beta process, and lifecycle complexity of planned asset types.

The existing Summer Solstice map-making report already analyzes the later Map Editor workflow and current terrain tooling. This report should be used for the 2023 editor vision and roadmap divergence rather than for step-by-step map creation.

## Implications for Cities2 modding

Editor and asset automation should start from current verified documentation, then use this diary only for rationale. The 2023 list of planned capabilities is not a valid feature-detection mechanism.

A robust asset workflow should include external-file validation, import, prefab configuration, contextual placement, network and entrance checks, simulation testing, packaging validation, and in-game playtesting. The diary supports the need for contextual preview but does not define the modern technical steps.

Porting a Cities: Skylines mod should be framed as reimplementation. Reuse may be possible for ideas, original source assets where licensing permits, or game-independent logic, but not for compiled binaries or assumed game APIs.

The unified editor and shared internal tooling make prefab inspection especially relevant to toolkit development. However, public documentation, installed assemblies, and actual prefab schemas must be checked before generating files or mutating components.

Multi-stage assets such as aging trees require coordinated state models. Toolkit scaffolds should not reduce them to a single mesh because the diary and current guide both establish lifecycle-aware setup.

## Implications for Cities2-MCP

This report should be retrieved for questions about the original Editor roadmap, why asset mods arrived later than map and code mods, whether Cities: Skylines I mods can be reused, the purpose of the unified editor, contextual asset preview, the modding beta group, planned asset categories, and early cross-platform promises.

For “when did this ship?” questions, Cities2-MCP should retrieve this report together with patch `1.1.0f1` and patch `1.5.2f1`. The concise answer is that map creation and code mods shipped publicly in March 2024, while custom asset creation and sharing followed in December 2025.

For current “how do I create an asset?” questions, retrieval should favor the verified `1.5.2f1` asset and Editor pages. The diary's `.fbx`, texture, color, decoration, and statistics description is introductory historical context rather than a complete recipe.

Answers should preserve roadmap language. “Planned,” “goal,” and “next step” must not be rewritten as “supported.” The same rule applies to vehicles, bushes, citizen models, and console availability.

## Uncertainties and transcript corrections

The supplied source is a complete MHTML forum snapshot. Analysis uses the first official post and excludes community replies from developer claims.

The snapshot decodes some typographic punctuation as replacement characters. Punctuation was normalized while retaining the substantive wording.

The diary says the editor would be added “as soon as it’s out of beta testing” but provides no date. Later public releases establish actual milestones; the original phrase should not be interpreted as a concrete deadline.

The current corpus confirms documented aging-tree support, but this review did not establish the current status of every vehicle, bush, or citizen-model workflow named in the 2023 roadmap. Those categories require a current documentation or installed-editor check before use.

The diary does not expose stable C# APIs, prefab type names, serialization formats, command-line tooling, or package schemas. No implementation should be generated solely from this source.

## Sources

- Colossal Order, Behind the Scenes #2: Editor, published 2023-10-18: https://forum.paradoxplaza.com/forum/developer-diary/behind-the-scenes-2-editor.1602378/
- Cities: Skylines II Wiki, Developer diaries: https://cs2.paradoxwikis.com/Developer_diaries
- Cities: Skylines II Wiki, Patch `1.1.X`: https://cs2.paradoxwikis.com/Patch_1.1.X
- Cities: Skylines II Wiki, Patch `1.5.X`: https://cs2.paradoxwikis.com/Patch_1.5.X
- Cities: Skylines II Wiki, Modding: https://cs2.paradoxwikis.com/Modding
- Cities: Skylines II Wiki, Editor: Interface: https://cs2.paradoxwikis.com/Editor:_Interface
- Cities: Skylines II Wiki, Assets: Importing: https://cs2.paradoxwikis.com/Assets:_Importing
- Cities: Skylines II Wiki, Assets: Import and Setup Aging Trees: https://cs2.paradoxwikis.com/Assets:_Import_and_Setup_Aging_Trees
- Cities: Skylines II Wiki, Map Creation: https://cs2.paradoxwikis.com/Map_Creation
