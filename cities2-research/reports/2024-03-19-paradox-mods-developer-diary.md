---
schema_version: 1
title: Modding Development Diary #1 - Paradox Mods
slug: paradox-mods-developer-diary
source_type: developer_diary
source_url: https://forum.paradoxplaza.com/forum/developer-diary/modding-development-diary-1-guest-entry-paradox-mods-in-cities-skylines-ii.1626999/
published_at: 2024-03-19
publication_date_basis: source_metadata
creators: Paradox Mods team
organizations: Paradox Interactive; Colossal Order
report_created_at: 2026-07-20
report_updated_at: 2026-07-20
event: Cities: Skylines II modding launch developer diary
game_version: 1.1.0f1 prerelease
---

# Modding Development Diary #1 - Paradox Mods

## Executive summary

This short launch diary documents the product model behind official Cities: Skylines II mod distribution: in-game discovery, web management, cloud-synchronized playsets, dependency-tree resolution, creator metadata, and support for local mods that are not cloud backed. Its durable value is the distinction between a subscribed Paradox Mods item and a local item merely added to a playset.

The diary predates later changes to supported content types, moderation, clients, and consoles. It should be used to explain the original platform contract, not as current upload or compatibility documentation.

## Source context and temporal scope

The Paradox Mods team published the diary on 2024-03-19, six days before the first public modding release. The contemporary promise covered maps and code mods, with creator instructions linked separately.

All current publishing requirements, supported game versions, content categories, and platform limitations must be checked against current Paradox Mods and official modding documentation.

## Findings

### Playsets are synchronized mod configurations

The in-game interface was designed for discovery, search, browsing, staff highlights, and playset management. Playsets act as named, toggleable mod configurations. They can also be changed on the Paradox Mods website and synchronized back to the game and across devices.

When a selected mod declares dependencies, the client offers to add the full dependency tree. This describes intended dependency resolution, but does not prove that arbitrary version conflicts or optional integrations can always be solved automatically.

### Local and hosted mods have different durability

The game can add local mods from any source to a playset, but those files are not uploaded or cloud-synchronized. A synchronized playset may therefore remember configuration while still lacking the local payload on another machine.

This is an important diagnostic distinction: “present in the playset” does not necessarily mean “available from Paradox Mods,” and restoring the playset does not restore private local binaries.

### Creator metadata is part of distribution

Creators can provide descriptions, screenshots, dependencies, release notes, and supported game versions, and may enable a discussion section. Much of this metadata can be edited from the website after upload.

Metadata communicates compatibility but does not guarantee it. The installed payload, declared dependency graph, game version, and runtime result still require verification.

### Discussion surfaces are connected

The diary describes mod discussions accessible from the game and forums, plus creator-supplied links to other platforms. That reflects the intended community surface, but current UI availability should be verified rather than inferred from this launch preview.

## Existing corpus overlap

The corpus contains current Paradox Mods, modding, packaging, and publishing guidance. It is better for commands and current policy. This report adds the launch rationale for cloud playsets, full-tree dependency prompts, and the explicit limitation of local content.

The code-modding diary and current mod-release skill cover the creator pipeline more deeply.

## Implications for Cities2 modding

Support tools should inventory playset entries and installed payloads separately. A missing local dependency, stale subscribed version, or metadata mismatch can all look like a playset problem while requiring different fixes.

Release tooling should treat description, supported version, dependency declarations, screenshots, and release notes as part of the product. Dependency graphs should be validated before upload rather than relying solely on client-side prompts.

## Implications for Cities2-MCP

Cities2-MCP should use this report for questions about the purpose of playsets, cross-device synchronization, dependency prompts, and why a local mod is not restored from the cloud.

For upload procedures, platform support, or current moderation rules, newer verified documentation must take priority.

## Uncertainties and transcript corrections

The source is a pre-release platform overview and omits implementation detail, failure modes, version-resolution rules, storage locations, and current platform limitations. It does not promise that all mod types work on every platform.

The MHTML's typographic punctuation was normalized. Community replies were excluded.

## Sources

- Paradox Mods team, Modding Development Diary #1 - Paradox Mods, published 2024-03-19: https://forum.paradoxplaza.com/forum/developer-diary/modding-development-diary-1-guest-entry-paradox-mods-in-cities-skylines-ii.1626999/
- Cities: Skylines II Wiki, Paradox Mods: https://cs2.paradoxwikis.com/Paradox_Mods
- Cities: Skylines II Wiki, Modding: https://cs2.paradoxwikis.com/Modding
