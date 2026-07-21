---
schema_version: 1
title: Adding Custom Assets Developer Diary
slug: adding-custom-assets-developer-diary
source_type: developer_diary
source_url: https://forum.paradoxplaza.com/forum/developer-diary/dev-diary-adding-custom-assets.1883646/
published_at: 2025-12-04
publication_date_basis: source_metadata
creators: Colossal Order development team
organizations: Colossal Order; Paradox Interactive
report_created_at: 2026-07-20
report_updated_at: 2026-07-20
event: Custom asset support release developer diary
game_version: 1.5.2f1
---

# Adding Custom Assets Developer Diary

## Executive summary

This diary is a compact overview of the public custom-asset workflow introduced in December 2025. Assets are created in the same Editor as maps and can be authored several at once in a shared scene. The importer reads a project root and asset folder, then creates a building, static object, or copy of an existing prefab. Creators decorate, configure components, add access and activity areas, save, and submit to Paradox Mods from the Workspace.

The most useful unique details are workflow affordances and scale limits: searches and bookmarks speed reuse of base assets; props can be attached to buildings, vehicles, and other props; there is no hard prop-count maximum even though performance imposes a practical limit; lots can be up to 1000 by 1000 tiles; three color masks form effectively unlimited authored combinations; and pathfinding areas require a Pedestrian Access Location marker.

## Source context and temporal scope

Colossal Order published the diary on 2025-12-04 with public custom-asset support in patch `1.5.2f1`. It is an orientation guide, while the official wiki contains the detailed mesh, texture, naming, component, and packaging requirements.

This report records the released workflow and practical interaction details. Current wiki pages should control exact technical inputs and any changes since release.

## Findings

### One scene can contain several assets

The Editor does not separate map and asset applications. Creators can place and edit multiple assets in one scene, use a blank ground plane, or load a map with roads and trees for scale and visual comparison. This supports contextual and batch authoring.

### Import can start from presets or an existing prefab

The Asset Importer takes a project root and an asset folder. A preset creates a building or static object, while `Existing Prefab in Project` copies an existing asset's settings as a starting point. Copied components can then be edited or extended.

Copying a prefab accelerates setup but also copies assumptions. Authors must review cost, capacity, consumption, access, effects, sub-objects, and other components rather than only replacing the mesh.

### Asset Browser supports repeated detailing work

The browser searches thousands of installed assets, remembers recent searches, and allows bookmarked items. With `Binds overlapping items to a building` enabled, placed objects become part of the building.

The Editor has no hard maximum for bound props, and props or vehicles can themselves receive child decorations. The diary explicitly warns that hundreds or thousands of props can affect performance; absence of a validation cap is not evidence of safety.

The documented shortcuts are `M` to move freely, `X`, `Y`, or `Z` to align a selected prop to a previously selected target on an axis, and `C` to copy.

### Lots, surfaces, and color variation are highly flexible

Lot depth and width can be entered directly up to 1000 by 1000 tiles. Polygonal surfaces allow non-rectangular visual areas within that space.

Three mask textures map to three independently chosen color properties. A triplet is one variation combination, and creators can define effectively unlimited combinations. Correct channel preparation and material setup still depend on the detailed wiki specification.

### Access uses paths and navigable areas

Invisible one-way or two-way vehicle paths and pedestrian paths provide explicit routes through an asset. Polygonal pathfinding areas create freely navigable surfaces and can be assigned activity or hangout purposes. Every functional pathfinding area needs a Pedestrian Access Location marker for entry and exit.

These approaches can be combined. A valid-looking plaza without an access marker or connected invisible path may remain unusable.

### Components and sub-objects define behavior

Selecting the asset opens the Object Info Panel, where creators configure cost, capacity, consumption, and other behavior. The panel also exposes props, areas, effects, and other sub-objects for editing, copying, or deletion.

The Workspace lists scene assets and is the point for saving and sharing. Publishing includes a description and screenshots, followed by serialization and submission to Paradox Mods.

## Existing corpus overlap

The Paradox-verified asset wiki is substantially deeper on file layout, meshes, textures, shaders, prefabs, lanes, effects, validation, and packaging. This diary adds an approachable end-to-end sequence plus shortcuts, multi-asset scenes, remembered searches and bookmarks, nested decoration, the stated lot maximum, and the access-marker warning.

The 2023 Behind the Scenes Editor report documents how asset support was originally planned for the first editor release but arrived much later. The REV0 report adds a professional optimization and balance case study.

## Implications for Cities2 modding

Toolkit scaffolds should validate the project-root and asset-folder layout before opening the Editor, then require an explicit review when cloning an existing prefab. Batch scenes can improve comparison but packaging should confirm that intended dependencies and sub-objects belong to each saved asset.

Performance checks should count nested props as well as mesh geometry. Path validation should verify access markers, lane direction, connections, activity areas, and service-vehicle routes.

Automated color checks should understand three-mask combinations rather than treating each color as an independent global variant.

## Implications for Cities2-MCP

Cities2-MCP should retrieve this report for orientation and workflow questions, especially multi-asset editing, cloning a prefab, prop binding and shortcuts, lot size, color variations, invisible paths, pathfinding areas, and Paradox Mods submission.

Exact file naming, texture channels, mesh constraints, and current component schemas should come from newer verified wiki pages. The report should never translate “no hard prop maximum” into “unlimited props are performant.”

## Uncertainties and transcript corrections

The diary does not enumerate supported prefab components, serialization schemas, texture requirements, LOD rules, dependency packaging, validation errors, or performance budgets. The 1000-by-1000 figure is the stated Editor lot cap at release, not a recommendation for normal assets.

MHTML punctuation artifacts were normalized and community replies excluded.

## Sources

- Colossal Order, Adding Custom Assets Developer Diary, published 2025-12-04: https://forum.paradoxplaza.com/forum/developer-diary/dev-diary-adding-custom-assets.1883646/
- Cities: Skylines II Wiki, Asset Creation: https://cs2.paradoxwikis.com/Asset_Creation
- Cities: Skylines II Wiki, Assets: Importing: https://cs2.paradoxwikis.com/Assets:_Importing
- Cities: Skylines II Wiki, Editor: Interface: https://cs2.paradoxwikis.com/Editor:_Interface
