---
name: cities2-mod-debugging
description: "Use automatically when debugging Cities: Skylines II mod build failures, packaging failures, runtime errors, game logs, UI debugger issues, or mod behavior that does not work in game."
metadata:
  short-description: "Debug CS2 mod failures with evidence"
---

# Cities2 Mod Debugging

Debug CS2 mods with evidence, one focused fix at a time. Use corpus-backed docs for CS2-specific assumptions and record negative constraints that rule out unsafe or misleading shortcuts.

## Debugging Workflow

1. State the failing symptom in one sentence: build, package, launch, runtime, UI, save, or gameplay behavior.
2. Gather the smallest useful evidence before changing code.
3. Form one hypothesis tied to a file, API, asset, package step, or game log entry.
4. Apply one focused fix.
5. Re-run the narrowest relevant check and compare evidence before/after.
6. If the symptom changes, update the hypothesis instead of stacking unrelated edits.

## Evidence Sources

- Build output, package output, project file, manifest, dependency list, generated artifacts, and install location.
- `Modding.log`, `Unity/Player logs`, game launch output, exception stack traces, and mod loader messages.
- UI debugger evidence from `localhost:9444` for React/TypeScript UI mods when the game and debugger are available.
- Screenshots, reproduction steps, user playtesting notes, save copies, and version/build numbers.
- Cities2-MCP wiki/reference results for corpus-backed API, toolchain, UI, localization, packaging, and compatibility checks.

## CS2 Failure Categories

- Toolchain: missing .NET runtime, post-processor issues, bad project references, stale generated files, or wrong output folders.
- Packaging: missing manifest data, bad thumbnail path, included build junk, missing dependencies, or archive layout mismatch.
- Runtime: load order, Harmony patch fragility, null game systems, unchecked reflection, settings migration errors, or unsupported API assumptions.
- UI: failed asset build, stale bundles, bad bindings, broken localization keys, debugger unreachable, or frontend/backend contract mismatch.
- Saves and gameplay: data mutation risks, versioned component changes, assumptions about simulation timing, or live save edits.

## Playtesting Handoff

Treat user playtesting as a debugging continuation, not a finished verification step. A playtesting handoff should include the exact build/package, scenario to try, expected behavior, what logs to collect, and what screenshots or debugger state would help.

When available, ask for `Modding.log`, `Unity/Player logs`, `localhost:9444` debugger evidence, and clear reproduction steps. If the user cannot gather logs, use their observations but mark the remaining uncertainty.

For save-affecting issues, prefer read-only diagnostics, backed-up saves, copied saves, offline workflows, and supported APIs. Do not ask the user to edit a live save until the risk is explicit and they have a backup.

## Verification Rule

Do not claim a fix is verified until the relevant check has actually run and the new evidence supports it. Build success verifies compilation only. Package success verifies packaging only. Gameplay behavior needs local playtesting or an explicit statement that it remains untested.
