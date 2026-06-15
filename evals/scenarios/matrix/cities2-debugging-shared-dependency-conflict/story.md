---
id: cities2-debugging-shared-dependency-conflict
title: Cities2 debugging shared dependency conflict
---

# Cities2 debugging shared dependency conflict

## Story

The user installed a local Cities: Skylines II mod build. On launch, another enabled mod throws a repeated `MissingMethodException` for a Harmony API. The useful answer should use the provided installed-state evidence to investigate a shared dependency conflict instead of blaming the other mod or patching source code blindly.

## Acceptance Criteria

- Inspect the provided launch log and target installed dependency manifest before diagnosing.
- Treat the cross-mod stack as a possible shared dependency or load-order conflict.
- Compare installed or loaded dependency versions, especially `0Harmony.dll`, against the missing API/member.
- Mention checking API/member availability, such as reflection for `HarmonyMethod.op_Implicit(MethodInfo)`.
- Keep compile/build/package success separate from launch or gameplay verification.

## Prompt

```text
I installed the local test build of this Cities: Skylines II mod. On launch, another mod now repeatedly throws:

MissingMethodException
Method not found: HarmonyLib.HarmonyMethod HarmonyLib.HarmonyMethod.op_Implicit(System.Reflection.MethodInfo)

The stack trace points at the other mod's startup code. If I remove this local test build, the launch error goes away. Please inspect the workspace evidence and tell me what to do next. The build compiled, so I am tempted to just blame the other mod or patch the first Harmony call site you find.
```
