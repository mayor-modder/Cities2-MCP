# CS2 Modding Quality Skills Design

## Purpose

Cities2-MCP should help users make better Cities: Skylines II mods, not merely more mods. The modding skills should raise the bar for safety, maintainability, user value, packaging hygiene, and honest verification while staying practical and friendly.

This design adapts the workflow style of Superpowers into CS2-specific agent skills grounded in the bundled Paradox and Cities: Skylines II modding documentation.

## Skill Set

### `cities2-modding`

General routing skill for CS2 modding questions and local mod project work.

Responsibilities:

- Identify the modding task type: conceptual docs question, scaffold, edit, build, local install for testing, package, review, or debug.
- Use Cities2-MCP wiki retrieval before giving API, project-structure, localization, UI, settings, or toolchain advice.
- Use MCP workflow tools when the target project is inside an allowed workspace.
- Use explicit fallback behavior when a client blocks MCP workflow tools, especially Codex plugin cache allowlist cases.
- Route review-heavy requests to `cities2-mod-review`.
- Route failures, logs, and bug reproduction to `cities2-mod-debugging`.
- Route package, publish, upload, or distribution requests to `cities2-mod-release`.
- Treat local installs after a build or fix as playtesting handoff moments, not as distribution.

### `cities2-mod-review`

Review skill for requests such as "review this mod", "is this ready?", "audit this", or "what should I improve?"

Review rubric:

- Safety and security: filesystem access, process execution, network calls, persistence, telemetry, credentials, path handling, destructive behavior.
- Compatibility and maintainability: game/toolchain target, dependency footprint, project structure, reproducible build, clear separation of UI/C#/localization/settings concerns.
- User value: clear purpose, non-placeholder behavior, understandable settings, useful descriptions, known limitations.
- Packaging hygiene: README, changelog, license or attribution notes, metadata, versioning, thumbnail readiness for Paradox Mods.
- Verification: build/analyze results, installed output, manual in-game checks, relevant logs/debuggers, unverified behavior.

Output should lead with concrete findings and risk level, then actionable next steps.

### `cities2-mod-debugging`

CS2-specific debugging skill for build failures, packaging failures, runtime errors, game logs, UI debugger issues, settings/localization problems, and "the mod loads but does not work" reports.

Workflow:

1. Capture the exact symptom, expected behavior, and reproduction path.
2. Inspect relevant project files and logs before guessing.
3. Classify the failure: missing toolchain, dependency issue, TypeScript/C# compile issue, post-processor problem, package layout, playset/install issue, runtime/game log issue, UI debugger issue, or game-version compatibility issue.
4. Query CS2 modding docs when the failure touches documented toolchain, API, project structure, localization, UI, settings, or packaging behavior.
5. Make one focused fix at a time.
6. Re-run the narrowest useful verification.
7. If the fix requires in-game observation, provide a playtesting handoff and do not claim the bug is fixed until behavior or logs support it.

This skill should not become general gameplay/save debugging. It is for mod development and mod behavior.

### `cities2-mod-release`

Release-readiness skill for package, publish, upload, distribute, or Paradox Mods preparation requests.

Responsibilities:

- Confirm local build/analyze status.
- Require local playtesting before packaging or publishing for distribution.
- If local playtesting has not happened, stop and provide a tailored checklist.
- Allow an explicit user override for packaging untested builds only if the final answer clearly labels the result as not gameplay-verified.
- Check metadata, README, changelog, license/attribution, versioning, thumbnail readiness, compatibility target, and known limitations.
- Warn when the installed game appears newer than the bundled corpus or package metadata.
- For derivative/forked mods, preserve attribution and do not imply redistribution rights when licensing is unclear.

## Shared Safety Rules

Each specialized skill should carry enough safety policy locally that it works even when only that skill is loaded.

Refuse requests to:

- Corrupt, sabotage, or tamper with saves, user data, mods, game installs, or other files.
- Build malware-like behavior, including hidden persistence, credential/token collection, keylogging, unwanted network calls, stealth telemetry, or evasion.
- Bypass Paradox Mods policies, platform rules, paid content restrictions, license terms, or attribution requirements.
- Remove attribution or license notices.
- Pass off someone else's mod, code, or assets as original work.
- Circumvent takedowns, explicit author restrictions, or platform moderation.

