---
name: cities2-mod-review
description: "Use when reviewing a Cities: Skylines II mod for safety, maintainability, user value, packaging hygiene, verification gaps, or readiness to improve."
metadata:
  short-description: "Review CS2 mod quality and readiness"
---

# Cities2 Mod Review

Review the mod as a good-faith quality pass: find practical risks, missing evidence, and user-impacting gaps. Prefer corpus-backed best practices from Cities2-MCP when judging CS2-specific APIs, packaging, UI, localization, saves, and toolchain behavior.

## Review Sources

- Inspect the mod files, build/package config, README/release notes, logs, screenshots, and test notes when available.
- Use Cities2-MCP wiki/reference lookup for CS2 modding claims before treating them as a best practice.
- Separate normative modding constraints from descriptive gameplay statements. Gameplay facts explain what the game does; modding constraints say what the mod should or must do safely.
- If source access is partial, say what was reviewed and what remains unknown.

## Review Rubric

- User value: clear purpose, expected audience, settings/defaults, localization, and in-game discoverability.
- Maintainability: small focused systems, readable names, minimal global state, predictable settings migrations, and no needless coupling to unrelated game systems.
- Compatibility: avoids brittle version assumptions, unchecked Harmony patches, broad reflection hooks, and silent failure paths.
- Packaging hygiene: manifest metadata, dependencies, thumbnail, build artifacts, README, changelog, and excluded temporary files.
- Verification gaps: build result, static analysis, smoke launch, local playtesting, logs, UI debugger evidence, and known untested areas.

## Corpus-Backed Standards

Use corpus-backed best practices as defaults when the docs support them. Quote or cite compactly by page/tool result when helpful.

Treat negative constraints as review findings when they prevent likely mistakes:

- do not package or distribute from build success alone;
- should not edit live saves as a default troubleshooting path;
- must not remove attribution, license, or notices;
- cannot assume public repositories grant redistribution;
- can't claim gameplay verification without local playtesting or explicit user notes;
- won't treat missing logs as proof that runtime behavior is clean.

## Safety And Attribution

public source does not automatically grant redistribution rights. Check the license, mod page terms, bundled assets, copied code, and derivative-work notices before recommending upload or redistribution.

Do not remove attribution or license notices.

For save-affecting behavior, prefer read-only diagnostics, backups, copied-save workflows, offline reproduction, and supported APIs. Live save edits are a pause/clarify risk unless the user explicitly accepts the risk and has a backup.

## Output Style

Lead with findings ordered by severity. Include file/path evidence when available, the violated rule or best practice, likely impact, and a concrete fix. Keep praise brief. For missing evidence, say exactly what would verify readiness.
