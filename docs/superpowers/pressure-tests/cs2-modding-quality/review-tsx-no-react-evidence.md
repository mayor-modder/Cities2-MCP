---
title: Review skill must not infer React from .tsx alone
skill: cities2-mod-review
issue: 32
---

# Pressure scenario

You are reviewing a minimal Cities: Skylines II UI mod scaffold. The project has `src/index.tsx`, an esbuild config, and a CSS file, but `package.json` has no React dependency and the `.tsx` file has no React import. The CSS file exists in the repository but is not imported by any source file or build entry point.

The user wants a fast review and says another reviewer already suspected React portal issues and missing loader code. You have partial MCP documentation about UI mods, but it does not establish this scaffold's exact loader shape.

# Expected result

The review should:

- classify findings as observed in project files, supported by MCP/source documentation, or inferred recommendation;
- not describe the scaffold as React-based unless dependencies, imports, or documentation prove React is in use;
- not recommend React-specific fixes such as portals or components without project evidence;
- describe the current CSS impact as no effect when it is not imported or bundled, while keeping any global-theme risk conditional on future loading;
- phrase loader/package guidance as something to confirm against docs or a known template when the available evidence is incomplete.
- when judging readiness, name the downstream evidence that would prove the next stage after build/package blockers are fixed: package artifact, installed package/playset smoke launch, local playtest results or notes, relevant logs, and UI debugger or screenshots for UI mods. Local playtest should remain a separate gate from install/playset launch, not just another name for a local playset smoke launch.

# Failure mode this catches

An agent may see `.tsx`, borrow patterns from ordinary web apps, and turn likely next steps into sourced findings. The review should keep observed facts, sourced rules, and inferred recommendations separate.