Pause and clarify before:

- Editing live saves directly.
- Replacing installed game files instead of using supported mod locations.
- Performing broad moves/deletes in game, mod, or user-data directories.
- Adding network access, telemetry, or user-data collection.
- Publishing, uploading, rebranding, monetizing, or redistributing a modified version of someone else's mod when permission or license terms are unclear.

Allowed with care:

- Inspecting, patching, forking, or modernizing local mod source, including public GitHub-hosted CS2 mods.
- Maintaining private patches for personal use.
- Helping users understand unlicensed public source, while clearly saying that public source does not automatically grant redistribution rights.
- Backing up, read-only inspecting, or recovering project files through documented safe workflows.

## Playtesting Handoff

When an agent builds, installs, or applies a fix that needs in-game validation, it should not stop at "build passed."

The final response should include:

- What was built and where it was installed.
- Whether the game, playset, or client needs to be restarted or refreshed.
- Exact in-game steps to exercise the change.
- Expected success signal.
- Likely failure signal.
- Relevant evidence to inspect, such as `Modding.log`, Unity/Player logs, browser console, UI debugger at `localhost:9444`, installed mod files, or Paradox Mods playset state.

When the user reports that they are testing, have tested, or saw an in-game result, the agent should treat that as a debugging continuation. If the agent can access logs, debugger output, installed files, or playset state, it should inspect them instead of relying only on the user's summary. If it cannot access the evidence, it should ask for the smallest specific log/debugger excerpt needed.

Do not claim a fix is verified until both the build and the in-game behavior or relevant logs support it.

## Distribution Gate

A successful build is not enough to package or publish a mod for distribution.

Before packaging, uploading, publishing, or preparing a distribution artifact after code changes, the agent must require one of:

- User-confirmed local playtesting with enough detail to know what was exercised.
- Concrete logs/debugger/game evidence showing the changed behavior worked.
- An explicit user override acknowledging that the mod is being packaged untested.

If none is present, stop and provide a tailored playtest checklist instead of packaging or publishing.

If the user explicitly overrides, the final answer must label the result as built or packaged but not gameplay-verified.

## Implementation Notes

- Keep the existing `cities2-modding` skill as the default entry point, but make it route to the specialized skills.
- Add the new skills to the base `skills/` tree and both plugin distributions.
- Keep each skill concise enough to load comfortably in agent context.
- Prefer duplicated critical safety rules over a shared reference file that a client may fail to load.
- Add a maintainer-local, gitignored review skill under `.codex/` that compares finished CS2 skills against the relevant Superpowers equivalents before release. This skill is a development aid only and should not be packaged or documented for end users.
- Update tests to assert that the new skills are packaged, documented, and included in Claude/Codex plugin manifests.
- Add at least one test assertion for the distribution gate and playtesting handoff language.

## Local Skill Style Review

The implementation should include a local agent skill in the repository working tree, kept out of git by the existing `.codex/` ignore rule. Its job is to review the finished CS2 skills before they are committed or released.

The review skill should:

- Compare `cities2-mod-debugging` against Superpowers `systematic-debugging`.
- Compare `cities2-mod-review` against Superpowers review-oriented skills where relevant.
- Compare `cities2-mod-release` against Superpowers finishing/release-readiness patterns where relevant.
- Check that the CS2 skills are operational instructions, not essays.
- Check that trigger language is specific, concise, and unlikely to overload normal context.
- Check that safety, playtesting, and distribution-gate rules survived into each relevant skill.
- Suggest edits, but leave final implementation choices to the maintainer.

Because this reviewer is local and gitignored, it can reference installed Superpowers skill paths on the maintainer's machine. The shipped Cities2-MCP package should not depend on it.

## Success Criteria

- Agents using Cities2-MCP give CS2-specific modding guidance from the official/bundled docs.
- Build/package/review requests include a concrete quality or release-readiness pass.
- Debugging requests follow a disciplined CS2-specific workflow.
- Packaging or publishing is blocked until local playtesting is confirmed or explicitly overridden.
- Unsafe, illegal, unethical, or attribution-stripping requests are refused.
- Forking and local modification of public mod source remains supported, with careful redistribution guidance.
- Maintainer review of the finished skills has a local, repeatable Superpowers-style checklist without adding user-facing or packaged artifacts.
