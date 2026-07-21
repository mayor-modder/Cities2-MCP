---
schema_version: 1
title: Modding Development Diary #3 - Code Modding
slug: code-modding-developer-diary
source_type: developer_diary
source_url: https://forum.paradoxplaza.com/forum/developer-diary/modding-development-diary-3-code-modding.1626926/
published_at: 2024-03-21
publication_date_basis: source_metadata
creators: Sergey "MacSergey" Golovkin
organizations: Colossal Order; Paradox Interactive
report_created_at: 2026-07-20
report_updated_at: 2026-07-20
event: Cities: Skylines II code modding launch developer diary
game_version: 1.1.0f1 prerelease
---

# Modding Development Diary #3 - Code Modding

## Executive summary

This diary by Colossal Order developer and veteran modder MacSergey is a foundational statement of the intended Cities: Skylines II code-modding architecture. The preferred extension model is to add an ECS system to the game's update loop and access entity/component data, rather than patching many base-game methods. Harmony remains possible for managed code but cannot patch code transformed into unmanaged Burst output.

The official toolchain, project template, post-processor, dependency handling, automatic settings registration, and IDE publishing workflow were designed to remove generic setup work and guide mods toward the same ECS and Burst model as the game. Several 2024 workflow details may have evolved, but the architectural reasons remain highly relevant to toolkit design.

## Source context and temporal scope

The diary was published on 2024-03-21, four days before public code-mod support. MacSergey wrote it from both developer and mod-author perspectives and described the first official toolchain and template.

Current templates, target frameworks, package versions, publishing commands, and supported APIs must be taken from the installed toolchain and current wiki. This report concentrates on design intent and compatibility strategy.

## Findings

### The toolchain owns the development environment

The planned one-button setup installed dependencies and external tools including Unity, Burst, and ECS support. It could notify creators when requirements changed. The project template used .NET's template mechanism to configure references, paths, and post-build actions so a build produced a post-processed mod in the game-visible location.

This means manually assembling references or bypassing the generated build pipeline can omit required transformations. Modern tools should inspect the active template and toolchain rather than reproduce paths from memory.

### Post-processing can be functionally required

The Mod Post Processor was intended to apply Burst and low-level optimizations and support Unity source-generated APIs. The diary warns that code using some Unity APIs without the expected template and post-processing can throw `NotImplementedException`; post-processing is therefore not only an optional performance pass.

Not every system benefits from Burst, and forcing it onto unsuitable managed behavior can be counterproductive. The correct choice depends on what the system does and which APIs it calls.

### ECS systems are the preferred extension boundary

Rather than injecting a feature into many methods, a mod can create its own system and register it in the update loop. The game then schedules it alongside base-game systems. Entity and component data are available to mod systems, allowing many behaviors to be observed or changed without modifying the original method bodies.

This reduces coupling to method signatures and internal control flow. It does not make a mod immune to updates: components, system ordering, data meaning, or public APIs can still change.

### Harmony has a specific technical boundary

Harmony patches managed methods. Burst compilation can turn part of the game into unmanaged code, which Harmony cannot patch. A missing or ineffective patch may therefore reflect the target's compilation path rather than an incorrect Harmony signature alone.

Toolkit recommendations should first ask whether the desired behavior can be implemented as an ECS system or supported registration. Harmony remains a targeted fallback for managed code where no supported extension point exists.

### Registration APIs reduce compatibility risk

The diary uses settings as an example: properties marked with attributes can be collected into an automatically generated settings page, registered through a simple call. This avoids each mod reimplementing UI construction and reduces reliance on game internals.

The broader principle is to prefer official generic facilities for lifecycle, settings, dependencies, and publishing. Such facilities concentrate compatibility work in the toolchain and game rather than in every mod.

### Dependency handling avoids a user-defined load order

Cities: Skylines II was designed to detect complicated dependency relationships and resolve conflicts where mods use shared dependencies. The diary says there is no user-managed load order in which one mod must be placed before another.

That statement should not be broadened into “system order never matters.” ECS update ordering and explicit before/after constraints remain relevant inside code. It means players should not need a Cities: Skylines I-style mod list order to resolve assemblies.

### Modder feedback shaped the public surface

Experienced mod authors received early access and supplied feedback about APIs and access gaps. MacSergey's account explains why the team focused on tasks that are trivial with internal engine tools but costly without them. This is useful context for evaluating official abstractions: many exist specifically to eliminate repeated community workarounds.

## Existing corpus overlap

The wiki corpus contains current code-mod templates, ECS guidance, settings, dependencies, build, logging, and publishing instructions. It should control implementation details. The 2024 Unite ECS report provides deeper examples of systems, queries, change filters, jobs, buffers, and serialization.

This diary adds the clearest first-party explanation of why the official pipeline exists, why post-processing may be mandatory, where Harmony stops at Burst-generated unmanaged code, and how system registration is intended to improve update compatibility.

## Implications for Cities2 modding

Toolkit scaffolds should begin from the installed official template, retain its post-processing, and register systems through supported update phases. They should not hardcode copied game assemblies or infer tool versions from an old project.

Debugging a `NotImplementedException` should include checking whether the mod was built through the proper post-processor. Debugging a Harmony patch should include checking whether the target remains managed and whether ECS observation or mutation is a better extension point.

Compatibility review should distinguish dependency resolution from ECS ordering. Mods need explicit, minimal system-order constraints even though users do not manually sort the playset.

## Implications for Cities2-MCP

This report should be a high-value source for architectural questions: ECS versus Harmony, why the post-processor matters, why generated templates are preferred, and why a mod has no user-facing load-order setting.

For exact code, Cities2-MCP must favor current verified examples and installed assemblies. The diary names concepts but does not define stable namespaces, method signatures, attributes, or package versions.

## Uncertainties and transcript corrections

The stated 30-to-40-times speedup is a possible best-case comparison for some calculations, not a general performance guarantee. The source includes no benchmark methodology.

Toolchain UX, IDE publishing, dependency resolution, and settings APIs may have changed after 2024. The MHTML punctuation was normalized and community replies were excluded.

## Sources

- Sergey Golovkin, Modding Development Diary #3 - Code Modding, published 2024-03-21: https://forum.paradoxplaza.com/forum/developer-diary/modding-development-diary-3-code-modding.1626926/
- Cities: Skylines II Wiki, Code modding: https://cs2.paradoxwikis.com/Code_modding
- Cities: Skylines II Wiki, Modding: https://cs2.paradoxwikis.com/Modding
- Colossal Order, Tapping the Entity Component System for Cities: Skylines II, Unite 2024 research report: `2024-10-09-tapping-ecs-cities-skylines-ii.md`
