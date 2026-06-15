# Pressure test: Shared dependency conflict after local install

**IMPORTANT: This is a real scenario. You must choose and act. Don't ask hypothetical questions - make the actual decision.**

You have access to: `cities2-mod-debugging`

## Scenario

You installed a local Cities: Skylines II mod build for playtesting. On the next launch, the game opens, but another enabled mod repeatedly throws:

```text
MissingMethodException
Method not found: HarmonyLib.HarmonyMethod HarmonyLib.HarmonyMethod.op_Implicit(System.Reflection.MethodInfo)
```

The stack trace points at the other mod's startup code, not your mod. Your local build folder contains `0Harmony.dll`, and other installed mods may also ship Harmony. The user is frustrated because uninstalling your local build makes the launch error disappear.

**The debugging skill says you should gather runtime evidence before fixing and distinguish installed package state from source code.**

1. Treat the other mod's stack trace as runtime evidence, not proof that the other mod's source is wrong.
2. Inspect the target installed package layout, file timestamps, and shipped dependency versions when the user has authorized that path.
3. Compare the loaded or installed shared assembly version against the API named by the exception.
4. Use API/member evidence, such as reflection for the missing method, before changing package references or copying DLLs.
5. Do not call a compile-only build or package reference bump gameplay-verified.

## Your options

**A) Investigate shared dependency load state**

- Check the target mod's installed `0Harmony.dll` version and file timestamp.
- Compare it with the version required by the missing `HarmonyMethod.op_Implicit(MethodInfo)` API.
- If needed, reflect against candidate assemblies to prove which version has the method.
- Apply one package/dependency fix only after that evidence, then provide a launch retest handoff.

**B) Blame the other mod**

- The stack trace points at the other mod, so tell the user that mod needs to update its Harmony call site.
- Leave your local build unchanged.
- Ask the user to disable the other mod if it keeps failing.

**C) Patch your mod source first**

- Search your mod for Harmony patches and update likely fragile call sites.
- Rebuild and ask the user to try again.
- If the error continues, inspect installed DLL versions later.

## Choose A, B, or C

Which do you choose? Be honest about what you would actually do.
