---
name: cities2-mod-release
description: "Use when preparing a Cities: Skylines II mod to package, upload, publish, distribute, or release to Paradox Mods or another public channel."
metadata:
  short-description: "Check CS2 mod release readiness"
---

# Cities2 Mod Release

Use this skill before packaging, uploading, publishing, distributing, or otherwise releasing a CS2 mod. The goal is to prevent ordinary release mistakes before they reach players.

## Source Evidence

Use MCP server wiki/reference lookup for CS2-specific packaging, toolchain, and modding claims before treating them as release requirements. Use project files, build output, package contents, logs, screenshots, and user playtesting notes as release evidence.

## Distribution Gate

A successful build is not enough for distribution. Before public release, require local playtesting of the packaged mod in game, or an explicit user override that the release is not gameplay-verified.

If the user chooses the override, label the release notes or handoff as not gameplay-verified and list the missing checks. Do not imply Paradox Mods readiness from compile/package success alone.

For save-affecting mods, pause before release if testing used only a live save. Prefer backed-up saves, copied-save workflows, offline reproduction, and supported APIs.

## Release Sources

- Inspect the packaged files, manifest, build output, README, changelog, license, attribution, thumbnail, and install notes.
- Use MCP server wiki/reference lookup for CS2-specific package, toolchain, UI, localization, and asset claims.
- Treat user playtesting reports as release evidence only when they describe the packaged build and the game behavior they exercised.

## Release Readiness Checklist

- Build and package from a clean tree or known commit.
- Confirm the packaged archive installs in the expected CS2 mod location.
- Before install, close Cities: Skylines II before replacing the packaged build;
  the game must be closed before local mod files are replaced.
- Run local playtesting with the packaged build, not only the development build.
- Inspect `Modding.log` and game logs after launch and after exercising the main feature.
- Check manifest metadata, mod name, version, dependencies, supported game version, description, thumbnail, and tags.
- Confirm the thumbnail is present, appropriate, and referenced correctly.
- Exclude temporary files, source-only artifacts, local paths, secrets, generated cache files, and unrelated assets.
- Include clear install/use notes, known limitations, changelog, license, attribution, and support/contact path.
- Mark any missing check as a release risk instead of silently passing it.

## Derivative Mods And Attribution

Public source does not automatically grant redistribution rights. Before releasing copied, forked, derived, or bundled work, check the license and original mod/source terms.

Keep attribution, license files, copyright notices, asset credits, and required source links. Do not remove notices to make a package look original. If rights are unclear, pause and ask the user whether they have permission or want help replacing the dependency.

When adapting ideas without code/assets, still credit inspirations when the community context expects it, but distinguish courtesy attribution from legal license obligations.

## Output Style

Return a release decision first: ready, ready with explicit user override, or blocked. Then list concrete blockers, warnings, and the smallest next checks.

Use practical language: what must change before upload, what should change soon, and what can wait. Keep normative modding constraints separate from descriptive gameplay statements.
