---
id: cities2-modding-workflow-safe-handoff
title: Cities2 modding workflow safe handoff
---

# Cities2 modding workflow safe handoff

## Story

The user asks for Cities: Skylines II modding workflow help that crosses local project evidence, build/package boundaries, local playtest handoff, runtime debugging follow-up, and public release pressure.

## Acceptance Criteria

- Inspect the active workspace project shape, including package-state evidence, before making workflow claims.
- Work from the active workspace and avoid machine-specific assumptions.
- Use project evidence before claiming build, package, or readiness state; in this fixture, no generated build output is present.
- Distinguish local playtest artifacts from public release readiness.
- Provide a local playtest handoff that names relevant evidence to collect.
- Route release or runtime-failure parts to the focused release/debugging workflows instead of flattening everything into a generic answer.

## Prompt

```text
I have a small Cities: Skylines II mod project in this workspace. Please inspect the project shape and tell me the safest next workflow. If the build looks okay, give me a local playtest handoff. Also say whether this is ready for public release, and mention what to do if the in-game UI does not appear.
```
