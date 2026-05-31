---
name: cities2-mod-debugging
description: "Use when debugging Cities: Skylines II mod build failures, packaging failures, runtime errors, game logs, UI debugger issues, or mod behavior that does not work in game."
metadata:
  short-description: "Debug CS2 mod failures with evidence"
---

# Cities2 Mod Debugging

Debug CS2 mods with evidence, one focused fix at a time. Use MCP-backed docs for CS2-specific assumptions and record negative constraints that rule out unsafe or misleading shortcuts.

**Core principle:** Always find root cause before attempting fixes. Plausible source-code guesses are still guesses.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT-CAUSE EVIDENCE FIRST
```

If the failure only appears after the mod is installed, loaded, or run in game,
source-code inspection is not enough. Inspect runtime evidence first or state
that root cause is unverified and stop before patching.

## Debugging Workflow

1. State the failing symptom in one sentence: build, package, launch, runtime, UI, save, or gameplay behavior.
2. Gather the smallest useful evidence before changing code.
3. Classify the failure category and state the likely root cause, or say what remains unknown.
4. Form one hypothesis tied to a file, API, asset, package step, or game log entry.
5. Apply one focused fix.
6. Re-run the narrowest relevant check and compare evidence before/after.
7. After applying a fix for runtime, UI, save, or gameplay behavior, either run
   the relevant build or install check or tell the user exactly why it could
   not run. Then provide playtesting steps without waiting for the user to ask.
8. If the fix fails or the symptom changes, return to evidence and hypothesis instead of stacking unrelated edits.
9. After three failed fix attempts, pause and ask whether the architecture, template choice, or modding approach should change.

## Runtime And UI Gate

For "build passes but it does not work in game" problems, complete at least one
runtime check before editing:

- installed package layout and file timestamps;
- enabled playset/load state;
- `Modding.log`, `Unity/Player logs`, launch output, or exception stack traces;
- UI debugger state at `localhost:9444` for UI mods.

Source files, `package.json`, and `dist/ui.js` can support a hypothesis, but
they do not prove why an installed CS2 mod failed at runtime. If those are the
only facts available, hand the user a playtesting/log collection step and mark
the root cause unverified. Do not patch a likely selector, import, path, timing,
or binding issue first and ask for logs only if it fails.

## Red Flags - STOP

If you catch yourself thinking any of these, return to evidence before editing:

- "Quick scan, then patch."
- "It is probably just the selector/import/path/timing."
- "The build passed, so source and bundle inspection are enough."
- "Patch now and ask for logs if it still fails."
- "The user is waiting, so make the likely fix first."
- "This is not blind because I checked `dist/ui.js`."

All of these are guesses for CS2 runtime/UI failures. A fast source scan is not
root-cause evidence when the missing evidence is installed state, logs, playset
state, or debugger state.

## Evidence Sources

- Build output, package output, project file, manifest, dependency list, generated artifacts, and install location.
- `Modding.log`, `Unity/Player logs`, game launch output, exception stack traces, and mod loader messages.
- UI debugger evidence from `localhost:9444` for React/TypeScript UI mods when the game and debugger are available.
- Screenshots, reproduction steps, user playtesting notes, save copies, and version/build numbers.
- MCP server wiki/reference results for API, toolchain, UI, localization, packaging, and compatibility checks.

For runtime or UI behavior that fails only in game, first distinguish package
layout, installed files, playset/load state, game logs, UI debugger state, and
source code. Do not use "quick scan, then patch" as a compromise when the
missing evidence is exactly what separates a plausible guess from root cause.

## CS2 Failure Categories

- Toolchain: missing .NET runtime, post-processor issues, bad project references, stale generated files, or wrong output folders.
- Packaging: missing manifest data, bad thumbnail path, included build junk, missing dependencies, or archive layout mismatch.
- Runtime: load order, Harmony patch fragility, null game systems, unchecked reflection, settings migration errors, or unsupported API assumptions.
- UI: failed asset build, stale bundles, bad bindings, broken localization keys, debugger unreachable, or frontend/backend contract mismatch.
- Saves and gameplay: data mutation risks, versioned component changes, assumptions about simulation timing, or live save edits.

## Playtesting Handoff

Treat user playtesting as a debugging continuation, not a finished verification step. A playtesting handoff should include the exact build/package, scenario to try, expected behavior, what logs to collect, and what screenshots or debugger state would help.

After applying a fix for an in-game symptom, do not stop at the code change.
If build or install commands are available, run the appropriate check before
handoff. If they are unavailable, name the missing prerequisite. Always include
playtesting steps for the user: which build/package to test, whether to restart
the game or playset, the exact scenario to exercise, the expected result, and
which logs or debugger evidence to bring back.

Cities: Skylines II must be closed before installing or replacing a local mod
build. If the game is running, do not install over it. Tell the user to close Cities: Skylines II first. Then install or replace the build, launch the game,
confirm the mod/playset is enabled if needed, and run the playtest scenario.

When available, ask for `Modding.log`, `Unity/Player logs`, `localhost:9444` debugger evidence, and clear reproduction steps. If the user cannot gather logs, use their observations but mark the remaining uncertainty.

For save-affecting issues, prefer read-only diagnostics, backed-up saves, copied saves, offline workflows, and supported APIs. Do not ask the user to edit a live save until the risk is explicit and they have a backup.

## Verification Rule

Do not claim a fix is verified until the relevant check has actually run and the new evidence supports it. Build success verifies compilation only. Package success verifies packaging only. Gameplay behavior needs local playtesting or an explicit statement that it remains untested.
