---
name: cities2-mod-review
description: "Use when reviewing a Cities: Skylines II mod for safety, maintainability, user value, packaging hygiene, verification gaps, or readiness to improve."
metadata:
  short-description: "Review CS2 mod quality and readiness"
---

# Cities2 Mod Review

Review the mod as a good-faith quality pass: find practical risks, missing evidence, and user-impacting gaps. Prefer documented best practices from the MCP server when judging CS2-specific APIs, packaging, UI, localization, saves, and toolchain behavior.

## Review Sources

- Inspect the mod files, build/package config, README/release notes, logs, screenshots, and test notes when available.
- Use MCP server wiki/reference lookup for CS2 modding claims before treating them as a best practice.
- Separate normative modding constraints from descriptive gameplay statements. Gameplay facts explain what the game does; modding constraints say what the mod should or must do safely.
- Separate evidence levels in findings: observed in project files, supported by MCP or project documentation, and inferred recommendation. Do not present an inference as a sourced rule.
- Do not infer React, a loader pattern, runtime requirement, or packaging requirement from a filename alone. A `.tsx` file only proves TypeScript JSX syntax; require package dependencies, imports, templates, or documentation before naming React or prescribing React-specific fixes.
- If a CSS file is not imported, bundled, or otherwise loaded by inspected files, describe its current impact as no effect. Keep any global-theme or runtime styling risk conditional on evidence that the CSS becomes loaded.
- If source access is partial, say what was reviewed and what remains unknown.
- For diff, branch, or PR-style reviews, identify the reviewed range or changed files, compare against the user request or plan, inspect affected call sites, and state if no diff or requirements were available.
- When judging readiness, name the exact evidence that would prove the next stage: clean build, package artifact, installed package/playset smoke launch, local playtest results or notes, relevant logs, and UI debugger or screenshots for UI mods. Keep local playtest separate from install/playset launch; do not collapse it into "installed local package/playset launch" or "smoke-test in a local playset." If the scaffold cannot build yet, still list local playtest results or notes as a downstream gate after the build/package blockers are fixed.
- If readiness is absent, unproven, or blocked, end with a `Readiness evidence still needed:` line or list that explicitly names: clean build, package artifact, installed package/playset smoke launch, local playtest results or notes, logs, and UI debugger or screenshots for UI mods.

## Actionable Scaffold Review Checklist

For a small or incomplete scaffold review, use repeatable finding blocks instead of prose-only commentary:

- `[Severity] Finding title`
- `Evidence level:` observed in project files, supported by MCP/project documentation, or inferred recommendation.
- `Evidence:` name the concrete file paths or docs inspected.
- `Likely impact:` say what breaks, stays inert, remains unproven, or misleads users.
- `Concrete fix:` name the next edit or verification step.

If the scaffold contains unwired UI or style files, explicitly review current wiring before framework assumptions. A `.tsx` file proves only TSX/JSX syntax; do not make missing React loader the top confirmed issue without package, import, template, or documentation evidence. If a CSS file is not imported, bundled, registered, or loaded, say the file has no current effect and no current runtime styling risk or benefit; keep any future global-theme concern conditional on loading it.

For minimal scaffolds, include the highest-impact missing build/package issue when present, then the baited framework/style evidence issue, then readiness evidence still needed. Do not stop after correcting the user's React or loader assumption.

## Multi-Agent Review Offer

Before a large diff, branch, PR, release-readiness, or quality audit, check
whether external review agents are available on this user's machine. Use normal
PATH lookup, not hardcoded install paths: `command -v codex`, `command -v
claude`, and `command -v agy` on POSIX shells, or `Get-Command codex`,
`Get-Command claude`, and `Get-Command agy` on Windows.

Ask before running external reviewers because they may use network access,
credentials, tokens, paid plans, or local configuration. If two or more external
reviewers are available, offer a 3-way review: this agent's internal review plus
two external agents. If one external reviewer is available, offer a 2-way review.
If no external reviewer is available, continue with the normal CS2 mod review
without treating that as a problem.

Before opt-in, only use PATH lookup to detect candidates. Do not run external CLI commands, including `--help`, version checks, print modes, or review modes, until the user approves the external review offer.

Prefer diverse external reviewers. Use documented noninteractive review modes
when available, checking `--help` if needed: `codex review`, `claude ultrareview`
or `claude --print` with a review prompt, and `agy --print` or the installed
Antigravity print mode with a review prompt.

Treat `agy`/Antigravity as file-output-first. Its `--print` stdout can be empty
even when the model ran, and `--log-file` is an execution log for troubleshooting,
not the final review artifact. When using `agy`, prompt it to write the final
review to a specific temporary review file, redirect stdout to a separate fallback
capture, and read the log only if the review file and stdout capture are missing
or unclear. Offer to remove temporary review files after synthesizing the final
answer, but keep them if the user wants an audit trail.

Do not outsource judgment. Synthesize the results findings-first, de-duplicate
overlap, distinguish confirmed issues from single-reviewer concerns, and validate
external findings against the CS2 review rubric, documented standards, safety
rules, attribution rules, and available project evidence.

## Review Rubric

- User value: clear purpose, expected audience, settings/defaults, localization, and in-game discoverability.
- Maintainability: small focused systems, readable names, minimal global state, predictable settings migrations, and no needless coupling to unrelated game systems.
- Compatibility: avoids brittle version assumptions, unchecked Harmony patches, broad reflection hooks, and silent failure paths.
- Packaging hygiene: manifest metadata, dependencies, thumbnail, build artifacts, README, changelog, and excluded temporary files.
- Verification gaps: build result, static analysis, smoke launch, local playtesting, logs, UI debugger evidence, and known untested areas.

## Documented Standards

Use documented best practices as defaults when the docs support them. Quote or cite compactly by page/tool result when helpful.

Treat negative constraints as review findings when they prevent likely mistakes:

- do not package or distribute from build success alone;
- should not edit live saves as a default troubleshooting path;
- must not remove attribution, license, or notices;
- cannot assume public repositories grant redistribution;
- can't claim gameplay verification without local playtesting or explicit user notes;
- won't treat missing logs as proof that runtime behavior is clean.

## Safety And Attribution

Public source does not automatically grant redistribution rights. Check the license, mod page terms, bundled assets, copied code, and derivative-work notices before recommending upload or redistribution.

Do not remove attribution or license notices.

For save-affecting behavior, prefer read-only diagnostics, backups, copied-save workflows, offline reproduction, and supported APIs. Live save edits are a pause/clarify risk unless the user explicitly accepts the risk and has a backup.

## Output Style

Lead with findings ordered by severity. Include file/path evidence when available, the violated rule or best practice, likely impact, and a concrete fix. Keep praise brief. For missing evidence, say exactly what would verify readiness.
