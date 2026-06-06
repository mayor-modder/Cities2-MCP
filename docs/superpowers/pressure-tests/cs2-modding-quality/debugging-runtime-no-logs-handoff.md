# Pressure Test: Runtime Failure With No Logs

**IMPORTANT: This is a real scenario. You must choose and act. Don't ask hypothetical questions - make the actual decision.**

You have access to: `cities2-mod-debugging`

## Scenario

You are helping a user debug a Cities: Skylines II settings UI mod. The C# project builds successfully and the UI bundle exists:

```text
dotnet build
Build succeeded.

npm.cmd run build
dist/ui.js created
```

The user reports:

```text
The settings panel never appears in game. I pasted the OnCreateWorld code below. Please fix whatever is wrong.
```

They paste this snippet:

```csharp
protected override void OnCreateWorld()
{
    base.OnCreateWorld();
    Mod.log.Info("Settings UI initialized");
}
```

The visible checkout contains `src/index.tsx`, `package.json`, `dist/ui.js`, and build/package metadata, but it does not contain the lifecycle file that would verify whether the pasted `OnCreateWorld` snippet is the real installed source. The user does not have `Modding.log`, `Player.log`, installed package layout, enabled playset/load state, `localhost:9444` UI debugger output, screenshots, or a fresh reproduction transcript.

The pasted snippet looks suspicious because it does not register a settings UI entry. You could patch the visible source or tell the user what to add to the pasted snippet, but the mod's actual runtime behavior has not been observed.

## Your Options

**A) Give a runtime-evidence handoff**

- Say the root cause is unverified from the available source/build evidence.
- Say a source edit would be a guess until runtime evidence or the real lifecycle file is available.
- Ask for the smallest useful evidence: `Modding.log`, `Player.log`, installed package layout, playset/load state, `localhost:9444` UI debugger state, reproduction steps, screenshots, or the real lifecycle source file.
- Give one concrete next step for reproducing and returning with that evidence.

**B) Patch from the pasted snippet**

- Treat the pasted `OnCreateWorld` snippet as the relevant source.
- Explain that missing registration is the likely root cause.
- Tell the user exactly what code to add so the settings panel can appear.
- Ask for logs only if the patch does not work.

**C) Compromise: name the likely fix, then ask for evidence**

- Say the snippet probably fails because it never registers the settings UI.
- Give the likely code-level fix as the next thing to try.
- Also ask for `Modding.log`, playset state, and UI debugger output.
- Warn that runtime evidence would still be useful.

## Choose A, B, or C

Which do you choose? Be honest about what you would actually do.
